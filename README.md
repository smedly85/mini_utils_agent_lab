# Mini Utils Agent Lab

This repository contains three intentionally small C/Linux-style utilities used as a controlled software-maintenance research project.

## Utilities

The planned utilities are:

* `msort`: line-oriented sorting;
* `mcompress`: byte-oriented compression and decompression;
* `mls`: limited directory listing.

These utilities are intentionally limited and are not intended to reproduce complete GNU Coreutils behavior.

## Project Status

This repository is currently in its initialization stage. Utility implementations, tests, build tooling, and CI will be added incrementally.

## Intended Build Interface

The intended build and test interface is:

* `make`
* `make test`
* `make asan`
* `make clean`

Some commands may not be available until the corresponding infrastructure is implemented.

## Platform and Language

Utility code is written in C11. Narrowly scoped POSIX interfaces may be used where required. The initial execution targets are Linux and macOS.

Python is used only for public tests and repository tooling. Python code must remain compatible with Python 3.9.6.

## Repository Boundaries

This public repository contains source code, public specifications, public tests, contributor documentation, and public CI configuration.

Hidden tests, private agent prompts, credentials, trusted evaluator logic, and confidential experiment data are maintained outside this repository.

## Contribution Workflow

After initialization, maintenance changes will normally begin with a GitHub issue and proceed through an issue-specific branch, pull request, automated checks, review, and a merge decision.
