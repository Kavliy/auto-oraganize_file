import json
import os
import shutil
import tempfile
import unittest

from organizer.undo import LOG_FILENAME, save_operation, undo_last


class UndoLastTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._tmpdir, ignore_errors=True)

    def _path(self, *parts):
        return os.path.join(self._tmpdir, *parts)

    def _write_file(self, relative_path, content):
        path = self._path(relative_path)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def _read_log(self):
        with open(self._path(LOG_FILENAME), "r", encoding="utf-8") as f:
            return json.load(f)

    def test_undo_last_restores_files_and_clears_log_entry(self):
        self._write_file("txt/report.txt", "hello")
        save_operation(
            self._tmpdir,
            "by_type",
            [{"source": "report.txt", "dest": "txt/report.txt"}],
        )

        restored = undo_last(self._tmpdir)

        self.assertTrue(restored)
        self.assertTrue(os.path.exists(self._path("report.txt")))
        self.assertFalse(os.path.exists(self._path("txt", "report.txt")))
        self.assertFalse(os.path.isdir(self._path("txt")))
        self.assertEqual(self._read_log()["operations"], [])

    def test_undo_last_keeps_conflicting_move_in_log(self):
        self._write_file("txt/report.txt", "organized")
        self._write_file("report.txt", "new file")
        save_operation(
            self._tmpdir,
            "by_type",
            [{"source": "report.txt", "dest": "txt/report.txt"}],
        )

        restored = undo_last(self._tmpdir)

        self.assertFalse(restored)
        self.assertEqual(
            self._read_log()["operations"][-1]["moves"],
            [{"source": "report.txt", "dest": "txt/report.txt"}],
        )
        self.assertTrue(os.path.exists(self._path("txt", "report.txt")))
        self.assertTrue(os.path.exists(self._path("report.txt")))

    def test_undo_last_retries_only_remaining_failed_moves(self):
        self._write_file("txt/report.txt", "organized report")
        self._write_file("jpg/photo.jpg", "organized photo")
        self._write_file("photo.jpg", "new conflicting photo")
        save_operation(
            self._tmpdir,
            "by_type",
            [
                {"source": "report.txt", "dest": "txt/report.txt"},
                {"source": "photo.jpg", "dest": "jpg/photo.jpg"},
            ],
        )

        first_restore = undo_last(self._tmpdir)

        self.assertTrue(first_restore)
        self.assertTrue(os.path.exists(self._path("report.txt")))
        self.assertFalse(os.path.exists(self._path("txt", "report.txt")))
        self.assertEqual(
            self._read_log()["operations"][-1]["moves"],
            [{"source": "photo.jpg", "dest": "jpg/photo.jpg"}],
        )

        os.remove(self._path("photo.jpg"))
        second_restore = undo_last(self._tmpdir)

        self.assertTrue(second_restore)
        self.assertTrue(os.path.exists(self._path("photo.jpg")))
        self.assertFalse(os.path.exists(self._path("jpg", "photo.jpg")))
        self.assertEqual(self._read_log()["operations"], [])


if __name__ == "__main__":
    unittest.main()
