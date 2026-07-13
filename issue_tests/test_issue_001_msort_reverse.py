"""
Public acceptance tests for GitHub Issue 1: msort reverse sorting.
"""

import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MSORT = (REPO_ROOT / "build" / "msort").resolve()
TIMEOUT_SECONDS = 5


class Issue001MsortReverseTests(unittest.TestCase):
    def run_msort(self, input_bytes=b"", args=None, cwd=None):
        if args is None:
            args = []
        if not MSORT.exists():
            self.fail("build/msort does not exist; run make before running tests")

        return subprocess.run(
            [str(MSORT)] + args,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            timeout=TIMEOUT_SECONDS,
            cwd=cwd,
        )

    def assert_success(self, result, expected_stdout):
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, expected_stdout)
        self.assertEqual(result.stderr, b"")

    def assert_usage_failure(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"usage:", result.stderr)

    def test_reverse_short_option_sorts_standard_input(self):
        result = self.run_msort(b"banana\napple\ncherry\n", args=["-r"])

        self.assert_success(result, b"cherry\nbanana\napple\n")

    def test_reverse_long_option_sorts_standard_input(self):
        result = self.run_msort(b"banana\napple\ncherry\n", args=["--reverse"])

        self.assert_success(result, b"cherry\nbanana\napple\n")

    def test_reverse_sorts_one_file(self):
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            temp_file.write(b"pear\napple\norange\n")
            temp_file.flush()

            result = self.run_msort(args=["-r", temp_file.name])

        self.assert_success(result, b"pear\norange\napple\n")

    def test_reverse_preserves_duplicate_records(self):
        result = self.run_msort(b"beta\nalpha\nbeta\nalpha\n", args=["-r"])

        self.assert_success(result, b"beta\nbeta\nalpha\nalpha\n")

    def test_reverse_preserves_empty_records(self):
        result = self.run_msort(b"b\n\na\n", args=["-r"])

        self.assert_success(result, b"b\na\n\n")

    def test_reverse_handles_input_without_final_newline(self):
        result = self.run_msort(b"delta\nalpha\ncharlie", args=["-r"])

        self.assert_success(result, b"delta\ncharlie\nalpha\n")

    def test_reverse_handles_empty_input(self):
        result = self.run_msort(b"", args=["-r"])

        self.assert_success(result, b"")

    def test_existing_ascending_behavior_remains_unchanged(self):
        result = self.run_msort(b"banana\napple\ncherry\n")

        self.assert_success(result, b"apple\nbanana\ncherry\n")

    def test_reverse_sorts_arbitrary_binary_records(self):
        result = self.run_msort(
            b"a\nab\na\x00\n\x80\n\xff\n",
            args=["--reverse"],
        )

        self.assert_success(result, b"\xff\n\x80\nab\na\x00\na\n")

    def test_rejects_unknown_short_option_even_when_filename_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "-x").write_bytes(b"z\na\n")

            result = self.run_msort(args=["-x"], cwd=temp_dir)

        self.assert_usage_failure(result)

    def test_rejects_unknown_long_option_even_when_filename_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "--unknown").write_bytes(b"z\na\n")

            result = self.run_msort(args=["--unknown"], cwd=temp_dir)

        self.assert_usage_failure(result)

    def test_rejects_path_followed_by_short_reverse_option(self):
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            temp_file.write(b"b\na\n")
            temp_file.flush()

            result = self.run_msort(args=[temp_file.name, "-r"])

        self.assert_usage_failure(result)

    def test_rejects_path_followed_by_long_reverse_option(self):
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            temp_file.write(b"b\na\n")
            temp_file.flush()

            result = self.run_msort(args=[temp_file.name, "--reverse"])

        self.assert_usage_failure(result)

    def test_rejects_two_input_paths(self):
        with tempfile.NamedTemporaryFile(delete=True) as first:
            with tempfile.NamedTemporaryFile(delete=True) as second:
                result = self.run_msort(args=[first.name, second.name])

        self.assert_usage_failure(result)

    def test_rejects_short_reverse_followed_by_two_paths(self):
        with tempfile.NamedTemporaryFile(delete=True) as first:
            with tempfile.NamedTemporaryFile(delete=True) as second:
                result = self.run_msort(args=["-r", first.name, second.name])

        self.assert_usage_failure(result)

    def test_rejects_long_reverse_followed_by_two_paths(self):
        with tempfile.NamedTemporaryFile(delete=True) as first:
            with tempfile.NamedTemporaryFile(delete=True) as second:
                result = self.run_msort(args=["--reverse", first.name, second.name])

        self.assert_usage_failure(result)


if __name__ == "__main__":
    unittest.main()
