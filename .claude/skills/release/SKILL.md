---
name: release
description: "Bump the version in pyproject.toml and create or update CHANGELOG.md with a synthesized summary of commits on the current branch relative to main (or, when on main with nothing ahead, the uncommitted working diff). Accepts a version string as argument (e.g. 0.2.0)."
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

Capture the current branch name:

```
git rev-parse --abbrev-ref HEAD
```

Run the following command to get the list of commits on the current branch that are not yet on `main`:

```
git log main..HEAD --oneline
```

If the output is non-empty, proceed to Step 3 in **commit-log mode** using these commits.

If the output is empty, branch on the current branch name:

- **On `main`, with nothing ahead:** there is no commit range to summarize, but there may still be unreleased work sitting uncommitted in the working tree. Automatically switch to **working-diff mode**: do not ask the user, just proceed. Collect:

  ```
  git status --porcelain
  git diff
  git diff --staged
  ```

  If all three are empty (nothing ahead, nothing uncommitted — genuinely nothing to release), warn the user and ask if they want to continue anyway.

- **On any other branch** (a feature/topic branch with no commits ahead of `main`): this is unexpected — warn the user and ask if they want to continue anyway, same as before. Do not silently fall back to working-diff mode here; an empty feature branch is more likely a mistake than an uncommitted-release situation.

---

## Step 3 — Synthesize the changelog entry

### Commit-log mode

Analyse the commit messages collected in Step 2 and group them into these categories (omit any category with no entries):

- **Added** — new features or capabilities
- **Changed** — changes to existing behaviour
- **Fixed** — bug fixes
- **Removed** — removed features or capabilities
- **Internal** — refactoring, test additions, tooling, documentation (only include if meaningful to an end-user reading the changelog)

Write concise, user-facing bullet points — not raw commit messages. Merge similar commits into a single entry. Drop noise commits (typo fixes, minor formatting, merge commits).

### Working-diff mode

Read the actual diff content (`git diff` / `git diff --staged`, plus the contents of any untracked files from `git status --porcelain`) rather than commit messages, and group changes into the same categories. When reading the diff:

- Attribute a change to **Added** only if it introduces genuinely new behaviour (e.g. a new CLI flag, a new branch in dispatch logic, a new public function). Reference the spec/PRD under `specs/` if one exists for the epic being released — it usually names the feature precisely.
- Treat documentation-only changes (README/docs edits) that describe a feature which *already shipped* in an earlier release as out of scope for this changelog entry — do not re-announce old features just because their docs were touched now. Only include doc changes that describe genuinely new behaviour introduced in this same diff.
- Treat new/changed test files as evidence supporting an Added/Changed/Fixed entry, not as their own Internal bullet, unless the diff contains no corresponding implementation change (pure test-suite additions with no behaviour change do belong under Internal).
- If the diff spans unrelated changes, split them into separate bullets rather than merging.

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
- Synthesis source: either "N commits from branch `<branch>` relative to `main`" (commit-log mode) or "uncommitted working diff on `main` (no commits ahead)" (working-diff mode)
- Sections written to CHANGELOG.md: (list the section headings that were populated)

Do not commit, tag, or push anything. Leave that to the user.
