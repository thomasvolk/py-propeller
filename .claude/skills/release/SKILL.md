---
name: release
description: "Bump the version in pyproject.toml and create or update CHANGELOG.md with a synthesized summary of commits on the current branch relative to main. Accepts a version string as argument (e.g. 0.2.0)."
argument-hint: <version>
---

# release

Prepare a release for version **$ARGUMENTS**.

Work through every step in order. Do not skip any step.

---

## Step 1 — Validate the argument

If `$ARGUMENTS` is empty or is not a valid semantic version string (digits separated by dots, e.g. `1.2.3` or `0.2.0`), stop immediately and tell the user:

> Usage: /release <version>  e.g. /release 0.2.0

Do not continue.

---

## Step 2 — Collect commits relative to main

Run the following command to get the list of commits on the current branch that are not yet on `main`:

```
git log main..HEAD --oneline
```

If the output is empty (no commits ahead of main), warn the user and ask if they want to continue anyway.

Also capture the current branch name:

```
git rev-parse --abbrev-ref HEAD
```

---

## Step 3 — Synthesize the changelog entry

Analyse the commit messages collected in Step 2 and group them into these categories (omit any category with no entries):

- **Added** — new features or capabilities
- **Changed** — changes to existing behaviour
- **Fixed** — bug fixes
- **Removed** — removed features or capabilities
- **Internal** — refactoring, test additions, tooling, documentation (only include if meaningful to an end-user reading the changelog)

Write concise, user-facing bullet points — not raw commit messages. Merge similar commits into a single entry. Drop noise commits (typo fixes, minor formatting, merge commits).

---

## Step 4 — Update pyproject.toml

Read `pyproject.toml`. Find the line:

```
version = "<current-version>"
```

under the `[project]` table and replace the version value with `$ARGUMENTS`.

Write the updated file back to `pyproject.toml`.

---

## Step 5 — Update CHANGELOG.md

Read `CHANGELOG.md` if it exists; otherwise start from an empty document.

Prepend a new release section at the top of the changelog (below the title if one exists), using the format below. Use today's date in `YYYY-MM-DD` format.

### CHANGELOG.md format

```
# Changelog

## [$ARGUMENTS] — YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Fixed
- ...

### Removed
- ...

### Internal
- ...

---

{existing content below this line}
```

- Only include sections that have at least one bullet point.
- Use the separator `---` between releases.
- If `CHANGELOG.md` already contains a section for `$ARGUMENTS`, replace it rather than prepend a duplicate.

Write the updated file to `CHANGELOG.md`.

---

## Step 6 — Report

Print a short summary:

- Version bumped: old → new
- Commits included: N commits from branch `<branch>` relative to `main`
- Sections written to CHANGELOG.md: (list the section headings that were populated)

Do not commit, tag, or push anything. Leave that to the user.
