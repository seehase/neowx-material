---
name: markdown-linting
description: Write or edit Markdown files in this repo (docs, workflow .md sources, README). Use for markdownlint-cli2 compliance.
---

# Markdown Linting

* All Markdown files must be compliant with `markdownlint-cli2`.
* The lint rules are defined in `.markdownlint.yaml`.
* Ensure proper formatting, line lengths (120 chars), and structure.
* Run `markdownlint-cli2 '**/*.md'` after changes and fix all reported errors before considering the work complete.
* Keep the CLI version in `.pre-commit-config.yaml` aligned with the version used by CI (currently `v0.24.0`).

Follow these `markdownlint` rules when generating or modifying Markdown files:

1. **Line Length (MD013)**:
   * Limit lines to **120 characters**.
   * Exception: Tables may exceed this limit.
   * Break long lines at appropriate points (e.g., after punctuation or between words).

2. **List Markers (MD030)**:
   * Use exactly **one space** after list markers (e.g., `* Item`, `1. Item`).
   * Do not use multiple spaces (e.g., `*   Item` is invalid).

3. **Fenced Code Blocks (MD031, MD040)**:
   * Always surround fenced code blocks with **blank lines** (one before, one after).
   * Always specify the **language** for the code block (e.g., `go`, `bash`, `text`, `yaml`).

4. **Headings (MD024)**:
   * Do not use duplicate headings within the same document.
   * If similar sections are needed, make the headings unique (e.g., "Logging Usage", "Notification Usage").

5. **Inline HTML (MD033)**:
   * Inline HTML is allowed.

6. **General Formatting**:
   * Ensure consistent indentation.
   * Use proper Markdown syntax for links and images.

7. **Table Column Style (MD060)**:
   * Keep this rule enabled and fix reported table-spacing errors, including delimiter rows.
   * Use `markdownlint-cli2 --fix` on affected files when appropriate, then rerun the linter to verify the result.
