"""
Public acceptance tests for GitHub Issue 3: msort ignore leading blanks.
"""

import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MSORT = (REPO_ROOT / "build" / "msort").resolve()
TIMEOUT_SECONDS = 5


class Issue003MsortIgnoreLeadingBlanksTests(unittest.TestCase):
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

    def test_short_option_ignores_leading_spaces_on_standard_input(self):
        result = self.run_msort(b" banana\napple\n  cherry\n", args=["-b"])

        self.assert_success(result, b"apple\n banana\n  cherry\n")

    def test_long_option_ignores_leading_spaces_on_standard_input(self):
        result = self.run_msort(
            b" banana\napple\n  cherry\n",
            args=["--ignore-leading-blanks"],
        )

        self.assert_success(result, b"apple\n banana\n  cherry\n")

    def test_short_option_reads_one_file(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b" beta\nalpha\n")
            temp_file.flush()

            result = self.run_msort(args=["-b", temp_file.name])

        self.assert_success(result, b"alpha\n beta\n")

    def test_long_option_reads_one_file(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b" beta\nalpha\n")
            temp_file.flush()

            result = self.run_msort(args=["--ignore-leading-blanks", temp_file.name])

        self.assert_success(result, b"alpha\n beta\n")

    def test_leading_tabs_are_ignored(self):
        result = self.run_msort(b"\tbanana\napple\n\t\tcherry\n", args=["-b"])

        self.assert_success(result, b"apple\n\tbanana\n\t\tcherry\n")

    def test_mixed_leading_spaces_and_tabs_are_ignored(self):
        result = self.run_msort(b" \tbanana\napple\n\t cherry\n", args=["-b"])

        self.assert_success(result, b"apple\n \tbanana\n\t cherry\n")

    def test_original_records_are_written_unchanged(self):
        result = self.run_msort(b"  z\n a\n", args=["-b"])

        self.assert_success(result, b" a\n  z\n")

    def test_duplicate_records_remain_duplicated(self):
        result = self.run_msort(b" beta\nbeta\n beta\n", args=["-b"])

        self.assert_success(result, b" beta\n beta\nbeta\n")

    def test_empty_records_remain_present(self):
        result = self.run_msort(b"\n\n a\n", args=["-b"])

        self.assert_success(result, b"\n\n a\n")

    def test_blank_only_records_use_original_bytes_as_tie_breaker(self):
        result = self.run_msort(b"\t\n \n  \n\n", args=["-b"])

        self.assert_success(result, b"\n\t\n \n  \n")

    def test_equal_comparison_keys_use_original_records_as_tie_breaker(self):
        result = self.run_msort(b"  beta\n beta\nbeta\n", args=["-b"])

        self.assert_success(result, b"  beta\n beta\nbeta\n")

    def test_blanks_after_the_first_nonblank_byte_are_not_ignored(self):
        result = self.run_msort(b"a \na\t\na\n", args=["-b"])

        self.assert_success(result, b"a\na\t\na \n")

    def test_vertical_tab_is_not_a_leading_blank(self):
        result = self.run_msort(b"\x0bbeta\n beta\nalpha\n", args=["-b"])

        self.assert_success(result, b"\x0bbeta\nalpha\n beta\n")

    def test_handles_input_without_final_newline(self):
        result = self.run_msort(b" b\n a", args=["-b"])

        self.assert_success(result, b" a\n b\n")

    def test_empty_input_produces_empty_output(self):
        result = self.run_msort(b"", args=["-b"])

        self.assert_success(result, b"")

    def test_binary_bytes_after_leading_blanks_remain_supported(self):
        result = self.run_msort(b" \xff\n\t\x00\n a\n", args=["-b"])

        self.assert_success(result, b"\t\x00\n a\n \xff\n")

    def test_default_ascending_sort_remains_bytewise(self):
        result = self.run_msort(b" b\na\n a\n")

        self.assert_success(result, b" a\n b\na\n")

    def test_rejects_unknown_options(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "-x").write_bytes(b"z\na\n")
            Path(temp_dir, "--unknown").write_bytes(b"z\na\n")
            for option in ("-x", "--unknown"):
                with self.subTest(option=option):
                    result = self.run_msort(args=[option], cwd=temp_dir)

                    self.assert_usage_failure(result)

    def test_rejects_path_followed_by_blank_option(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            for option in ("-b", "--ignore-leading-blanks"):
                with self.subTest(option=option):
                    result = self.run_msort(args=[temp_file.name, option])

                    self.assert_usage_failure(result)

    def test_rejects_two_paths_with_or_without_blank_option(self):
        with tempfile.NamedTemporaryFile() as first:
            with tempfile.NamedTemporaryFile() as second:
                for args in (
                    [first.name, second.name],
                    ["-b", first.name, second.name],
                    ["--ignore-leading-blanks", first.name, second.name],
                ):
                    with self.subTest(args=args):
                        result = self.run_msort(args=args)

                        self.assert_usage_failure(result)

    def test_rejects_repeated_and_mixed_blank_options(self):
        for args in (
            ["-b", "-b"],
            ["-b", "--ignore-leading-blanks"],
            ["--ignore-leading-blanks", "-b"],
            ["--ignore-leading-blanks", "--ignore-leading-blanks"],
        ):
            with self.subTest(args=args):
                result = self.run_msort(args=args)

                self.assert_usage_failure(result)


if __name__ == "__main__":
    unittest.main()
