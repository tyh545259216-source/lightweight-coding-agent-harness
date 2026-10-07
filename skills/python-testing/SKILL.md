---
name: python-testing
description: Write regression tests, test generation, assertions, pytest collection, boundary and empty cases.
---

Read source/tests; import actual implementation. Add test_* functions in test_*.py with meaningful task-derived assertions and boundary cases. Preserve production source for test-only tasks. Use run_tests for canonical pytest. Exit 0 means collected tests passed; exit 5 means none. Repair import/collection failures. Report observed results; respect permissions.
