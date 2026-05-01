import os
import shutil
import subprocess
import sys
import unittest
import uuid

from organizer.presets import (
    PRESETS_ENV_VAR,
    list_presets,
    load_type_groups,
    save_preset,
)


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILESORT = os.path.join(REPO_ROOT, "filesort")


def _make_tmpdir():
    path = os.path.join(REPO_ROOT, f"tmp_test_{uuid.uuid4().hex}")
    os.makedirs(path)
    return path


class CliTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = _make_tmpdir()
        self.addCleanup(shutil.rmtree, self._tmpdir, ignore_errors=True)

        self._previous_env = os.environ.get(PRESETS_ENV_VAR)
        self._store_path = os.path.join(self._tmpdir, "presets.json")
        os.environ[PRESETS_ENV_VAR] = self._store_path
        self.addCleanup(self._restore_env)

    def _restore_env(self):
        if self._previous_env is None:
            os.environ.pop(PRESETS_ENV_VAR, None)
        else:
            os.environ[PRESETS_ENV_VAR] = self._previous_env

    def _run(self, *args):
        env = os.environ.copy()
        env[PRESETS_ENV_VAR] = self._store_path
        return subprocess.run(
            [sys.executable, FILESORT, *args],
            cwd=REPO_ROOT,
            env=env,
            universal_newlines=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

    def test_list_presets_with_unified_list_option(self):
        save_preset("downloads", "by_type", {})

        result = self._run("--list", "presets")

        self.assertIn("Configured presets:", result.stdout)
        self.assertIn("downloads: by_type", result.stdout)

    def test_preset_subcommand_removes_preset(self):
        save_preset("downloads", "by_type", {})

        result = self._run("presets", "remove", "downloads")

        self.assertIn("Removed preset 'downloads'", result.stdout)
        self.assertEqual(list_presets(), {})

    def test_group_subcommands_manage_type_groups(self):
        set_result = self._run("groups", "set", "images=jpg,png")
        list_result = self._run("groups", "list")
        remove_result = self._run("groups", "remove", "images")

        self.assertIn("Saved type group 'images'", set_result.stdout)
        self.assertIn("images=jpg,png", list_result.stdout)
        self.assertIn("Removed type group 'images'", remove_result.stdout)
        self.assertEqual(load_type_groups(), {})

    def test_completion_command_prints_powershell_script(self):
        result = self._run("completion", "powershell")

        self.assertIn("Register-ArgumentCompleter", result.stdout)
        self.assertIn("--list", result.stdout)


if __name__ == "__main__":
    unittest.main()
