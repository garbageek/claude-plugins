# Setup and normal operation

Verify CLI command availability and actual behavior on the target Ubuntu host; documented interfaces do not establish that a particular installation is working.

## Install

For a new host, install missing dependencies under appropriate administrative authority:

```bash
sudo apt-get update
sudo apt-get install -y curl ca-certificates git
```

Run the official standalone installer as the intended regular user:

```bash
install_script=$(mktemp)
if curl -fsSL https://chatgpt.com/codex/install.sh -o "$install_script"; then
  sh "$install_script"
  install_result=$?
else
  install_result=1
fi
rm -f "$install_script"
if [ "$install_result" -ne 0 ]; then
  printf 'Codex installation failed\n' >&2
else
  export PATH="$HOME/.local/bin:$PATH"
  command -v codex
  readlink -f "$(command -v codex)"
  codex --version
fi
```

Proceed only after successful installation and executable verification. Typical paths are `~/.local/bin/codex` and `${CODEX_HOME:-$HOME/.codex}/packages/standalone`; inspect actual paths. The export affects the current shell; inspect installer profile changes if later sessions cannot find Codex.

Retain existing npm installations unless migration is requested. `npm install -g @openai/codex` is a valid alternative when intended; do not introduce Node.js solely for standalone installation.

## Authenticate

Check `codex login status` first. For headless ChatGPT login, run `codex login --device-auth`. Give the user the live verification URL and code when their participation is required; keep the login flow available and verify status afterward.

If API-key authentication is explicitly chosen and the key already exists in the target environment:

```bash
printenv OPENAI_API_KEY | codex login --with-api-key
codex login status
```

Do not print the key or embed it in generated commands. API usage has separate billing; preserve the user's choice.

## Normal operation

Run `codex doctor --summary` if supported. For repository work, enter the actual repository root, inspect `git status --short --branch`, then use `codex` interactively or `codex exec` for a one-shot task.

If an end-to-end model check is requested or needed to diagnose runtime failure:

```bash
codex exec 'Inspect this repository and summarize its purpose. Do not modify any files.'
```

Login status or diagnostics alone do not prove model execution. Do not launch a nested interactive agent solely to finish installation.

## Requested managed remote control

Ordinary SSH work does not require it. Check command availability and existing process ownership first; consult maintenance.md when ownership is unclear.

```bash
codex remote-control start
codex app-server daemon version
codex doctor --summary
```

Create a code only when needed with `codex remote-control pair`, optionally `--json` if supported. `stop` stops the managed daemon. Bare `codex remote-control` runs in the foreground; use `start` for background operation. Do not substitute a raw app-server listener.

Background operation does not establish boot persistence. A boot service is a separately requested host-management change.

## Official sources

- [CLI installation](https://learn.chatgpt.com/docs/codex/cli)
- [Commands and remote control](https://learn.chatgpt.com/docs/developer-commands)
- [Installer environment](https://learn.chatgpt.com/docs/config-file/environment-variables)
