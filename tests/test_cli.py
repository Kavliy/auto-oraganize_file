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

    def _run(self, *args, **kwargs):
        extra_env = kwargs.pop("extra_env", None)
        if kwargs:
            raise TypeError(f"Unexpected keyword arguments: {', '.join(kwargs)}")

        env = os.environ.copy()
        env[PRESETS_ENV_VAR] = self._store_path
        if extra_env:
            env.update(extra_env)
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

    def test_help_hides_legacy_management_flags(self):
        result = self._run("--help")

        self.assertIn("filesort presets list", result.stdout)
        self.assertIn("filesort completion install", result.stdout)
        self.assertNotIn("--list-preset", result.stdout)
        self.assertNotIn("--remove-preset", result.stdout)
        self.assertNotIn("--set-type-group", result.stdout)
        self.assertNotIn("--remove-type-group", result.stdout)
        self.assertNotIn("--list-type-groups", result.stdout)
        self.assertNotIn("--completion", result.stdout)
        self.assertNotIn("--install-completion", result.stdout)

    def test_legacy_management_flags_still_work(self):
        set_result = self._run("--set-type-group", "images=jpg,png")
        list_result = self._run("--list-type-groups")
        remove_result = self._run("--remove-type-group", "images")

        self.assertIn("Saved type group 'images'", set_result.stdout)
        self.assertIn("images=jpg,png", list_result.stdout)
        self.assertIn("Removed type group 'images'", remove_result.stdout)

    def test_completion_install_bash_updates_user_files(self):
        result = self._run(
            "completion",
            "install",
            "bash",
            extra_env={"FILESORT_COMPLETION_HOME": self._tmpdir},
        )

        completion_path = os.path.join(
            self._tmpdir,
            ".local",
            "share",
            "bash-completion",
            "completions",
            "filesort",
        )
        bashrc_path = os.path.join(self._tmpdir, ".bashrc")

        self.assertIn("Installed bash completion", result.stdout)
        self.assertTrue(os.path.isfile(completion_path))
        self.assertTrue(os.path.isfile(bashrc_path))

        with open(bashrc_path, "r", encoding="utf-8") as f:
            bashrc = f.read()

        self.assertIn(">>> filesort completion >>>", bashrc)
        self.assertIn("bash-completion/completions/filesort", bashrc)


if __name__ == "__main__":
    unittest.main()
