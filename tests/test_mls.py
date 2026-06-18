"""
tests/test_mls.py
Public behavioral tests for the mls directory-listing utility.
Author: Sonja Brown
"""

import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MLS = REPO_ROOT / "build" / "mls"
TIMEOUT_SECONDS = 5


class MlsTests(unittest.TestCase):
    def run_mls(self, args=None, cwd=None):
        if args is None:
            args = []
        if not MLS.exists():
            self.fail("build/mls does not exist; run make before running tests")

        return subprocess.run(
            [str(MLS)] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            timeout=TIMEOUT_SECONDS,
            cwd=None if cwd is None else str(cwd),
        )

    def test_lists_explicit_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "beta").write_bytes(b"")
            (directory / "alpha").write_bytes(b"")

            result = self.run_mls([str(directory)])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"alpha\nbeta\n")
        self.assertEqual(result.stderr, b"")

    def test_lists_current_directory_when_no_path_supplied(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "current").write_bytes(b"")

            result = self.run_mls(cwd=directory)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"current\n")
        self.assertEqual(result.stderr, b"")

    def test_sorts_names_bytewise(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            for name in ["b", "aa", ".hidden", "Z", "a", "0"]:
                (directory / name).write_bytes(b"")

            result = self.run_mls([str(directory)])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b".hidden\n0\nZ\na\naa\nb\n")
        self.assertEqual(result.stderr, b"")

    def test_sorts_case_sensitively(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "a").write_bytes(b"lower")
            (directory / "A").write_bytes(b"upper")

            created_names = {entry.name for entry in directory.iterdir()}
            if created_names != {"A", "a"}:
                self.skipTest(
                    "filesystem does not support distinct case-sensitive names"
                )

            result = self.run_mls([str(directory)])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"A\na\n")
        self.assertEqual(result.stderr, b"")

    def test_orders_prefix_before_longer_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "aa").write_bytes(b"")
            (directory / "a").write_bytes(b"")

            result = self.run_mls([str(directory)])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"a\naa\n")
        self.assertEqual(result.stderr, b"")

    def test_includes_hidden_names(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / ".hidden").write_bytes(b"")
            (directory / "visible").write_bytes(b"")

            result = self.run_mls([str(directory)])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b".hidden\nvisible\n")
        self.assertEqual(result.stderr, b"")

    def test_excludes_dot_entries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "entry").write_bytes(b"")

            result = self.run_mls([str(directory)])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"entry\n")
        self.assertNotIn(b".\n", result.stdout)
        self.assertNotIn(b"..\n", result.stdout)
        self.assertEqual(result.stderr, b"")

    def test_empty_directory_outputs_nothing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.run_mls([temp_dir])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr, b"")

    def test_includes_files_and_directories_without_markers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "plain").write_bytes(b"")
            (directory / "subdir").mkdir()

            result = self.run_mls([str(directory)])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"plain\nsubdir\n")
        self.assertNotIn(b"/", result.stdout)
        self.assertNotIn(b"*", result.stdout)
        self.assertEqual(result.stderr, b"")

    def test_lists_only_immediate_entries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            nested = directory / "nested"
            nested.mkdir()
            (nested / "inside").write_bytes(b"")
            (directory / "top").write_bytes(b"")

            result = self.run_mls([str(directory)])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"nested\ntop\n")
        self.assertNotIn(b"inside", result.stdout)
        self.assertEqual(result.stderr, b"")

    def test_prints_names_not_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "entry").write_bytes(b"")

            result = self.run_mls([str(directory)])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"entry\n")
        self.assertNotIn(str(directory).encode("utf-8"), result.stdout)
        self.assertEqual(result.stderr, b"")

    def test_rejects_option(self):
        result = self.run_mls(["-a"])

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"usage:", result.stderr)

    def test_rejects_more_than_one_path(self):
        result = self.run_mls(["first", "second"])

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"usage:", result.stderr)

    def test_reports_missing_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing"

            result = self.run_mls([str(missing)])

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"cannot open", result.stderr)

    def test_rejects_regular_file_when_directory_required(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            regular_file = Path(temp_dir) / "file.txt"
            regular_file.write_bytes(b"not a directory")

            result = self.run_mls([str(regular_file)])

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"cannot open", result.stderr)


if __name__ == "__main__":
    unittest.main()
