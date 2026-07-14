Issue Tests
===========

`issue_tests` contains public acceptance tests for open GitHub issues.

`make test` remains the normal baseline regression suite and does not run
these opt-in issue acceptance tests.

Each issue suite is opt-in and can be run independently:

* `make issue-1-test` runs the Issue 1 acceptance tests; `make issue-1-check`
  runs the normal regression suite first.
* `make issue-2-test` runs the Issue 2 acceptance tests; `make issue-2-check`
  runs the normal regression suite first.
* `make issue-3-test` runs the Issue 3 acceptance tests; `make issue-3-check`
  runs the normal regression suite first.
* `make issue-4-test` runs the Issue 4 acceptance tests; `make issue-4-check`
  runs the normal regression suite first.
* `make issue-5-test` runs the Issue 5 acceptance tests; `make issue-5-check`
  runs the normal regression suite first.

Issue tests are expected to fail on a pre-implementation baseline. Submitters
may inspect and run them while working on an issue.

These tests are public acceptance tests. They are not hidden tests, trusted
evaluator tests, or evaluator answer keys.
