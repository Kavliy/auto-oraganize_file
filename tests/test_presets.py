import os
import shutil
import tempfile
import unittest

from organizer.presets import (
    PRESETS_ENV_VAR,
    PresetError,
    load_preset,
    load_type_groups,
    remove_type_group,
    save_preset,
    save_type_group,
)


class PresetTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._tmpdir, ignore_errors=True)

        self._previous_env = os.environ.get(PRESETS_ENV_VAR)
        os.environ[PRESETS_ENV_VAR] = os.path.join(self._tmpdir, "presets.json")
        self.addCleanup(self._restore_env)

    def _restore_env(self):
        if self._previous_env is None:
            os.environ.pop(PRESETS_ENV_VAR, None)
        else:
            os.environ[PRESETS_ENV_VAR] = self._previous_env

    def test_save_and_load_preset_round_trip(self):
        path, existed = save_preset(
            "qdata-db",
            "by_pattern",
            {"pattern": r"QData一体机(.+?)\d{4}年.*"},
        )

        self.assertFalse(existed)
        self.assertTrue(os.path.isfile(path))
        self.assertEqual(
            load_preset("qdata-db"),
            ("by_pattern", {"pattern": r"QData一体机(.+?)\d{4}年.*"}),
        )

    def test_save_preset_reports_overwrite(self):
        save_preset("downloads", "by_type", {})

        _, existed = save_preset("downloads", "by_date", {"fmt": "%Y-%m"})

        self.assertTrue(existed)
        self.assertEqual(load_preset("downloads"), ("by_date", {"fmt": "%Y-%m"}))

    def test_load_preset_requires_existing_name(self):
        with self.assertRaises(PresetError):
            load_preset("missing")

    def test_save_and_load_type_groups_round_trip(self):
        path, existed = save_type_group("images", ["jpg", ".gif", "PNG"])

        self.assertFalse(existed)
        self.assertTrue(os.path.isfile(path))
        self.assertEqual(
            load_type_groups(),
            {"images": ["jpg", "gif", "png"]},
        )

    def test_save_type_group_rejects_extension_conflicts(self):
        save_type_group("images", ["jpg", "gif"])

        with self.assertRaises(PresetError):
            save_type_group("docs", ["pdf", "jpg"])

    def test_remove_type_group_updates_store(self):
        save_type_group("images", ["jpg", "gif"])
        save_type_group("docs", ["pdf"])

        remove_type_group("images")

        self.assertEqual(load_type_groups(), {"docs": ["pdf"]})


if __name__ == "__main__":
    unittest.main()
