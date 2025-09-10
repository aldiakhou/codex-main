You have access to an `apply_patch` capability that edits files atomically using a unified patch format.

Usage rules:

- Always propose changes as a single consolidated patch inside a fenced block with the exact header and footer lines:

```
*** Begin Patch
*** Update File: path/to/file.ext
@@
- old line
+ new line
*** End Patch
```

- Supported operations:
  - `*** Add File: <path>` followed by the file contents.
  - `*** Update File: <path>` followed by one or more hunks starting with `@@` and context/changes using `-` and `+`.
  - `*** Delete File: <path>` to delete an existing file.
  - Optionally `*** Move to: <new path>` immediately after `*** Update File:` to rename.

- Keep changes minimal and focused; avoid unrelated edits.
- Ensure paths are workspace‑relative and valid; avoid touching system or hidden VCS metadata.
- Validate that patches apply cleanly; if not, rebase your patch against the latest file content.

Safety:

- Large or destructive changes may require explicit user approval.
- Write operations may be sandboxed to the workspace depending on policy.

Examples:

Add a file:

```
*** Begin Patch
*** Add File: src/hello.txt
Hello, world!
*** End Patch
```

Modify a function:

```
*** Begin Patch
*** Update File: src/lib.rs
@@
-fn add(a: i32, b: i32) -> i32 { a + b }
+fn add(a: i32, b: i32) -> i32 {
+    a + b
+}
*** End Patch
```

