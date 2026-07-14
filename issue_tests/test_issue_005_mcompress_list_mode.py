"""
Public acceptance tests for GitHub Issue 5: mcompress list mode.
"""

import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MCOMPRESS = (REPO_ROOT / "build" / "mcompress").resolve()
TIMEOUT_SECONDS = 5
HEADER = b"compressed_bytes uncompressed_bytes runs\n"


class Issue005McompressListModeTests(unittest.TestCase):
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

    def assert_listing(self, result, compressed_bytes, uncompressed_bytes, runs):
        expected = HEADER + (
            f"{compressed_bytes} {uncompressed_bytes} {runs}\n".encode("ascii")
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, expected)
        self.assertEqual(result.stderr, b"")

    def assert_malformed(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(result.stdout, (b"", HEADER))
        self.assertNotEqual(result.stderr, b"")

    def assert_usage_failure(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"usage:", result.stderr)

    def test_short_option_lists_issue_example(self):
        result = self.run_mcompress(b"\x03A\x01B\x05C", args=["-l"])

        self.assert_listing(result, 6, 9, 3)

    def test_long_option_lists_issue_example(self):
        result = self.run_mcompress(b"\x03A\x01B\x05C", args=["--list"])

        self.assert_listing(result, 6, 9, 3)

    def test_list_mode_reads_one_file(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b"\x02A\x04B")
            temp_file.flush()

            result = self.run_mcompress(args=["-l", temp_file.name])

        self.assert_listing(result, 4, 6, 2)

    def test_list_mode_reports_empty_input(self):
        result = self.run_mcompress(b"", args=["--list"])

        self.assert_listing(result, 0, 0, 0)

    def test_list_mode_reports_one_run(self):
        result = self.run_mcompress(b"\x07Z", args=["-l"])

        self.assert_listing(result, 2, 7, 1)

    def test_list_mode_reports_several_runs(self):
        result = self.run_mcompress(b"\x02A\x04B\x01C\x08D", args=["-l"])

        self.assert_listing(result, 8, 15, 4)

    def test_count_255_is_unsigned(self):
        result = self.run_mcompress(b"\xffA", args=["--list"])

        self.assert_listing(result, 2, 255, 1)

    def test_multiple_255_counts_are_summed(self):
        result = self.run_mcompress(b"\xffA\xffB\x01C", args=["-l"])

        self.assert_listing(result, 6, 511, 3)

    def test_binary_values_do_not_affect_statistics(self):
        result = self.run_mcompress(b"\x02\x00\x03\xff", args=["--list"])

        self.assert_listing(result, 4, 5, 2)

    def test_compressed_bytes_and_runs_count_exact_input_structure(self):
        compressed = b"\x01A\x02B\x03C\x04D\x05E"
        result = self.run_mcompress(compressed, args=["-l"])

        self.assert_listing(result, len(compressed), 15, 5)

    def test_list_mode_does_not_output_decompressed_bytes(self):
        result = self.run_mcompress(b"\x03A", args=["-l"])

        self.assert_listing(result, 2, 3, 1)
        self.assertNotIn(b"AAA", result.stdout)

    def test_list_mode_rejects_zero_count_at_start(self):
        result = self.run_mcompress(b"\x00A", args=["-l"])

        self.assert_malformed(result)

    def test_list_mode_rejects_zero_count_after_valid_runs(self):
        result = self.run_mcompress(b"\x03A\x00B", args=["--list"])

        self.assert_malformed(result)

    def test_list_mode_rejects_trailing_unmatched_count(self):
        result = self.run_mcompress(b"\x03A\x02", args=["-l"])

        self.assert_malformed(result)

    def test_list_mode_rejects_malformed_file_input(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b"\x02A\x00B")
            temp_file.flush()

            result = self.run_mcompress(args=["--list", temp_file.name])

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
                result = self.run_mcompress(args=["-l", first.name, second.name])

        self.assert_usage_failure(result)

    def test_rejects_missing_input_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = str(Path(temp_dir, "missing.rle"))
            result = self.run_mcompress(args=["-l", missing])

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertNotEqual(result.stderr, b"")

    def test_rejects_repeated_and_mixed_list_aliases(self):
        for args in (
            ["-l", "-l"],
            ["-l", "--list"],
            ["--list", "-l"],
            ["--list", "--list"],
        ):
            with self.subTest(args=args):
                result = self.run_mcompress(args=args)

                self.assert_usage_failure(result)

    def test_rejects_list_mode_combined_with_other_modes(self):
        for args in (
            ["-c", "-l"],
            ["-d", "-l"],
            ["-l", "-c"],
            ["-l", "-d"],
            ["--compress", "--list"],
            ["--decompress", "--list"],
            ["--list", "--compress"],
            ["--list", "--decompress"],
            ["-t", "-l"],
            ["-l", "-t"],
            ["--test", "--list"],
            ["--list", "--test"],
        ):
            with self.subTest(args=args):
                result = self.run_mcompress(args=args)

                self.assert_usage_failure(result)


if __name__ == "__main__":
    unittest.main()
