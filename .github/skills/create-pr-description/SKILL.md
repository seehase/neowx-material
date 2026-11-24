---
name: create-pr-description
description: Create a copy-and-paste ready pull request title and Markdown description from the branch changes, using .github/PULL_REQUEST_TEMPLATE.md. Use only when the user says "create pr description".
---

# Create PR Description

Run this when the user asks for a "create pr description" (never automatically). Do not commit, push or open the PR.

## Steps

1. **Collect changes:** `git status`, `git log origin/master..HEAD --oneline` and `git diff origin/master..HEAD --stat`;
   read the diff only as far as needed to understand the main topic.
3. **Title:** exactly `fix: Short description`.
   * Short and precise; if several things changed, describe only the most important topic.
   * The short description starts with a capital letter, e.g. `fix: Remove team access on secret alerts`.
4. **Description:** fill in `.github/PULL_REQUEST_TEMPLATE.md`, keeping its headings, order and checklist items.
   * Summary: one or two sentences.
   * Changes: only the main changes, short bullets (no file-by-file listing). Also list the "unrelated" changes in
     the branch (e.g. `AGENTS.md`, `README.md`, `.github/skills/`, `docs/plans/`) as a short bullet each, so
     reviewers know they are intentional.
   * Checklist: tick only items that are actually true (e.g. tests were run); leave others unticked.
   * Reviewer Notes / Related Issues: short, mention operational or config impact (new env vars, behaviour changes)
     and the ticket; remove the HTML comment placeholders.
5. **Output format:** present title and description each in its own fenced code block so they can be copied directly.
   Use a four-backtick fence for the description (it is Markdown and may contain inner code fences), and a plain
   fence for the title. Print nothing else except an optional one-line note (e.g. the ticket id source).

## Output example

Title:

```text
fix: [EPDF-1234] Remove team access on secret alerts
```

Description:

````markdown
# Summary

Short summary of the delivered change.

## Changes

- Main change one
- Main change two

## Checklist

- [x] I have reviewed the changes for accuracy and clarity
...

## Reviewer Notes

Short notes.

## Related Issues

EPDF-1234
````
