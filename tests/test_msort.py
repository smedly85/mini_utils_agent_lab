"""
tests/test_msort.py
Public behavioral tests for the msort utility.
Author: Sonja Brown
"""

import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MSORT = REPO_ROOT / "build" / "msort"
TIMEOUT_SECONDS = 5


class MsortTests(unittest.TestCase):
    def run_msort(self, input_bytes=b"", args=None):
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
        )

    def test_sorts_ordinary_records_from_stdin(self):
        result = self.run_msort(b"banana\napple\ncherry\n")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"apple\nbanana\ncherry\n")
        self.assertEqual(result.stderr, b"")

    def test_preserves_duplicate_records(self):
        result = self.run_msort(b"beta\nalpha\nbeta\nalpha\n")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"alpha\nalpha\nbeta\nbeta\n")
        self.assertEqual(result.stderr, b"")

    def test_handles_empty_input(self):
        result = self.run_msort(b"")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr, b"")

    def test_processes_final_record_without_trailing_newline(self):
        result = self.run_msort(b"delta\nalpha\ncharlie")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"alpha\ncharlie\ndelta\n")
        self.assertEqual(result.stderr, b"")

    def test_preserves_empty_records(self):
        result = self.run_msort(b"b\n\na\n")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"\na\nb\n")
        self.assertEqual(result.stderr, b"")

    def test_reads_from_one_file_path(self):
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            temp_file.write(b"pear\napple\norange\n")
            temp_file.flush()

            result = self.run_msort(args=[temp_file.name])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"apple\norange\npear\n")
        self.assertEqual(result.stderr, b"")

    def test_rejects_more_than_one_file_argument(self):
        result = self.run_msort(args=["first.txt", "second.txt"])

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"usage:", result.stderr)

    def test_reports_missing_input_file(self):
        missing_path = str(REPO_ROOT / "tests" / "missing-msort-input.txt")
        result = self.run_msort(args=[missing_path])

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"cannot open", result.stderr)

    def test_handles_long_record(self):
        long_record = b"x" * 10000
        result = self.run_msort(b"short\n" + long_record + b"\nmedium\n")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"medium\nshort\n" + long_record + b"\n")
        self.assertEqual(result.stderr, b"")

    def test_sorts_bytewise_not_numerically(self):
        result = self.run_msort(b"10\n2\n1\n")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"1\n10\n2\n")
        self.assertEqual(result.stderr, b"")

    def test_reverse_short_option_sorts_standard_input(self):
        result = self.run_msort(b"banana\napple\ncherry\n", args=["-r"])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"cherry\nbanana\napple\n")
        self.assertEqual(result.stderr, b"")

    def test_reverse_long_option_sorts_standard_input(self):
        result = self.run_msort(b"banana\napple\ncherry\n", args=["--reverse"])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"cherry\nbanana\napple\n")
        self.assertEqual(result.stderr, b"")

    def test_reverse_sorts_one_file(self):
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            temp_file.write(b"pear\napple\norange\n")
            temp_file.flush()

            result = self.run_msort(args=["-r", temp_file.name])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"pear\norange\napple\n")
        self.assertEqual(result.stderr, b"")

    def test_reverse_preserves_duplicate_records(self):
        result = self.run_msort(b"beta\nalpha\nbeta\nalpha\n", args=["-r"])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"beta\nbeta\nalpha\nalpha\n")
        self.assertEqual(result.stderr, b"")

    def test_reverse_preserves_empty_records(self):
        result = self.run_msort(b"b\n\na\n", args=["-r"])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"b\na\n\n")
        self.assertEqual(result.stderr, b"")

    def test_reverse_handles_input_without_final_newline(self):
        result = self.run_msort(b"delta\nalpha\ncharlie", args=["-r"])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"delta\ncharlie\nalpha\n")
        self.assertEqual(result.stderr, b"")

    def test_reverse_handles_empty_input(self):
        result = self.run_msort(b"", args=["-r"])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr, b"")

    def test_rejects_unknown_short_option(self):
        result = self.run_msort(args=["-x"])

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"usage:", result.stderr)

    def test_rejects_unknown_long_option(self):
        result = self.run_msort(args=["--unknown"])

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"usage:", result.stderr)

    def test_rejects_path_followed_by_reverse_option(self):
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            temp_file.write(b"b\na\n")
            temp_file.flush()

            result = self.run_msort(args=[temp_file.name, "-r"])

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"usage:", result.stderr)


if __name__ == "__main__":
    unittest.main()
