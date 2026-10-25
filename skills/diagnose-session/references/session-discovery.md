# Session discovery

Resolve the session the user named, establish what its records mean, and record both in the case file. Host facts below were checked against the cited sources on 2026-10-25. They are starting points: confirm every location and record meaning against the files actually present, because formats and paths change between versions.

## Method

1. **Use what is supplied.** A usable absolute path, session id, or export does not need another search. Otherwise use the host's exposed session tools, configured storage, local help, or bounded filesystem inspection.
2. **Expand paths.** Resolve `~`, environment variables, and configured overrides to full absolute paths. Use the same path in the case file and in the reply.
3. **Confirm identity.** Match the session id, working directory, timestamps, and conversation content. Quote the first human prompt and first timestamp. Recency alone is not confirmation. Separate the requested session from its subagents, forks, resumed copies, and unrelated candidates; record rejected candidates with the reason.
4. **Establish record meanings from observed records.** Determine which records are human messages, injected context (hooks, reminders, skill bodies, parent dispatches), assistant messages, tool calls, and tool results, and how calls match results. Determine whether usage counters are per-message, per-turn, or cumulative, and their units, before calculating anything. Identify compaction, resume, and subagent-link records. Do not carry a format over from another host or version, and do not turn a missing field into zero.
5. **Record it.** Write sources, extraction commands, identity evidence, associated sessions, record meanings with supporting line numbers, and unresolved gaps into the case file. If history is missing, deleted, or ambiguous, state the specific limit and ask for the path, an export, or an identifying detail.

## Claude Code

Sources: [Manage sessions](https://code.claude.com/docs/en/sessions), [Explore the .claude directory](https://code.claude.com/docs/en/claude-directory).

- Transcripts are JSONL at `~/.claude/projects/<project>/<session-id>.jsonl`. `<project>` is the working directory path with non-alphanumeric characters replaced by `-`; names longer than 200 characters are truncated and suffixed with a hash of the full path.
- `CLAUDE_CONFIG_DIR` moves storage away from `~/.claude`; `CLAUDE_CODE_PROJECT_DIR_NAME` sets the `<project>` name. Check both before concluding a transcript is absent.
- Subagent transcripts are under `projects/<project>/<session-id>/subagents/`. Large tool outputs spill to `projects/<project>/<session-id>/tool-results/`. Earlier transcripts set aside for the same session carry `.orphaned-` or `.superseded-` markers in their names and do not appear in the session picker.
- Transcripts older than `cleanupPeriodDays` (default 30) are deleted; Claude Desktop and Cowork transcripts follow their own rule. A missing old session may have been swept.
- The docs state that the entry format is internal and changes between versions, and that `/export` is the supported interface for building on session data. Establish record meanings from the actual file every time.
- The docs state that transcripts are plaintext and include anything that passed through a tool, including file contents and command output.

## Codex

Sources: [Environment variables](https://developers.openai.com/codex/environment-variables), [Advanced configuration](https://developers.openai.com/codex/config-advanced), and the `codex-rs/rollout` crate on the `main` branch of [openai/codex](https://github.com/openai/codex/tree/main/codex-rs/rollout/src). Source-derived facts describe current `main`; an installed release may differ.

- Documented: `CODEX_HOME` defaults to `~/.codex` and is the root for state including sessions. The docs also describe `history.jsonl` under `CODEX_HOME` as local history; treat it as a separate source from per-session rollouts.
- Source: per-session rollouts are written to `$CODEX_HOME/sessions/YYYY/MM/DD/rollout-<timestamp>-<thread-id>.jsonl`. Archived sessions use `$CODEX_HOME/archived_sessions`.
- Source: a background job compresses rollouts older than about seven days to `.jsonl.zst`, and a plain `.jsonl` takes precedence over a compressed sibling. Read compressed files as a stream (`zstd -dc "$F" | ...`); never decompress in place. Line numbers then refer to the decompressed stream; record that in the case file.
- Source: session metadata can name a parent or forked-from thread, which links associated sessions. Token-count events carry both a running total (`total_token_usage`) and the most recent usage (`last_token_usage`). Confirm both against the observed records before using them.

## Other hosts

Use the host's own documentation, session tools, or export. When no history is reachable, report that and ask for an export.
