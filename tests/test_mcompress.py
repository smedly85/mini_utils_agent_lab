"""
tests/test_mcompress.py
Public behavioral tests for the mcompress utility.
Author: Sonja Brown
"""

import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MCOMPRESS = REPO_ROOT / "build" / "mcompress"
TIMEOUT_SECONDS = 5


class McompressTests(unittest.TestCase):
    def run_mcompress(self, args, input_bytes=b""):
        if not MCOMPRESS.exists():
            self.fail("build/mcompress does not exist; run make before running tests")

        return subprocess.run(
            [str(MCOMPRESS)] + args,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            timeout=TIMEOUT_SECONDS,
        )

    def test_compresses_ordinary_repeated_bytes(self):
        result = self.run_mcompress(["-c"], b"AAAABCC")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"\x04A\x01B\x02C")
        self.assertEqual(result.stderr, b"")

    def test_decompresses_valid_encoded_bytes(self):
        result = self.run_mcompress(["-d"], b"\x04A\x01B\x02C")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"AAAABCC")
        self.assertEqual(result.stderr, b"")

    def test_compression_decompression_round_trip(self):
        original = b"aaabccccccccdde"
        compressed = self.run_mcompress(["--compress"], original)
        self.assertEqual(compressed.returncode, 0)
        self.assertEqual(compressed.stderr, b"")

        decompressed = self.run_mcompress(["--decompress"], compressed.stdout)
        self.assertEqual(decompressed.returncode, 0)
        self.assertEqual(decompressed.stdout, original)
        self.assertEqual(decompressed.stderr, b"")

    def test_empty_input_in_compression_mode(self):
        result = self.run_mcompress(["-c"], b"")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr, b"")

    def test_empty_input_in_decompression_mode(self):
        result = self.run_mcompress(["-d"], b"")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr, b"")

    def test_arbitrary_binary_bytes(self):
        original = b"\x00\x00\n\xff\xff\xff\x00"
        compressed = self.run_mcompress(["-c"], original)

        self.assertEqual(compressed.returncode, 0)
        self.assertEqual(compressed.stdout, b"\x02\x00\x01\n\x03\xff\x01\x00")
        self.assertEqual(compressed.stderr, b"")

        decompressed = self.run_mcompress(["-d"], compressed.stdout)
        self.assertEqual(decompressed.returncode, 0)
        self.assertEqual(decompressed.stdout, original)
        self.assertEqual(decompressed.stderr, b"")

    def test_splits_run_of_256_equal_bytes(self):
        result = self.run_mcompress(["-c"], b"x" * 256)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"\xffx\x01x")
        self.assertEqual(result.stderr, b"")

    def test_reads_compression_input_from_one_file_path(self):
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            temp_file.write(b"ZZZY")
            temp_file.flush()

            result = self.run_mcompress(["-c", temp_file.name])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"\x03Z\x01Y")
        self.assertEqual(result.stderr, b"")

    def test_reads_decompression_input_from_one_file_path(self):
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            temp_file.write(b"\x03Z\x01Y")
            temp_file.flush()

            result = self.run_mcompress(["-d", temp_file.name])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"ZZZY")
        self.assertEqual(result.stderr, b"")

    def test_rejects_zero_count_during_decompression(self):
        result = self.run_mcompress(["-d"], b"\x00A")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"malformed", result.stderr)

    def test_rejects_unmatched_final_count_byte(self):
        result = self.run_mcompress(["-d"], b"\x03")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"malformed", result.stderr)

    def test_rejects_invocation_with_no_mode(self):
        result = self.run_mcompress([], b"")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"usage:", result.stderr)

    def test_rejects_conflicting_modes(self):
        result = self.run_mcompress(["-c", "-d"], b"")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"usage:", result.stderr)

    def test_rejects_unknown_option(self):
        result = self.run_mcompress(["--unknown"], b"")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"usage:", result.stderr)

    def test_rejects_more_than_one_input_path(self):
        result = self.run_mcompress(["-c", "first.bin", "second.bin"], b"")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"usage:", result.stderr)

    def test_reports_missing_input_file(self):
        missing_path = str(REPO_ROOT / "tests" / "missing-mcompress-input.bin")
        result = self.run_mcompress(["-c", missing_path], b"")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"cannot open", result.stderr)


if __name__ == "__main__":
    unittest.main()
