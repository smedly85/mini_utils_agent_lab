Issue Tests
===========

`issue_tests` contains public acceptance tests for open GitHub issues.

`make test` remains the normal baseline regression suite and does not run
these opt-in issue acceptance tests.

`make issue-1-test` runs only the Issue 1 acceptance tests for `msort` reverse
sorting and option rejection behavior.

`make issue-1-check` runs the normal regression tests and the Issue 1
acceptance tests.

The Issue 1 tests are expected to fail on the pre-implementation baseline.
Submitters may inspect and run these tests while working on the issue.

These tests are public acceptance tests. They are not hidden tests, trusted
evaluator tests, or evaluator answer keys.
