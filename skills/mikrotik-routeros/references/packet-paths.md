# Packet Paths

Trace one flow at a time. Record address family, source address/port, destination address/port, protocol, ingress and time. Use [inventory and topology](discovery.md) to resolve each hop. Label what rules predict, what counters or probes confirm, and what has yet to be seen beyond the router.

## Port forwarding and firewall

1. Confirm the public destination is on the intended WAN or forwarded by an upstream device. Check whether the test originates outside the LAN or needs hairpin NAT. Identify the actual ingress interface and its list membership.
2. For a new CPU-routed IPv4 flow, follow raw and connection tracking, prerouting mangle and dstnat, routing decision, forward filters and postrouting/srcnat where applicable. Router-destined traffic uses input. Router-originated traffic uses output. For bridged traffic check the bridge path and offload first.
3. Inspect only the relevant ordered rules in `/ip firewall raw`, `mangle`, `nat` and `filter`, including jumps, address lists, disabled flags and `print stats` where supported. Inspect pertinent `/ip firewall connection` entries, original/reply tuples and translation. A NAT rule's match counter does not prove delivery. Existing flows can retain their translation.
4. Verify server ownership and the expected response from the required client path. For UDP, use a known non-mutating, bounded application query when permitted. If such a query is not available, observe existing traffic and mark application delivery unverified. Correlate a new connection and counter deltas. Check the destination host's listener, local firewall and route back when accessible. Without a verified server/client result, report how far the evidence reaches.

[Packet flow](https://manual.mikrotik.com/docs/firewall-and-quality-of-service/packet-flow-in-routeros/) · [Connection tracking](https://manual.mikrotik.com/docs/firewall-and-quality-of-service/connection-tracking/).

## Multi-WAN or asymmetric routing

Read the active route and immediate gateway in the table the packet actually uses. On v7 inspect `/routing table print`, `/routing rule print detail` and the matching routing/connection marks in mangle. Check whether the chosen table can resolve the gateway. Inspect the router's own return path separately from forwarded packets. Where applicable, check route rules, reverse-path checks, NAT bindings and policy routing on the downstream host. FastTrack uses the main table, so confirm whether the affected flow is eligible. Probe from the affected source/table, verify egress on the correct WAN and confirm the return/application result before declaring resolution. [Routing decision](https://manual.mikrotik.com/docs/user-guides/routing-and-networking-protocols/routing-decision/).

## VLAN cannot reach the gateway

1. Start at the client's learned MAC and access port. Walk `/interface bridge port print detail` and `/interface bridge vlan print` on each hop. Check PVID, allowed frame types, ingress filtering, actual tagged/untagged membership and STP/RSTP forwarding state.
2. At the gateway confirm the VLAN can reach the CPU if required, the VLAN interface binds to the intended parent, and the router has the expected address and connected route. For DHCP check server binding, subnet options and broadcast reachability.
3. Check the detected switch chip before interpreting hardware offload. Software forwarding and offload are distinct outcomes. Confirm the relevant bridge port flags and traffic path. Verify client lease or static addressing, ARP and a bounded probe to the gateway from that VLAN. For isolation changes verify the intended blocked path too.

The RB760iGS hEX S uses MT7621 for its Ethernet ports, which can offload compatible bridge VLAN filtering on RouterOS v7. The hAP ax3 uses IPQ-PPE, for which the manual lists plain port switching and no hardware VLAN table. Compare the detected board and live flags before applying either expectation.

[Bridging and switching](https://manual.mikrotik.com/docs/bridging-and-switching/) · [Switch chip features](https://manual.mikrotik.com/docs/bridging-and-switching/switch-chip-features/).

## VPN and queues

- For WireGuard, use the handshake and inner-packet checks in [diagnostics](diagnostics.md#triage-by-symptom). For IPsec, compare active peers, installed SAs via selected nonsecret fields, policy selectors and the actual routed traffic. Verify bidirectional protected traffic across the expected tunnel before declaring success. [IPsec](https://manual.mikrotik.com/docs/virtual-private-networks/ipsec/).
- For a queue, inspect simple queue targets or tree parents, packet marks, configured rates and counters during matching traffic. Check FastTrack and hardware forwarding before treating flat counters as an empty link. Confirm behavior from the affected client and use an authorized load check only when necessary. [Queues](https://manual.mikrotik.com/docs/firewall-and-quality-of-service/queues/).
