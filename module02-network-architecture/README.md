# Module 02 — Network Architecture

`Status: In progress`

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
| LAB 06 — Inter-VLAN Routing | Trunking, router-on-a-stick, one subnet and gateway per VLAN | ⬜ Planned |

---

## Key takeaways

- **A VLAN separates by configuration, not by cabling.** The same switch, cables and IP subnet; only the VLAN assignment changed, and PCs in different VLANs stopped reaching each other.
- **Physical and logical topology can disagree.** "Same switch" does not mean "can talk". An investigator has to check both layers.
- **Crossing VLANs requires a router** (or layer-3 switch), with one subnet and gateway per VLAN.
- **The MAC address table maps MAC → port → VLAN,** and it is volatile: entries age out after about 5 minutes of silence.
