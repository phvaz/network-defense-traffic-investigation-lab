# Module 02 — Network Architecture

`Status: Complete`

## Objective

Build the corporate topology (four VLANs: Administration, Employees, Servers, Guests) and understand how segmentation shapes security.

## Scope

LAN and WAN · switches · routers · VLANs · trunking · inter-VLAN routing · DHCP · NAT · ACLs · segmentation.

**Main tool:** Cisco Packet Tracer (time-boxed to about 3 hours. Most hands-on work happens in Linux VMs.)

---

## Labs

| Lab | Topic | Status |
|---|---|---|
| [**LAB 05 — VLANs: Segmenting One Switch**](lab05-vlans/) | Switch vs router, VLANs, access ports, before/after isolation test, MAC address table as volatile evidence | ✅ Complete |
| [**LAB 06 — Inter-VLAN Routing (Router-on-a-Stick)**](lab06-inter-vlan-routing/) | Trunking, 802.1Q subinterfaces, one subnet and gateway per VLAN, routed path verified by ping, tracert and TTL | ✅ Complete |
| [**LAB 07 — ACLs: Filtering Traffic Between VLANs**](lab07-acl/) | Extended ACL, implicit deny, placement near source, stateless side effects, ICMP unreachable vs timeout, hit counters as evidence | ✅ Complete |
| [**LAB 08 — Servers and Guests VLANs**](lab08-servers-guests/) | VLANs 30/40, four-segment design complete, guest-to-admin segmentation gap found and closed with a summarised guest ACL, `no ip domain-lookup` | ✅ Complete |
| [**LAB 09 — DHCP: Automatic Addressing per VLAN**](lab09-dhcp/) | Router as DHCP server, one pool per client VLAN, static server, DHCP vs guest ACL, binding table used to correct earlier documentation | ✅ Complete |
| [**LAB 10 — NAT: Sharing One Public Address**](lab10-nat/) | Simulated ISP, default route, private addresses vs the internet (before/after), NAT overload (PAT), translation table as attribution evidence | ✅ Complete |

---

## Key takeaways

- **A VLAN separates by configuration, not by cabling.** The same switch, cables and IP subnet; only the VLAN assignment changed, and PCs in different VLANs stopped reaching each other.
- **Physical and logical topology can disagree.** "Same switch" does not mean "can talk". An investigator has to check both layers.
- **Crossing VLANs requires a router** (or layer-3 switch), with one subnet and gateway per VLAN.
- **The MAC address table maps MAC → port → VLAN,** and it is volatile: entries age out after about 5 minutes of silence.
- **A trunk carries several VLANs over one cable** by tagging each frame (802.1Q). It is a port mode, not a special cable.
- **Router-on-a-stick:** one router port split into subinterfaces, one per VLAN, each holding that VLAN's gateway.
- **TTL 128 → 127 reveals one routed hop,** readable from any captured packet without running a trace.
- **Routing without filtering undoes segmentation.** The router is the choke point where ACLs belong.
- **An ACL is read top to bottom and ends with an invisible deny.** Forgetting the final permit isolates the whole segment.
- **Router ACLs are stateless.** Blocking FUNC → ADMIN also dropped the replies to ADMIN-initiated pings.
- **An ICMP unreachable points to where traffic was blocked; a timeout does not.** The notice goes to the sender of the dropped packet.
- **ACL hit counters corroborate what was attempted,** and are volatile like the MAC table.
- **Every new segment needs its own policy.** Adding the guest VLAN without an ACL gave guests the same reach as employees.
- **A summarised deny (`192.168.0.0/16`) protects future internal VLANs automatically.**
- **The DHCP binding table maps IP → MAC at a point in time.** Joined with the switch MAC table it leads from an IP in an alert to a switch port.
- **Documentation is a claim, not evidence.** Cross-checking three sources showed two PCs had been documented on swapped ports since LAB 05.
- **Private addresses cannot get replies from the internet.** NAT on the edge router swaps them for the one public address, and every inside host shares it (PAT).
- **The NAT translation table is the only link from a public IP and port back to an internal host,** and it is the most volatile table in the module. Attribution behind NAT needs logged translations with exact port and time.
