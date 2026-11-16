# Debug mode

- Reproduce first, then trace, isolate, root-cause, fix, and verify with a test.
- Keyword `forensic`: do a line-by-line structural deep dive of the failing path before editing;
  list each hypothesis and the evidence that confirms or kills it.
- Run long processes in background terminals; read their output instead of waiting.
- Apply hotfixes and rerun checks without asking, under the same destructive command guard as
  Code mode.
- Finish: hand off to `doc-master` with the changed files.
