# RouterOS Automation

Use configured SSH for existing devices unless the task needs a different transport. Choose a read or mutation by the exact RouterOS command. For bulk reads, request narrowly scoped fields and filter device output before logging it.

## Scripting and scheduled jobs

- Use full menu paths and explicit property names in saved code. Keep dependent local variables in the same block. Give variables distinctive names so RouterOS properties such as `name` and `type` do not shadow them. Inspect actual types before comparing addresses, time values and strings.
- Check the number and state of rows returned by `find`. Treat internal IDs as handles obtained from current state. For retryable jobs, read before adding or changing an object and make repeated runs converge on the requested state. If runs can overlap, check the script's active jobs and use a suitable single-instance guard.
- Use `print as-value` for structured records. Where available use `:serialize` for structured output across SSH. Restrict fields with `proplist` in menus that support it. Make sure the local shell passes RouterOS variables literally.
- Confirm the invoking identity, policies and event-supplied variables for Scheduler, Netwatch or DHCP lease scripts. Read `/system script job print`, scheduler state and filtered logs when investigating failures. Guard retries against partial application and keep errors visible. Keep permissions scoped to the action and avoid `dont-require-permissions` as a shortcut.
- For an authorized file-based syntax check, use a unique ordinary `.rsc` filename and the target's supported `verbose=yes dry-run` form. Upload and cleanup still write files on the router. See the [change workflow](changes.md) for import and rollback.

[Scripting](https://manual.mikrotik.com/docs/developer-guides/scripting/) · [Scripting tips](https://manual.mikrotik.com/docs/developer-guides/scripting/scripting-tips-and-tricks/) · [Scheduler](https://manual.mikrotik.com/docs/system-information-and-utilities/scheduler/).

## RouterOS API and REST

- When API access is already provisioned, verify the host and choose the configured transport. For a newly authorized REST integration, use trusted HTTPS on the management network or VPN and a dedicated least-privilege account. Current RouterOS REST reads use `read,api,rest-api`; check target support and restrict source access. Review the web service and input firewall as part of provisioning. Binary `api-ssl` is a separate service.
- REST reads use `GET /rest/<menu>` with `.proplist` to limit output. Normalize string values explicitly, including string booleans. REST `POST` can execute console commands, so inspect the endpoint and arguments when judging side effects. For the binary API, inspect error replies as well as terminal replies and use API query words for filtering.
- Bound calls and keep reads small. The current manual describes a 60-second REST limit and per-user serialization. On timeout or a lost response to a write, re-read before retrying because the router may already have applied the change. Use the same access and rollback discipline as with SSH.

[REST API](https://manual.mikrotik.com/docs/developer-guides/rest-api/) · [Binary API](https://manual.mikrotik.com/docs/developer-guides/api/).
