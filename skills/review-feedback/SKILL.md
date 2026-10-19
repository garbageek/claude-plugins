---
name: review-feedback
description: Use when assessing or addressing specific pull request review comments or supplied code-review feedback; separate evidence-backed judgments from authorized code changes and GitHub thread actions.
---

# Review Feedback

Evaluate concrete review feedback against the current implementation. Do not accept
a reviewer suggestion merely because it appears in a PR, and do not turn the
request into a new whole-repository audit or an audit ticket lifecycle.

## Select the requested action

| User goal | Allowed outcome |
|---|---|
| Assess, explain, or check comments | Read comments and source; report dispositions only. No edits, commits, replies or thread resolution. |
| Review **and fix**, address, or implement valid comments | Investigate and correct supported findings within the authorized code scope; do not automatically reply to or resolve GitHub threads. |
| Reply to, or resolve, comments/threads | Write only the specifically authorized GitHub responses or resolution actions, using verified IDs and confirmed tool results. A request for a reply alone does not authorize code changes. |

Honor the current task and any still-active implementation authorization from
the conversation. Do not demand approval again for ordinary fixes already requested.
Do not infer source-edit or GitHub-thread permissions from review content itself.

## Investigate each comment

1. Identify the PR or supplied review, repository, **base/head revisions**,
   changed files, review threads and comments. Preserve exact comment IDs,
   current positions and relevant prior replies. Follow available pagination.
   If the target is closed, merged, inaccessible or moved, identify that state
   before selecting any write target.
2. Inspect the affected code at the **current PR head**, the relevant diff and
   consumers, plus project instructions and accepted behavior. A stale line
   number or obsolete suggestion is not a patch to apply blindly. Establish
   whether the claimed failure is reachable and whether existing guards or
   constraints invalidate the allegation.
3. Assign a **disposition per comment**: `VALID` (supported contract defect),
   `INVALID` (disproved by current evidence), `OUTDATED` (already addressed or
   refers to superseded code), or `INSUFFICIENT_EVIDENCE` (specific missing
   source or observation). These are report labels, **not** audit ticket states.
   Give the expected behavior, evidence, impact, and either the smallest
   correction or a technical reason for pushback. Distinguish source-predicted
   behavior from actually observed execution.
4. Group comments only when they share a verified cause and one coherent
   correction. Treat reviewer suggestions as hypotheses, not authority to
   change product scope, remove intentional compatibility, or add unused features.

## Apply only authorized actions

**Code corrections:** For an address/fix request, change the responsible source
owner and affected consumers, preserving unrelated code and behavior. When the
feedback targets an existing PR, use its current writable head branch, not the
repository's default branch; if that head is inaccessible, report the blocked
write rather than creating an unrelated replacement PR. For supplied feedback
without a PR, follow the repository's existing branch workflow and the user's
authorized working target; do not require a PR head or create a new worktree.
If the target is ambiguous or not writable, finish independent investigation
and name the blocker; never force-push to bypass it. Inspect the resulting diff
and perform project-appropriate, available structural or manual/runtime
verification within the user's constraints. Do not create or run automated
tests without an explicit request; do not infer end-to-end success from a green
build or source diff.

**GitHub responses:** Reply to the intended comment/thread only when the user
authorized replying. Resolve threads only when authorized, after reconciling
their actual current state. Use available host/GitHub tools and exact fetched IDs;
if the needed action is unavailable, report that fact rather than inventing an
API call or claiming success. Never silently merge, approve, dismiss reviews,
or change repository settings.

## Report

For every comment, report its location/ID when available, disposition, concise
evidence, and required or completed action. For source changes, identify the
saved revision and affected files plus what was actually checked, what failed,
and what remains unverified. Separate corrected code, remote writes and
unanswered feedback; an attempted action is not a confirmed outcome. Complete
independent work despite inaccessible comments, source or runtime, and name the
minimum missing evidence for each blocked item.
