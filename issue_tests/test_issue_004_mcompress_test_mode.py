"""
Public acceptance tests for GitHub Issue 4: mcompress test mode.
"""

import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MCOMPRESS = (REPO_ROOT / "build" / "mcompress").resolve()
TIMEOUT_SECONDS = 5


class Issue004McompressTestModeTests(unittest.TestCase):
    def run_mcompress(self, input_bytes=b"", args=None, cwd=None):
        if args is None:
            args = []
        if not MCOMPRESS.exists():
            self.fail("build/mcompress does not exist; run make before running tests")

        return subprocess.run(
            [str(MCOMPRESS)] + args,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            timeout=TIMEOUT_SECONDS,
            cwd=cwd,
        )

    def assert_valid(self, result):
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr, b"")

    def assert_malformed(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertNotEqual(result.stderr, b"")

    def assert_usage_failure(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"usage:", result.stderr)

    def test_short_option_accepts_valid_standard_input_without_output(self):
        result = self.run_mcompress(b"\x03A", args=["-t"])

        self.assert_valid(result)

    def test_long_option_accepts_valid_standard_input_without_output(self):
        result = self.run_mcompress(b"\x03A", args=["--test"])

        self.assert_valid(result)

    def test_test_mode_accepts_valid_file_input(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b"\x03A\x01B")
            temp_file.flush()

            result = self.run_mcompress(args=["-t", temp_file.name])

        self.assert_valid(result)

    def test_test_mode_accepts_empty_input(self):
        result = self.run_mcompress(b"", args=["-t"])

        self.assert_valid(result)

    def test_test_mode_accepts_several_valid_runs(self):
        result = self.run_mcompress(b"\x03A\x01B\x05C", args=["--test"])

        self.assert_valid(result)

    def test_test_mode_accepts_count_255(self):
        result = self.run_mcompress(b"\xffA", args=["-t"])

        self.assert_valid(result)

    def test_test_mode_accepts_binary_values(self):
        result = self.run_mcompress(b"\x01\x00\x02\xff", args=["--test"])

        self.assert_valid(result)

    def test_test_mode_rejects_zero_count_at_start(self):
        result = self.run_mcompress(b"\x00A", args=["-t"])

        self.assert_malformed(result)

    def test_test_mode_rejects_zero_count_after_valid_runs(self):
        result = self.run_mcompress(b"\x03A\x00B", args=["--test"])

        self.assert_malformed(result)

    def test_test_mode_rejects_trailing_unmatched_count(self):
        result = self.run_mcompress(b"\x03A\x02", args=["-t"])

        self.assert_malformed(result)

    def test_test_mode_rejects_malformed_file_input(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b"\x02A\x00B")
            temp_file.flush()

            result = self.run_mcompress(args=["--test", temp_file.name])

        self.assert_malformed(result)

    def test_rejects_no_selected_mode(self):
        result = self.run_mcompress()

        self.assert_usage_failure(result)

    def test_rejects_unknown_options(self):
        for option in ("-x", "--unknown"):
            with self.subTest(option=option):
                result = self.run_mcompress(args=[option])

                self.assert_usage_failure(result)

    def test_rejects_two_input_paths(self):
        with tempfile.NamedTemporaryFile() as first:
            with tempfile.NamedTemporaryFile() as second:
                result = self.run_mcompress(args=["-t", first.name, second.name])

        self.assert_usage_failure(result)

    def test_rejects_missing_input_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = str(Path(temp_dir, "missing.rle"))
            result = self.run_mcompress(args=["-t", missing])

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertNotEqual(result.stderr, b"")

    def test_rejects_repeated_and_mixed_test_aliases(self):
        for args in (
            ["-t", "-t"],
            ["-t", "--test"],
            ["--test", "-t"],
            ["--test", "--test"],
        ):
            with self.subTest(args=args):
                result = self.run_mcompress(args=args)

                self.assert_usage_failure(result)

    def test_rejects_test_mode_combined_with_other_modes(self):
        for args in (
            ["-c", "-t"],
            ["-d", "-t"],
            ["-t", "-c"],
            ["-t", "-d"],
            ["--compress", "--test"],
            ["--decompress", "--test"],
            ["--test", "--compress"],
            ["--test", "--decompress"],
        ):
            with self.subTest(args=args):
                result = self.run_mcompress(args=args)

                self.assert_usage_failure(result)


if __name__ == "__main__":
    unittest.main()
