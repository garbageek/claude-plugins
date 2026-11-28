# MikroTik RouterOS CLI Cheat Sheet

Portable edition of the RouterOS command reference. Commands use root-relative
RouterOS menus; shell commands are marked separately. Examples use illustrative
names and addresses. Confirm the actual device, version, installed package and
objects before using an example. The baseline is RouterOS v7; v6 differences
are called out where relevant. Use terminal completion and the
[versioned MikroTik CLI reference](https://manual.mikrotik.com/docs/cli-reference/)
for options not listed here.

## CLI and management

| Need | Command or action |
| --- | --- |
| Navigate | `/` returns to root; `..` goes up. Use `Tab` for completion and terminal help on the target. |
| Select entries | `print detail`, `print terse`, `print count-only`, `print where disabled=no`, `print where name="bridge"`. The `~` operator matches a regular expression. |
| Use a selector | `/interface print detail where name="ether1"` before using `[find where name="ether1"]` for a change. Verify matches and expected count; printed item numbers are session-local and can shift. |
| Inspect daemon exposure | `/ip service print detail`, `/user print`, `/user group print`, `/tool mac-server print`, `/tool mac-server mac-winbox print`. Verify listening services against firewall rules and the allowed source network. |
| Identify the device | `/system identity print`, `/system resource print`, `/system routerboard print`, `/system package print`. |
| Check time and CPU | `/system clock print`, `/system ntp client print`, `/system resource cpu print`. `/tool profile` is interactive; bound it separately. |
| Check recent changes | `/system history print`, `/log print without-paging where topics~"dhcp"`. Narrow log output and avoid disclosing command arguments or logs containing secrets. |

For a bounded read on a Linux management host:

```bash
timeout 15s ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=5 router-alias '/system identity print; /system resource print'
```

Use a configured alias/key and an independently verified host key. For a
guarded configuration change use a persistent interactive TTY. Toggle Safe
Mode with `Ctrl+X` or `F4` and verify the `<SAFE>` prompt; `Ctrl+D` ends the
session and undoes pending Safe Mode changes. `/quit` does not undo them.
Check history and the actual outcome after a disconnect. A scheduled reboot
does not undo saved configuration. See [changes and recovery](changes.md) for
rollback sequencing and [console help](https://manual.mikrotik.com/docs/management-tools/console/).

## Interfaces, layer 2 and addressing

```routeros
/interface print detail
/interface print stats-detail
/interface ethernet monitor ether1 once
/interface ethernet print stats
/interface bridge print detail
/interface bridge monitor bridge once
/interface bridge port print detail
/interface bridge vlan print detail
/interface bridge host print where bridge=bridge
/interface vlan print detail
/interface list print
/interface list member print
/ip neighbor discovery-settings print
/ip neighbor print detail
/ip address print detail
/ip arp print where address=192.0.2.10
/ipv6 address print detail
/ipv6 neighbor print
```

Compare actual link rate/duplex and error deltas. For VLANs compare PVID,
configured and current tagged/untagged membership, CPU/bridge port membership
and the active hardware-offload flag. LLDP/MNDP rows alone do not prove a cable
path. See [packet paths](packet-paths.md) and [device discovery](discovery.md).

## DHCP, DNS and routing

```routeros
/ip dhcp-client print detail
/ip pool print
/ip dhcp-server print detail
/ip dhcp-server network print detail
/ip dhcp-server lease print where mac-address=02:00:00:00:00:01
/ip dhcp-server lease print where host-name~"client"
/ip dns print
/ip dns static print
:put [:resolve "example.com"]
/ip route print detail where active
/ip route print detail where dst-address="0.0.0.0/0"
/routing table print
/routing rule print detail
/ipv6 route print detail
/ipv6 nd print detail
```

`/routing table` and `/routing rule` are v7 menus; v6 places routing rules
under `/ip route rule` and uses routing marks in the route configuration.
Check the DHCP owner, subnet, pool and effective client settings before
changing DNS or gateways. Multiple DNS servers in DHCP are not a guarantee
of ordered failover; query the advertised addresses separately for a local
and a public name. When testing LTE or another uplink, verify probe egress
and client-forwarded traffic independently.
[DHCP Server](https://manual.mikrotik.com/docs/network-management/dhcp/server/).

## Firewall, NAT, queues and VPN

```routeros
/ip firewall filter print stats
/ip firewall nat print detail
/ip firewall nat print stats where chain=dstnat
/ip firewall mangle print stats
/ip firewall raw print stats
/ip firewall connection tracking print
/ip firewall connection print where src-address~"^192[.]0[.]2[.]10(:|\$)"
/queue simple print stats
/queue tree print stats
/interface wireguard peers print proplist=interface,last-handshake,rx,tx
/ip ipsec active-peers print
```

WireGuard is a v7 feature. If the target lacks CLI `proplist`, select the
required properties with a supported read rather than dumping full objects.
Request only needed fields when inspecting
security objects; do not return private keys or preshared keys. Use the
correct input, forward or output chain, and inspect rule ordering and
interface lists. NAT is decided for a new tracked connection; a pre-existing
connection may not demonstrate a changed rule. FastTrack and hardware
offload affect counter visibility. Do not clear live counters or all tracked
connections during read-only diagnosis. Simple Queue rate pairs are
upload/download relative to the configured target.

## Wi-Fi, LTE and bounded diagnostics

```routeros
/interface wireless print
/interface wireless registration-table print stats
/interface wifi print
/interface wifi registration-table print detail
/interface lte print
/interface lte apn print
/interface lte monitor lte1 once
/interface monitor-traffic ether1 once
/ping 192.0.2.1 count=3
/tool traceroute 192.0.2.1
/tool netwatch print stats
/system logging print
/system scheduler print
/system script print where name="example-job"
```

Choose the Wi-Fi menu by installed driver/package; do not require both to
exist. Some older LTE packages use `info` instead of `monitor`. Redact
subscriber/modem identifiers, APN credentials and script source as needed.
Replace documentation IPs with the known endpoint for an actual probe.
Put its own time limit around traceroute. Compare receive/transmit byte
deltas over a known interval for bandwidth, and compare both ends of a
backhaul. Do not use Torch, packet capture, wireless scanning, or bandwidth
tests as the default read-only sample; see [diagnostics](diagnostics.md).

## Configuration examples

These are individual syntax patterns for **authorized** changes, not a
script to paste into a router. Validate unique objects, rule position and
recovery first. Verify the affected service from a separate client or path.

| Need | Example |
| --- | --- |
| Create a bridge and add a checked port | `/interface bridge add name=br-lan protocol-mode=rstp`, then `/interface bridge port add bridge=br-lan interface=ether3`. |
| Declare a VLAN interface | `/interface vlan add name=vlan20 vlan-id=20 interface=br-lan`. This does not configure bridge VLAN membership. |
| Assign an address | `/ip address add address=192.0.2.1/24 interface=vlan20`. First check collision and management consequences. |
| Convert a DHCP lease | `/ip dhcp-server lease make-static [find where server="lan-dhcp" and mac-address=02:00:00:00:00:01 and dynamic=yes]`. Confirm exactly one matching lease first. |
| Configure WAN DHCP | `/ip dhcp-client add interface=ether1 use-peer-dns=no add-default-route=yes disabled=yes`. Check for an existing client and route/DNS effects before enabling. |
| Add a static route | `/ip route add dst-address=198.51.100.0/24 gateway=192.0.2.254 disabled=yes`. Verify nexthop resolution and the intended table. |
| Add a local DNS record | `/ip dns static add name=host.example.test address=192.0.2.10`. Keep remote DNS service restricted to intended clients. |
| Stage masquerade | `/ip firewall nat add chain=srcnat out-interface-list=WAN action=masquerade disabled=yes comment="example-wan-nat"`. Confirm WAN membership and matching rule order before enabling. |
| Stage a destination NAT rule | `/ip firewall nat add chain=dstnat in-interface-list=WAN protocol=tcp dst-port=8080 action=dst-nat to-addresses=192.0.2.10 to-ports=80 disabled=yes comment="example-web-forward"`. Confirm the corresponding forward policy and the actual publication intent. |
| Stage a simple queue | `/queue simple add name=limit-client target=192.0.2.10/32 max-limit=5M/10M disabled=yes`. Check existing ordering and FastTrack. |

For a new gateway, verify wired/console access first. Stage bridge addressing,
interface lists and input/forward policy before exposing services or attaching
the WAN; then add the intended pool, DHCP network options, server and NAT as
required. Verify locally acquired leases and clients' real traffic. Do not
replace a working gateway with a generic skeleton. For scripts, permissions and
one-shot Scheduler/Netwatch behavior see [automation](automation.md).

## Export, backup and upgrades

| Need | Command or distinction |
| --- | --- |
| Inspect one section | `/ip dhcp-server export terse`. Export may still expose secrets in comments or scripts. Review before sharing. |
| Save text to router storage | `/export terse file=config-before-change` creates an `.rsc` file; `terse` emits full command paths. `compact` omits defaults; `verbose` includes them. |
| Include sensitive export fields | v7 supports `show-sensitive`; use only for an explicitly authorized protected recovery copy, never in shared output. On v6 inspect command help before exporting; do not assume the v7 defaults. |
| Inspect files | `/file print`. Use a unique filename, check size and verify the transferred copy before removing a temporary router file. |
| Check an import on supported v7 | `/import file-name=reviewed.rsc verbose=yes dry-run=yes`. This is a syntax/preview check; it does not demonstrate a working migration. Normal import executes commands. |
| Back up or restore | `/system backup save` and `/system backup load` are separate operations; supply an explicit protected backup password for encryption. Binary restore is disruptive, normally for the same device/version; text export is better for inspection or controlled migration. |
| Inspect upgrade state | `/system package update print`, `/system routerboard print`. RouterOS package installation and RouterBOOT upgrades are separate operations, with separate post-reboot verification. |

See [configuration management](https://manual.mikrotik.com/docs/getting-started/configuration-management/)
and the bundled [backup and recovery workflow](changes.md). Keep reset and
broad rule deletion out of a generic command batch.
