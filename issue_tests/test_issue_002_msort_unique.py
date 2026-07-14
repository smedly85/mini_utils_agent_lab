"""
Public acceptance tests for GitHub Issue 2: msort unique output.
"""

import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MSORT = (REPO_ROOT / "build" / "msort").resolve()
TIMEOUT_SECONDS = 5


class Issue002MsortUniqueTests(unittest.TestCase):
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

    def test_short_option_sorts_and_deduplicates_standard_input(self):
        result = self.run_msort(b"banana\napple\nbanana\n", args=["-u"])

        self.assert_success(result, b"apple\nbanana\n")

    def test_long_option_sorts_and_deduplicates_standard_input(self):
        result = self.run_msort(b"banana\napple\nbanana\n", args=["--unique"])

        self.assert_success(result, b"apple\nbanana\n")

    def test_short_option_reads_one_file(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b"pear\napple\npear\n")
            temp_file.flush()

            result = self.run_msort(args=["-u", temp_file.name])

        self.assert_success(result, b"apple\npear\n")

    def test_long_option_reads_one_file(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b"pear\napple\npear\n")
            temp_file.flush()

            result = self.run_msort(args=["--unique", temp_file.name])

        self.assert_success(result, b"apple\npear\n")

    def test_unique_sorts_before_deduplicating(self):
        result = self.run_msort(b"b\na\nb\na\n", args=["-u"])

        self.assert_success(result, b"a\nb\n")

    def test_unique_collapses_duplicate_ordinary_records(self):
        result = self.run_msort(b"beta\nalpha\nbeta\nalpha\n", args=["-u"])

        self.assert_success(result, b"alpha\nbeta\n")

    def test_unique_collapses_multiple_empty_records(self):
        result = self.run_msort(b"\n\nb\n\n", args=["-u"])

        self.assert_success(result, b"\nb\n")

    def test_unique_handles_empty_input(self):
        result = self.run_msort(b"", args=["-u"])

        self.assert_success(result, b"")

    def test_unique_handles_input_without_final_newline(self):
        result = self.run_msort(b"delta\nalpha\ndelta", args=["-u"])

        self.assert_success(result, b"alpha\ndelta\n")

    def test_unique_keeps_records_with_different_padding_distinct(self):
        result = self.run_msort(b" alpha\nalpha\nalpha \n alpha\n", args=["-u"])

        self.assert_success(result, b" alpha\nalpha\nalpha \n")

    def test_unique_compares_binary_records_bytewise_and_preserves_bytes(self):
        result = self.run_msort(
            b"\xff\n\x00\n\x80\n\x00\n\xff\n",
            args=["--unique"],
        )

        self.assert_success(result, b"\x00\n\x80\n\xff\n")

    def test_default_ascending_sort_preserves_duplicates(self):
        result = self.run_msort(b"b\na\nb\na\n")

        self.assert_success(result, b"a\na\nb\nb\n")

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

    def test_rejects_path_followed_by_unique_option(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            for option in ("-u", "--unique"):
                with self.subTest(option=option):
                    result = self.run_msort(args=[temp_file.name, option])

                    self.assert_usage_failure(result)

    def test_rejects_two_input_paths_with_or_without_unique_option(self):
        with tempfile.NamedTemporaryFile() as first:
            with tempfile.NamedTemporaryFile() as second:
                for args in (
                    [first.name, second.name],
                    ["-u", first.name, second.name],
                    ["--unique", first.name, second.name],
                ):
                    with self.subTest(args=args):
                        result = self.run_msort(args=args)

                        self.assert_usage_failure(result)

    def test_rejects_repeated_and_mixed_unique_options(self):
        for args in (
            ["-u", "-u"],
            ["-u", "--unique"],
            ["--unique", "-u"],
            ["--unique", "--unique"],
        ):
            with self.subTest(args=args):
                result = self.run_msort(args=args)

                self.assert_usage_failure(result)


if __name__ == "__main__":
    unittest.main()
