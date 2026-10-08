# Maintenance and recovery

Check the installed Codex version and command help on the target Ubuntu host before maintenance; command options and daemon behavior can vary by release.

## Inspect

```bash
id -un
command -v codex
readlink -f "$(command -v codex)"
codex --version
codex login status
```

For app-server tasks, also inspect:

```bash
codex app-server daemon version
pgrep -af 'codex.*app-server'
systemctl --user list-units --type=service --all --no-pager
```

Inspect relevant system services, process parent, command line, and cgroup if ownership remains unclear. Daemon-manager state does not prove that every app-server belongs to that manager.

## Update from an independent session

If the update cannot terminate the task, run `codex update` and wait. For an intended standalone installation only, use the installer once if self-update fails or is unsupported:

```bash
set -o pipefail
curl -fsSL https://chatgpt.com/codex/install.sh | CODEX_NON_INTERACTIVE=1 sh
```

Do not silently migrate npm or externally packaged installs. Refresh command resolution with `hash -r`, repeat executable/version checks, and verify auth and diagnostics.

When the Codex-managed daemon is also in maintenance scope:

```bash
codex app-server daemon update
codex app-server daemon version
```

This may interrupt work. `--from-cli` copies and pins the invoking CLI package, changing lifecycle semantics. Check the target version's implementation/documentation before combining `--yes` with `--from-cli`; help text may not reveal all flag restrictions. Prefer the ordinary command for ordinary release updates.

## Autonomous self-maintenance

When updating the executing installation or daemon could disconnect the task, prepare a payload outside its process lifetime before any mutation. Include a brief handoff delay, before/after evidence, sequential update/fallback, scoped daemon maintenance, and a success marker after all required checks.

This example is for a verified standalone CLI-only installation under `~/.local/bin`. Adapt PATH to actual resolution. For a verified Codex-managed deployment in scope, insert the daemon update before final checks and its version check before the success marker.

```bash
#!/bin/bash
set -euo pipefail
sleep 5
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
command -v codex
readlink -f "$(command -v codex)"
codex --version
if ! codex update; then
  curl -fsSL https://chatgpt.com/codex/install.sh | CODEX_NON_INTERACTIVE=1 sh
fi
hash -r
# Managed deployments in scope: codex app-server daemon update
command -v codex
readlink -f "$(command -v codex)"
codex --version
codex login status
codex doctor --summary
# Managed deployments in scope: codex app-server daemon version
printf 'CODEX_MAINTENANCE_OK\n'
```

Save the adapted payload to an absolute path such as `${CODEX_HOME:-$HOME/.codex}/codex-maintenance.sh`. Preserve the inspected user's environment, non-default CODEX_HOME, and any required installation-specific variables. Check syntax with `bash -n`. Do not replace a payload while an earlier job uses it or run it synchronously inside the process it might terminate.

### Preferred supervisor

```bash
systemctl --user is-system-running
loginctl show-user "$(id -un)" -p Linger
```

A degraded but reachable manager may still accept services. If the job must survive the last logout, establish user-manager persistence or choose another host supervisor. Enable linger only when persistent user services are authorized; linger does not create a Codex boot service.

With the prepared payload:

```bash
maintenance_home=${CODEX_HOME:-$HOME/.codex}
maintenance_script="$maintenance_home/codex-maintenance.sh"
systemd-run --user \
  --unit=codex-maintenance \
  --collect \
  --description="Codex autonomous maintenance" \
  --setenv=HOME="$HOME" \
  --setenv=CODEX_HOME="$maintenance_home" \
  --setenv=PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin" \
  --working-directory="$HOME" \
  /bin/bash "$maintenance_script"
```

Inspect an existing unit instead of renaming to bypass its concurrency protection. Confirm launch acceptance promptly and record the result channel before the delay expires:

```bash
systemctl --user status codex-maintenance --no-pager
journalctl --user -u codex-maintenance -n 200 --no-pager
```

If disconnected, use an independent connection to inspect the result afterward. A completed `--collect` unit may be unloaded. Read journal output for the current invocation, not an old success marker; retention is host-dependent. Verify final state before claiming completion.

### Detached fallback

Use only when a suitable manager is unavailable and no maintenance job is active:

```bash
maintenance_home=${CODEX_HOME:-$HOME/.codex}
maintenance_script="$maintenance_home/codex-maintenance.sh"
maintenance_log="$maintenance_home/codex-maintenance.log"
setsid -f nohup /bin/bash "$maintenance_script" \
  </dev/null >"$maintenance_log" 2>&1
```

Confirm actual startup through process state and fresh log output. Reuse this single log path. `nohup` alone does not establish a new session; even this combination may be terminated by cgroup/container policy or shutdown. If no suitable supervisor or detached process is available, use a separate SSH maintenance session. Request manual intervention only when available tools cannot establish one.

## Recovery

- For verified managed remote control, restart with `codex remote-control stop` and `start` when needed, then verify daemon state and diagnostics.
- Restart external supervisors through their owning service. Stop a manually started instance deliberately before replacing it. Avoid broad PID kills or unsolicited lifecycle migration.
- After reboot, inspect actual state. If intended managed remote access is stopped, run `codex remote-control start`, then verify. Installation or a detached updater does not guarantee boot persistence.
- Downloaded releases, selected CLI, managed package, and running process may differ; investigate rather than inferring success from a directory.
- Automatic daemon-update timing and eligibility are version-specific. Do not rely on historical polling schedules to complete an immediate update.

## Sources

- User-supplied installation v4 document: ownership and independent handoff design.
- [Official commands](https://learn.chatgpt.com/docs/developer-commands)
- [Installer](https://learn.chatgpt.com/docs/codex/cli)
- [Environment](https://learn.chatgpt.com/docs/config-file/environment-variables)
- Target CLI help/implementation and installed `systemd-run(1)`, `systemctl(1)`, `loginctl(1)` manuals for version-specific behavior.
