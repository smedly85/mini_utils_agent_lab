# Repository Purpose

`mini_utils_agent_lab` is the public target repository for a thesis project studying secure, role-separated agentic software maintenance through GitHub issues, branches, pull requests, reviews, evaluation, and merge decisions.

# Repository Boundary

This public repository may contain C utility source code, public tests, public specifications, contributor documentation, and GitHub Actions workflows.

This repository must never contain hidden or trusted tests, private agent prompts, controller implementation code, model credentials, GitHub tokens, evaluator answer keys, confidential experiment results, or automatic merge credentials.

Those private components belong in the separate `agent_maintenance_controller` repository.

# Utilities

This repository will contain three intentionally small C11 utilities:

* `msort`, a line-oriented sorting utility;
* `mcompress`, a byte-oriented compression utility;
* `mls`, a limited directory-listing utility.

These utilities are not intended to reproduce complete GNU Coreutils behavior.

# Engineering Standards

Changes must compile using the C11 language standard. Use standard C11 facilities where possible; narrowly scoped POSIX interfaces may be used when required for operating-system functionality such as directory listing. The initial supported execution environments are Linux and macOS unless an issue explicitly expands platform support.

Changes must avoid third-party runtime dependencies, enable strict compiler warnings, check dynamic-memory and integer-overflow conditions where relevant, handle errors clearly, stay small and focused, avoid unrelated refactoring, avoid premature shared abstractions, and keep final newlines in text files. 

Python is used only for repository tooling and public tests; the utility binaries themselves are implemented in C. All Python scripts and public tests in this repository must run under Python 3.9.6.

# Build and Test Interface

The intended build and test interface is:

* `make`
* `make test`
* `make asan`
* `make clean`

These commands are the intended interface but may not exist until the corresponding infrastructure is added.

# Testing Policy

Public tests belong in `tests/`.

Hidden correctness, safety, adversarial, and acceptance tests must remain outside this repository.

Tests must be real behavioral tests, not empty or placeholder tests.

# Change Discipline

Future changes must correspond to a defined issue or initialization task, remain narrowly scoped, include tests when behavior changes, preserve existing behavior unless the specification changes it, avoid modifying unrelated files, and leave the working tree understandable and reviewable.

# Git Safety

An assistant must not commit, push, force-push, delete branches, open pull requests, merge pull requests, or modify repository settings unless the user explicitly requests that exact action.

Direct changes to `main` should be limited to researcher-controlled initialization. Later maintenance work should use issue-specific branches and pull requests.

# Completion Requirements

Before reporting a coding task complete, the assistant must inspect the final diff, run the relevant available build and test commands, report commands executed and their outcomes, disclose tests that could not be run, and disclose warnings, assumptions, and remaining risks.
