---
name: release
description: Bumps the project version in pyproject.toml and files the CHANGELOG.md entry for a release, turning [Unreleased] into the given version and date. Use when the user runs `/release <version>` or asks to release, cut, or publish a new version of py-propeller.
allowed-tools: Read, Edit, Bash, AskUserQuestion
---

# release — bump version and file the changelog entry

You are running the `release` skill. It takes a version number as its argument, sets it in `pyproject.toml`, and turns the CHANGELOG's `[Unreleased]` section into that version's dated entry — or, if there's nothing unreleased yet, asks what belongs in it rather than inventing content.

## 0. Get the version

The argument is the version number (e.g. `0.8.0`). If it wasn't given, ask the user for it — don't guess a version.

## 1. Bump pyproject.toml

Read `pyproject.toml` and find the `version = "..."` line under `[project]`. Replace it with the new version. Note the old → new version for the report in step 3.

## 2. File the CHANGELOG entry

Read `CHANGELOG.md`.

- **`## [Unreleased]` heading exists, with entries below it** (any non-blank content before the next `## [` heading or end of file): replace the heading line with `## [<version>] — <today's date>` (get today's date via `date +%Y-%m-%d`, matching the file's existing `YYYY-MM-DD` entries). Leave the entries under it untouched. If that section doesn't already end in a `---` separator before the next version heading, add one — matching every other version-to-version boundary in the file.
- **`## [Unreleased]` heading exists but is empty, or is missing entirely**: stop and ask the user what belongs in this release's changelog entry (categories like Added/Changed/Fixed/Internal, matching the file's existing style). Never fabricate release notes from commit history or guesswork.

After filing the entry, add a fresh empty `## [Unreleased]` heading (no subsections yet) above it, so future work has somewhere to land — unless the user says not to.

## 3. Report

State the version bump (old → new) and show the resulting CHANGELOG heading. Do not commit, tag, or push — that's a separate step the user asks for explicitly if they want it.
