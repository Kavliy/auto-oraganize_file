import io
import os
import shutil
import unittest
import uuid
from contextlib import redirect_stderr
from datetime import datetime

from organizer.core import _normalize_category_name, organize


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _make_tmpdir():
    path = os.path.join(REPO_ROOT, f"tmp_test_{uuid.uuid4().hex}")
    os.makedirs(path)
    return path


class CategoryNormalizationTests(unittest.TestCase):
    def test_normalize_category_name_keeps_single_directory(self):
        normalized = _normalize_category_name("../QData:2026/04\\final*?  ")

        self.assertEqual(normalized, "QData_2026_04_final")

    def test_normalize_category_name_falls_back_to_uncategorized(self):
        self.assertEqual(_normalize_category_name(" / \\ . "), "uncategorized")


class OrganizeTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = _make_tmpdir()
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
        return path

    def test_by_date_sanitizes_nested_directory_formats(self):
        file_path = self._write_file("report.txt", "hello")
        timestamp = datetime(2026, 4, 15, 8, 30).timestamp()
        os.utime(file_path, (timestamp, timestamp))

        organize(self._tmpdir, "by_date", {"fmt": "%Y/%m"}, execute=True)

        self.assertTrue(os.path.exists(self._path("2026_04", "report.txt")))
        self.assertFalse(os.path.exists(self._path("2026", "04", "report.txt")))
        self.assertFalse(os.path.isdir(self._path("2026")))

    def test_by_pattern_reports_invalid_regex_cleanly(self):
        self._write_file("report.txt", "hello")
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as exc:
                organize(self._tmpdir, "by_pattern", {"pattern": "("}, execute=True)

        self.assertEqual(exc.exception.code, 2)
        self.assertIn("Invalid regex pattern for --by-pattern", stderr.getvalue())

    def test_by_type_applies_extension_groups(self):
        self._write_file("photo.JPG", "image")
        self._write_file("scan.gif", "gif")
        self._write_file("report.pdf", "pdf")
        self._write_file("movie.mp4", "video")

        organize(
            self._tmpdir,
            "by_type",
            {
                "type_groups": {
                    "images": ["jpg", "gif"],
                    "docs": ["pdf"],
                },
            },
            execute=True,
        )

        self.assertTrue(os.path.exists(self._path("images", "photo.JPG")))
        self.assertTrue(os.path.exists(self._path("images", "scan.gif")))
        self.assertTrue(os.path.exists(self._path("docs", "report.pdf")))
        self.assertTrue(os.path.exists(self._path("mp4", "movie.mp4")))


if __name__ == "__main__":
    unittest.main()
