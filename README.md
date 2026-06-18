# Mini Utils Agent Lab

This repository is a small public target repository for research on agentic software maintenance. It contains intentionally limited C utilities, public specifications, public tests, documentation, and public CI configuration.

The utilities are not intended to reproduce full GNU utility behavior.

## Implemented Utilities

### `msort`

`msort` is a line-oriented sorting utility. It reads newline-delimited records from standard input or one file, sorts records in ascending bytewise lexicographic order, preserves duplicate and empty records, and handles a final record without a trailing newline.

### `mcompress`

`mcompress` is a byte-oriented run-length compression utility. It supports `-c` / `--compress` and `-d` / `--decompress`, reads standard input or one file, and encodes each run as one count byte followed by one value byte. Valid counts are 1 through 255. Decompression rejects malformed compressed input.

### `mls`

`mls` is a limited directory-listing utility. It lists the current directory or one supplied directory, lists only immediate entries, includes hidden names, excludes `.` and `..`, and sorts names in ascending bytewise order. It uses the narrow POSIX `<dirent.h>` interface and does not implement full system `ls` behavior.

## Build And Test

The supported build and test commands are:

```text
make
make test
make asan
make clean
```

`make` builds all three release binaries. `make test` builds all required release binaries and runs the public tests. `make asan` builds AddressSanitizer and UndefinedBehaviorSanitizer versions. `make clean` removes generated build output.

Produced binaries:

```text
build/msort
build/mcompress
build/mls
build/msort_asan
build/mcompress_asan
build/mls_asan
```

## Test Status

The baseline contains 41 public behavioral tests:

* 10 for `msort`;
* 16 for `mcompress`;
* 15 for `mls`.

One `mls` case-sensitivity test is skipped on filesystems that cannot represent `A` and `a` as distinct names, so not all 41 tests necessarily execute on every filesystem.

## Compatibility And CI

The utility code is C11 and is built with strict compiler warnings. Public test tooling is Python 3.9-compatible. The target environments are Linux and macOS.

GitHub Actions runs on Ubuntu and macOS. CI builds the release binaries, runs the public tests, builds sanitizer binaries, and runs the public tests again against the sanitizer builds.

## Public/Private Research Boundary

This public repository may contain target source code, public tests, public specifications, documentation, and public CI.

Trusted hidden tests, private agent prompts, controller code, credentials, evaluator answer keys, automatic merge credentials, and confidential experimental results belong outside this repository.
