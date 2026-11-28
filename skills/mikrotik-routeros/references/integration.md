# Management Tools

## Choose a working transport

1. Discover available tools and prefer a configured RouterOS MCP with authorized access and a verified SSH trust configuration. Inspect schemas before calling tools. On WireSage MCP, `list_devices` takes no device argument and lists configured titles and tags. Pass the exact title in `device` on subsequent calls and confirm identity with device reads. Inventory output alone requires no router connection.
2. Use the existing permitted SSH path for unavailable operations or when MCP is absent or fails the trust requirement. Use a known alias and verify the pinned host key. [Bounded SSH reads](diagnostics.md).
3. Use an already provisioned trusted HTTPS REST endpoint only when the host can reach it and supports the needed command. REST requests do not hold a persistent Safe Mode session. [REST workflow](automation.md#routeros-api-and-rest).
4. When no path is configured or reachable, report the exact blocker and give offline guidance where applicable. A cloud session needs its own reachable connector. A `stdio` process on another machine is local to its host.

## WireSage capabilities

This table describes the reviewed upstream source, not a guarantee about an installed release. Compare it with the active tool catalog and device permissions. Evaluate actual side effects even when a tool is labeled read-only. For example, a Wi-Fi scan can disconnect stations. Treat login failure, command error and genuinely empty output as different outcomes.

| Need | Found in the reviewed MCP | Inspect through SSH if fields or tools are missing |
| --- | --- | --- |
| Inventory, identity and resources | `list_devices`, `get_system_resource`, `get_system_routerboard`, `get_system_clock`, `list_system_packages`, `list_interfaces`, `get_logs` | `/system identity print`, full port counters, Ethernet/SFP monitors |
| Topology and DHCP | `list_arp_entries`, `list_dhcp_servers`, `list_dhcp_leases`, `list_bridge_ports`, `list_bridge_vlans` | L2 discovery, bridge host table, RSTP state, reservation writes |
| Packet path | `list_routes`, `get_routing_table`, `list_filter_rules`, `list_raw_rules`, `list_nat_rules`; targeted rule updates where supported | Policy rules, mangle, conntrack and missing counters |
| Wi-Fi, DNS, VPN, queues | `get_wireless_registration_table`, `get_dns_settings`, `list_wireguard_peers`, selected IPsec reads, queue tools | Driver-specific radio fields, LTE, IPsec configuration, omitted peer counters |
| Probes | `ping` with `address`, bounded `count` and optional `device`; `traceroute`; bounded `torch` and `sniff_packets` on reviewed source | Missing probe options, authorized persistent captures and client-side tests |
| Recoverable writes | `enable_safe_mode`, `safe_mode_status`, `commit_safe_mode`, `rollback_safe_mode`, each with optional `device` | Router-side confirmation or an interactive guarded SSH session |

Safe Mode tools hold an interactive shell per device in the MCP process. Use one backend instance and explicit title throughout. In the reviewed implementation `safe_mode_status` reads a process flag. Rollback closes the shell and commit interprets its response. Neither result establishes actual router state. Confirm router ownership/history when possible and re-read configuration and access after commit or rollback. On disconnect or server restart, stop writes, reconnect and verify state before continuing. [WireSage source at 13c7a2c](https://github.com/wiresage/mikrotik-mcp/tree/13c7a2c326fffc70ca195a8aa32cf6dd25aad722) · [Coverage](https://github.com/wiresage/mikrotik-mcp/blob/13c7a2c326fffc70ca195a8aa32cf6dd25aad722/docs/api-coverage.md).

## Optional setup

- Keep [operator metadata](../assets/network.example.yaml) separate from the [WireSage inventory example](../assets/mikrotik-mcp.inventory.example.yaml). Use the latter as a starting point for the actual YAML list passed via `MIKROTIK_INVENTORY_FILE`. Store it outside the skill with mode 0600. Use a reachable management hostname/IP, an existing authorized account and a key path on the machine running the server. OpenSSH alias configuration is separate.
- Before enabling this backend with real credentials, review host verification on the chosen release. The reviewed source creates a Paramiko client with `AutoAddPolicy()` and does not load host keys in `connect()`. Prefer the existing pinned SSH path until the backend provides equivalent verification. [SSH client source](https://github.com/wiresage/mikrotik-mcp/blob/13c7a2c326fffc70ca195a8aa32cf6dd25aad722/src/mcp_mikrotik/mikrotik_ssh_client.py).
- For an approved installation, use the upstream `mcp-server-mikrotik` stdio package with a reviewed version. In Codex the registration form is `codex mcp add --env MIKROTIK_INVENTORY_FILE=/absolute/path/inventory.yaml mikrotik -- uvx mcp-server-mikrotik@VERSION`. In Claude Code use `claude mcp add --transport stdio mikrotik --env MIKROTIK_INVENTORY_FILE=/absolute/path/inventory.yaml -- uvx mcp-server-mikrotik@VERSION`. Replace `VERSION` with the reviewed release and choose host scope as needed. After configuration, inspect the loaded catalog and run inventory and a bounded identity/resource read before using write tools. [Upstream installation](https://www.mikrotik-mcp.com/docs/).

