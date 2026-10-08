---
name: codex-ubuntu-server
description: Install, authenticate, update, diagnose, or recover Codex CLI on Ubuntu Server, including managed remote control and independent self-maintenance handoff. Use for headless Ubuntu hosts; not for desktop app updates or general server administration.
---

# Codex on Ubuntu Server

Complete the requested lifecycle task on the identified Ubuntu host as its normal Unix user. Prefer standalone installation for new hosts; preserve an existing installation method and app-server owner unless migration is requested.

For installing, upgrading, disabling or removing plugins **inside** Codex, use
[install-agent-plugins](../install-agent-plugins/SKILL.md). This skill owns the
Codex CLI installation and Ubuntu process/service lifecycle, not plugin packages.

## Establish context

- Resolve the target host, Unix user, and operation from the conversation or available connection. Ask only for genuinely missing information. A local Windows shell is not the Ubuntu target.
- Distinguish instructions-only requests from host operations. Creating or reading this skill does not authorize installations, updates, authentication, or service changes.
- Inspect the selected executable, version, authentication status, and relevant process owner before modifying an existing installation. Do not print credential files.
- Check command availability with the target CLI's `--help`. The references provide a baseline, not a guarantee for every release. Consult linked official documentation for changing product behavior.

## Procedures

- Installation, headless login, normal CLI use, or requested remote control: read [references/setup.md](references/setup.md).
- Update, self-maintenance, version skew, app-server ownership, or reboot recovery: read [references/maintenance.md](references/maintenance.md).

Read only the applicable reference; load the other when needed.

## Operational invariants

- Run Codex without `sudo`, using the same user and Codex state directory as normal work. System dependencies may require administrative rights.
- Ordinary SSH CLI work does not require remote control. Enable remote control or boot persistence only when requested or already part of the intended deployment.
- Identify the lifecycle owner before restarting an app-server. An externally managed instance is not automatically broken; use its owning service.
- Run one updater at a time. Wait for its result before installer fallback. After one failed fallback, investigate rather than repeating mutations.
- If maintenance can terminate the agent or its transport, hand it to an independent host supervisor before changing the executing installation. Prefer a user systemd transient service; use `setsid` plus `nohup` as a best-effort fallback.
- Confirm accepted handoff and record its result channel. Acceptance means started, not completed.
- Distinguish downloaded package, selected CLI, managed daemon package, and running process. CLI version alone does not establish daemon replacement.
- Continue authorized ordinary steps autonomously. For device authentication or a tool-enforced protected action, complete independent preparation, request the minimum user action, then resume verification.

## Completion

Report target, concrete changes, selected executable/version, authentication result, applicable daemon state, and unresolved diagnostic failures. Verify detached maintenance through its result channel or explicitly report completion unverified. Do not claim reboot persistence or a running replacement without evidence.
