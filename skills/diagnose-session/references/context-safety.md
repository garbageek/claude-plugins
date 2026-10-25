# Context safety for session transcripts

One transcript record can exceed a megabyte or embed a whole earlier history. Printing one whole record can overflow the context of the session doing the diagnosis. Every reader, the controller and every analyst, follows these rules for every file.

1. **Measure before reading.**

   ```bash
   wc -lc "$F"
   awk 'length($0) > 100000 { print NR, length($0) }' "$F"   # oversized lines
   ```

   For a compressed transcript, measure the stream: `zstd -dc "$F" | wc -lc`.
2. **Locate first, then extract small fields.** Get line numbers and counts first (`grep -n PATTERN "$F" | cut -d: -f1`, `jq -r '.type' "$F" | sort | uniq -c`), then extract bounded fields from specific lines (`sed -n 'Np' "$F" | jq -c '{...}'`, or `| cut -c1-500`). Use the extraction commands recorded in the case file. Do not `cat` a transcript or print whole matching lines.
3. **Keep each result under 500 characters per record.** If a command returns more, tighten the field or the slice.
4. **Read-only.** Never modify, move, delete, or decompress a session file in place. Work on streams or on copies inside the diagnosis workspace.
5. **No secrets in output.** When an extracted field contains a credential or key, report its presence and location, not its value.
