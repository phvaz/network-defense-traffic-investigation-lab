# Module 01 — Networking Fundamentals

`Status: In progress`

## Objective

Understand how computers communicate on a network well enough to explain the path of a packet between two hosts and to identify the protocols involved, as the foundation for traffic analysis and investigation.

## Scope

OSI and TCP/IP models · IPv4 · private vs public addresses · subnetting, CIDR and masks · default gateway · MAC addresses · ARP · DHCP · DNS · TCP · UDP · ICMP · ports and protocols · encapsulation.

---

## Labs

| Lab | Topic | Status |
|---|---|---|
| [**LAB 01 — Understanding Network Communication**](lab01-network-communication/) | IP, MAC, mask, ARP, ICMP, and the first packet capture | ✅ Complete |
| [**LAB 02 — DNS Resolution and TCP Connections**](lab02-dns-and-tcp/) | Gateway, DNS over UDP, TCP handshake, HTTP, FIN vs RST | ✅ Complete |
| [**LAB 03 — Routing and the Path to the Internet**](lab03-routing-and-traceroute/) | Routing table, traceroute/TTL, ICMP Time Exceeded, double NAT, CGNAT | ✅ Complete |
| LAB 04 | Ports and active connections (`ss`, `netstat`) | ⬜ Planned |

---

## Key takeaways so far

- **A host decides "local or remote" using its subnet mask.** Local destinations are delivered directly; remote ones go to the gateway.
- **ARP comes before ICMP.** A host must resolve the destination MAC before any IP packet leaves on the LAN.
- **The ARP cache is volatile evidence** of which neighbours a host contacted recently (RFC 3227, order of volatility).
- **A MAC belongs to the NIC and an IP belongs to the network.** The same NIC kept its MAC and changed its IP when moved between networks.
- **Traffic leaving the LAN goes to the gateway.** Destination IP = final recipient; destination MAC = next hop (the gateway).
- **DNS comes before every connection,** which makes DNS records one of the earliest indicators of C2 activity.
- **Middleboxes can answer on someone else's behalf.** The VirtualBox NAT hid the real path from traceroute and rewrote the TTL; the real path (9 hops) was only visible from the host.
- **Absence in a capture is not absence of the event.** An incomplete capture was caught by cross-checking against the `tracert` output.
- **A packet's source address is a claim, not proof.** A TCP `RST` "from" a remote server was *consistent with* local generation by the NAT, based on timing.
