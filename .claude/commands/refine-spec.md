---
description: Iteratively refine a technical specification with open Q&A until confidence reaches 90%. Creates the spec from the PRD if it doesn't exist. Reconciles answered questions and checked decisions into architecture, data model, and tasks.
argument-hint: <epic-id>
---

You are running /refine-spec for epic **$ARGUMENTS**.

Work through the steps below **in order**. Do not skip any step.

---

## Step 1 — Load context

Read the following files:

- `specs/$ARGUMENTS.md` — the PRD for this epic (must exist)
- `specs/$ARGUMENTS-spec.md` — the technical specification (may not exist yet)

---

## Step 2 — Check for PRD

If `specs/$ARGUMENTS.md` does not exist, output the following message and stop immediately. Do not proceed to any further step.

> No PRD found for $ARGUMENTS. Run `/refine-epic $ARGUMENTS` first to create and refine the PRD before generating a technical specification.

---

## Step 3 — Create the spec if it does not exist

If `specs/$ARGUMENTS-spec.md` does not exist, derive the initial technical specification from the PRD.

For each functional requirement (F-x) and acceptance criterion (AC-x) in the PRD, plan at least one test task (type: test) and one implementation task (type: impl). Tests must appear before their corresponding implementation tasks — preserve strict TDD order throughout the task table.

Identify and document:
- The high-level architecture: how the system is structured, which components exist, and how they interact
- The data model: key types, structures, and their relationships
- Key architecture decisions: choices with meaningful trade-offs that affect the design

Place all high-impact architecture and technology decisions in the **Open Decisions** section, formatted as unchecked checkboxes so the user can select preferred options.

Use the document structure defined at the bottom of these instructions.

If `specs/$ARGUMENTS-spec.md` already exists, skip this step and proceed to Step 4.

---

## Step 4 — Reconcile answered questions

Read the **Open Questions** section of `specs/$ARGUMENTS-spec.md`.

For every question whose **Answer** field is filled in:

1. Interpret what the answer implies for the specification.
2. Apply the implication to the appropriate section:
   - An implementation detail or component behaviour → update **Architecture Overview** or the relevant **Components** subsection
   - A type, field, or schema detail → add or update a row in **Data Model**
   - A new or revised behaviour that needs testing → add task rows to **Implementation Tasks**, keeping strict TDD order (test before impl)
   - A high-impact architectural choice with remaining trade-offs → add a new **D-N** entry to **Open Decisions**
3. Remove the answered question from the Open Questions section entirely.
4. Record what was reconciled in the Revision Log entry you will write in Step 7.

If there are no answered questions, skip this step and proceed to Step 5.

---

## Step 5 — Reconcile checked decisions

Read the **Open Decisions** section of `specs/$ARGUMENTS-spec.md`.

For every decision that has a selected option (a `[x]` checked box):

1. Interpret what the selected option implies for the specification.
2. Apply the implication to the appropriate section:
   - A structural or behavioural implication → Architecture Overview or Components
   - A type or schema implication → Data Model
   - A new task → Implementation Tasks (preserving TDD order)
3. Remove the fully-answered decision block from Open Decisions entirely.
4. Record what was reconciled in the Revision Log entry you will write in Step 7.

If there are no checked decisions, skip this step and proceed to Step 6.

---

## Step 6 — Assess confidence

Analyse the current state of `specs/$ARGUMENTS-spec.md` and assign a confidence level (0–100%) reflecting how completely and unambiguously the specification covers the PRD.

Use this rubric:

| Dimension | Questions to ask |
|-----------|-----------------|
| PRD coverage | Does every F-x and AC-x in the PRD have at least one corresponding task? |
| TDD ordering | Does every impl task have a test task that precedes it? |
| Architecture clarity | Are all components and their interactions described without ambiguity? |
| Data model completeness | Are all types and structures needed to implement the requirements defined? |
| Task specificity | Is each task small enough to be implemented and reviewed independently? |
| Open ambiguities | How many unanswered questions and unchecked high-impact decisions remain? |

Write a short plain-English explanation of what is missing or ambiguous that justifies the score.

Update the **Confidence Level** line in the document with the new score and explanation.

---

## Step 7 — Add new questions or decisions if confidence < 90%

If confidence is below 90%, identify the most critical unresolved ambiguities and add them to the appropriate section:

- Ambiguities the user can resolve by answering a question → add to **Open Questions**
- High-impact architectural choices with concrete trade-offs → add to **Open Decisions**

Rules for open questions:
- Each question must be specific and answerable.
- Provide 2–4 concrete options per question.
- Mark exactly one option as *(recommended — {one-line reason})*.
- Leave the **Answer** field empty for the user to fill in.
- Assign sequential Q-numbers continuing from any existing ones.

Rules for open decisions:
- Present 2–4 concrete options as unchecked checkboxes `[ ]`.
- Mark the recommended option with `*(recommended — {one-line reason})*`.
- Assign sequential D-numbers continuing from any existing ones.

If confidence is 90% or above, do not add questions or decisions. State that the specification is complete.

---

## Step 8 — Update the Revision Log

Append one new log entry at the bottom of the Revision Log section. Keep entries compact — one per cycle.

Format:

```
### Cycle N — Confidence: X%
- Reconciled: Q-1 → architecture updated (logger strategy), D-1 → data model updated (enum for state)
- Added: Q-2 (async runtime choice), D-2 (test harness choice)
```

If nothing was reconciled and nothing was added, still append the entry with the updated score and a brief note.

---

## Step 9 — Save the file

Write the fully updated document to `specs/$ARGUMENTS-spec.md`.

The document must maintain sections in this exact order:

```
# $ARGUMENTS · {Epic Title} — Technical Specification

## Overview
{One short paragraph summarising what this epic builds, derived from the PRD overview.}

**Confidence Level:** X% — {one-sentence explanation of what is missing}

---

## Architecture Overview
{Narrative description of the technical approach, component boundaries, and how they interact.}

---

## Components

### {Component Name}
{Responsibility, interface, and key behaviours.}

---

## Data Model

| Type | Fields | Notes |
|------|--------|-------|

---

## Implementation Tasks

Tasks are ordered TDD-first: every test task must appear before the impl task it covers.

| ID | Task | Type | PRD ref | Depends on |
|----|------|------|---------|------------|

---

## Open Questions
{Only unanswered questions live here. Answered questions are removed after reconciliation.}

---

## Open Decisions
{High-impact choices awaiting user selection via checkbox. Check your preferred option, then re-run /refine-spec to reconcile.}

---

## Revision Log
{One compact entry per cycle, oldest first.}
```

---

## Open question format

```
### Q-N · {Short descriptive title}

{The question in one or two sentences.}

**Options**
- A. {Option} — {brief rationale}
- B. {Option} — {brief rationale} *(recommended — {one-line reason})*
- C. {Option} — {brief rationale}

**Answer:**
```

---

## Open decision format

```
### D-N · {Decision title}

{One sentence describing the choice to be made and why it matters.}

- [ ] A. {Option} — {rationale}
- [ ] B. {Option} — {rationale} *(recommended — {one-line reason})*
- [ ] C. {Option} — {rationale}
```
