# Inventory and Topology

Start with the devices named in the request. Resolve `all`, tags, or a role such as "the router serving VLAN X" using configured targets and current network evidence. When two candidates remain and it affects a decision, identify what evidence is missing before any write.

## Discover what is reachable

1. On first contact collect identity, board, RouterOS version and installed packages. For a health or inventory request add uptime, clock, resource usage, interfaces and recent relevant log events. Separate a configured alias or advertised neighbor from a successful management read.
2. When reconstructing topology, collect addresses, active routes and immediate gateways, bridge/port/VLAN tables and interface state. Add L2 discovery (`/ip neighbor print detail` plus discovery settings), bridge host/MAC entries and wireless registrations where available. Infer WAN, gateway, AP, switch or tunnel roles from this evidence, not model hints or default interface names. Check IPv6 if relevant to the deployed path.
3. For client identification correlate current bound DHCP address, MAC and hostname with ARP and the bridge host table or wireless registration. A lease can outlive a connection. A learned MAC behind a trunk or downstream switch identifies direction, not a direct cable. Distinguish device label from identity when MAC randomization or duplicate hostnames make the match uncertain.
4. For each claimed link or attachment record endpoints, interface/VLAN, evidence, timestamp or last-seen age, and confidence (`observed`, `inferred`, `unknown`). Distinguish logical adjacency from physical cabling. A missing LLDP/MNDP/CDP entry can reflect discovery scope or filtering. Verify the link from both ends where possible. A compact table or text path is sufficient.

For a missing device, check discovery scope, VLAN forwarding and known MAC evidence before concluding that the device is offline. If available, check its authorized management path from the relevant segment. Mark its physical location unknown until independently confirmed. [Neighbor discovery](https://manual.mikrotik.com/docs/system-information-and-utilities/neighbor-discovery/) and [bridge behavior](https://manual.mikrotik.com/docs/bridging-and-switching/).

## Snapshots and history

When requested, save scoped Markdown or JSON observations in user-owned storage outside the skill. Record collection time and timezone, device alias, observed identity/model/version, source and relevant state. Store configuration and runtime observations separately. For a comparison, locate the actual earlier snapshot and compare stable fields, ignoring transient IDs and preserving semantically important order, such as firewall rules. A current snapshot can establish a baseline when an earlier one is unavailable. Keep raw exports and sensitive logs private. [Backup and restore](changes.md#backup-and-restore).
