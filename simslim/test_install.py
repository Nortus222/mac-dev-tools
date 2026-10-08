"""Verify that unsupported CLIs cannot replace a working watcher."""

import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("installer", Path(__file__).with_name("install.py"))
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallVersionTests(unittest.TestCase):
    def test_unsupported_version_leaves_loaded_service_untouched(self):
        for version in ["simslim 0.11.0", "unexpected version output"]:
            with (
                self.subTest(version=version),
                tempfile.TemporaryDirectory() as home,
                patch.object(installer.Path, "home", return_value=Path(home)),
                patch.object(installer.sys, "argv", ["install.py", "install"]),
                patch.object(installer.shutil, "which", return_value="/tmp/simslim"),
                patch.object(installer.subprocess, "run") as run,
                contextlib.redirect_stderr(io.StringIO()),
            ):
                run.return_value = subprocess.CompletedProcess([], 0, stdout=version + "\n")
                with self.assertRaises(SystemExit) as error:
                    installer.main()
                self.assertEqual(error.exception.code, 2)
                self.assertEqual(run.call_count, 2)
                self.assertFalse((Path(home) / "Library/LaunchAgents").exists())


if __name__ == "__main__":
    unittest.main()
