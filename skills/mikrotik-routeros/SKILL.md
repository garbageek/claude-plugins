---
name: mikrotik-routeros
description: Inspect, diagnose, configure, and verify MikroTik RouterOS networks through available MCP, SSH or RouterOS API tools. Use for MikroTik inventory, topology, client connectivity, Wi-Fi, VLANs, routing, firewall and NAT, DHCP and DNS, VPNs, LTE failover, backups, upgrades, or Safe Mode.
---

# MikroTik RouterOS

Live work requires a configured management transport with access to the target. Offline RouterOS guidance uses the same references.

## Select the workflow

- Use the bundled [RouterOS CLI cheat sheet](references/mikrotik-routeros-cheat-sheet.md) to select actual commands by menu. It includes inspection commands and separately marked configuration examples. No site documents or network access are needed to read it.
- For live work, use [tool selection and setup](references/integration.md) to resolve an available transport. For device inventory, client identification, topology or snapshots, use [discovery](references/discovery.md).
- For incidents and performance, use [diagnostics](references/diagnostics.md). For NAT, policy routing, firewall or VLAN packet paths, use [packet paths](references/packet-paths.md).
- For authorized changes, backup, migration, upgrades or recovery, use [changes and recovery](references/changes.md).
- For RouterOS scripts, scheduled jobs, or API integrations, read [automation](references/automation.md).
- For a specific network, identify the site and use its supplied inventory, topology or recovery runbook. Look for relevant files in the active workspace documentation when no paths are given. Treat these files as optional site inputs, separate from this package. Verify live state before using settings from a snapshot. If a missing site input prevents verification or recovery, say exactly what remains unknown and continue with the supported portion of the task.

## Operational workflow

1. Classify the request as explanation, inspection/diagnosis, configure/fix, or disruptive operation. For diagnosis, use status reads and bounded, low-impact probes. Treat captures, scans, load tests, file creation, counter resets and existing scripts according to their actual side effects. Perform disruptive operations such as reboot, upgrade or broad migration only within explicitly requested scope and with a feasible recovery path.
2. Resolve the exact device or set of devices from configured names, tags and live role evidence. Check identity, version and the capabilities relevant to the task. An inventory entry identifies a configured target. Confirm reachability with a live read. For an offline question or a missing transport provide documentation-based guidance and state the missing evidence.
3. Read the smallest surface that distinguishes plausible causes. Label facts observed, inferred or unverified. Use live configuration for site facts, target help and the RouterOS manual for command semantics, and the active tool schema for callable parameters.
4. For an authorized change, compare current and desired state and identify the exact object, impact, recovery and verification. Skip writes when the requested state already exists. Before a remote write that can cut management access, verify a recovery method that still works if that access drops. If none is available, stop before the write, report the missing recovery prerequisite, and finish any safe reads. Otherwise apply the smallest recoverable increment.
5. Re-read the changed object, check fresh management access when relevant and verify the affected service from the right vantage point. Repair or revert an unsuccessful change within scope and confirm the outcome.
6. Report verified devices, the finding, actual changes, observed checks and material gaps. Distinguish configured, verified working, externally unverified, unsupported, not run, failed and confirmed rolled back. Use per-device outcomes when work spans multiple routers.

Typical requests include listing MikroTik routers, tracing a UDP port, diagnosing Wi-Fi roaming or adding a DHCP reservation. General networking theory, shopping and code that merely mentions a router belong to their respective workflows. [RouterOS CLI reference](https://manual.mikrotik.com/docs/cli-reference/).

Use the [MikroTik manual index](https://manual.mikrotik.com/llms.txt) to locate a specific guide, CLI menu or hardware page. Follow the primary sources in each reference and check the installed version. See [third-party notices](THIRD-PARTY-NOTICES.md) for adapted material.
