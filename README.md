# Network Defense & Traffic Investigation Lab

**A hands-on lab building network knowledge for security investigation: from how two hosts talk on a LAN, to traffic analysis, reconnaissance, detection, and a simulated DFIR network investigation.**

`VirtualBox · Kali Linux · Windows 10` · `Wireshark · Nmap · Suricata` · `RFC 3227 · ISO/IEC 27037 · NIST SP 800-86 / 800-61` · `Status: In progress — Module 03 (Traffic Analysis) underway`

---

## Overview

This project builds and investigates a small corporate network in a controlled lab. The scenario: I have been engaged to assess the infrastructure of a small company that has an administrative network, an employee network, internal servers, a guest network, and an internet connection. The mission is to build that infrastructure, understand how it works, implement security controls, and then investigate suspicious activity on it.

The goal is **not** to become a network administrator. It is to understand networking well enough to **read network traffic, recognise abnormal behaviour, and investigate how an attack develops** inside a corporate environment, with the analyst mindset of DFIR.

Every lab follows the same discipline used in my forensic investigations:

- **Observed fact → technical interpretation → conclusion.** Findings carry exactly the strength the evidence permits ("consistent with", not "proves").
- **Evidence integrity.** Every packet capture is saved and SHA-256 hashed immediately, with a hash manifest so results can be verified independently.
- **Troubleshooting is documented, not hidden.** Failures, hypotheses, and how each one was verified are part of the record.

---

## Roadmap

| Module | Focus | Main tools | Status |
|---|---|---|---|
| [**00 — Lab Environment**](module00-lab-environment/) | VMs, VirtualBox network modes, isolation | VirtualBox | ✅ Complete |
| [**01 — Networking Fundamentals**](module01-networking-fundamentals/) | IPv4, subnetting, MAC, ARP, ICMP, DHCP, DNS, TCP/UDP | `ip`, `ipconfig`, Wireshark | ✅ Complete |
| [**02 — Network Architecture**](module02-network-architecture/) | VLANs, trunking, inter-VLAN routing, NAT, ACLs | Cisco Packet Tracer | ✅ Complete |
| [**03 — Traffic Analysis**](module03-traffic-analysis/) | PCAP analysis, TCP/TLS handshakes, DNS, HTTP, C2/exfiltration patterns | Wireshark | 🔄 In progress |
| [**04 — Network Reconnaissance**](module04-network-reconnaissance/) | Host discovery, port/service/OS detection, exposure mapping | Nmap | ⬜ Planned |
| [**05 — Network Defense**](module05-network-defense/) | Firewalling, IDS rules, alert triage, alert ↔ PCAP correlation | nftables/UFW, Suricata | ⬜ Planned |
| [**06 — DFIR Network Investigation**](module06-dfir-investigation/) | Simulated incident: timeline, IOCs, hypotheses, formal report | All of the above | ⬜ Planned |

---

## Target architecture

The corporate network to be built and investigated:

| Segment | VLAN | Hosts |
|---|---|---|
| Administration | 10 | Admin workstation |
| Employees | 20 | Two workstations |
| Servers | 30 | Ubuntu Server |
| Guests | 40 | Guest workstation |

With switching, routing, a firewall, IPv4 addressing, DHCP, DNS, NAT, ACLs, and traffic monitoring. The design is documented in Module 02.

---

## Completed labs

| Lab | What it demonstrates | Evidence |
|---|---|---|
| [**LAB 01 — Understanding Network Communication**](module01-networking-fundamentals/lab01-network-communication/) | ARP resolution before ICMP; broadcast vs unicast; ARP cache as volatile evidence; cross-source MAC correlation; TTL as an OS indicator; layer-2 troubleshooting with `ip neigh` | `lab01-arp-icmp.pcapng` (SHA-256 verified) |
| [**LAB 02 — DNS Resolution and TCP Connections**](module01-networking-fundamentals/lab02-dns-and-tcp/) | Gateway ARP vs remote destinations; DNS over UDP; TCP handshake, HTTP, FIN vs RST; capture/tool cross-correlation; why a source address is not proof of origin | `lab02-dns-sanitized.pcapng`, `lab02-tcp-sanitized.pcapng` (resolver address redacted, SHA-256 verified) |
| [**LAB 03 — Routing and the Path to the Internet**](module01-networking-fundamentals/lab03-routing-and-traceroute/) | Routing table and default route; traceroute via TTL expiry; how a NAT middlebox hid the real path; double NAT and CGNAT implications for attribution; detecting an incomplete capture | Captures retained privately (home network); SHA-256 recorded |
| [**LAB 04 — Ports and Active Connections**](module01-networking-fundamentals/lab04-ports-and-connections/) | Listening ports on Kali vs Windows; PID → program → service attribution; outbound connections and ephemeral ports; default services as attack surface | Socket-table screenshots |
| [**LAB 05 — VLANs: Segmenting One Switch**](module02-network-architecture/lab05-vlans/) | Switch vs router; one switch split into two VLANs; before/after ping test isolating a single variable; MAC address table as volatile evidence of port and segment | `lab05-vlans.pkt` (Packet Tracer project, SHA-256 verified) |
| [**LAB 06 — Inter-VLAN Routing (Router-on-a-Stick)**](module02-network-architecture/lab06-inter-vlan-routing/) | 802.1Q trunk and router subinterfaces; one subnet and gateway per VLAN; routed path confirmed by ping, tracert and TTL decrement (128 → 127) | `lab06-intervlan.pkt` (Packet Tracer project, SHA-256 verified) |
| [**LAB 07 — ACLs: Filtering Traffic Between VLANs**](module02-network-architecture/lab07-acl/) | Extended ACL blocking one VLAN from another; stateless side effect on replies; ICMP unreachable vs timeout; hit counters (8 matches) reconciled with tests | `lab07-acl.pkt` (Packet Tracer project, SHA-256 verified) |
| [**LAB 08 — Servers and Guests VLANs**](module02-network-architecture/lab08-servers-guests/) | Four-VLAN corporate design complete; guest-to-admin segmentation gap found by testing and closed with a guest ACL; counters reconciled with tests | `lab08-servers-guests.pkt` (Packet Tracer project, SHA-256 verified) |
| [**LAB 09 — DHCP: Automatic Addressing per VLAN**](module02-network-architecture/lab09-dhcp/) | Router-hosted DHCP per VLAN; why the guest ACL let DHCP through; binding table (IP → MAC) cross-checked with the LAB 05 MAC table, exposing and correcting a documentation error | `lab09-dhcp.pkt` (Packet Tracer project, SHA-256 verified) |
| [**LAB 10 — NAT: Sharing One Public Address**](module02-network-architecture/lab10-nat/) | Simulated ISP and internet server; before/after test showing private addresses cannot get replies; NAT overload (PAT); translation table as the volatile record linking a public address back to an internal host | `lab10-nat.pkt` (Packet Tracer project, SHA-256 verified) |
| [**LAB 11 — TCP in Depth: Handshakes, Retransmissions and Capture Integrity**](module03-traffic-analysis/lab11-tcp-in-depth/) | One click, two connections (favicon); cached 304; idle pre-connections with keep-alives; 10 % induced loss read as duplicate ACKs and 80 fast retransmissions; capture-point artefacts (unseen drops, TSO); a hash taken before `tcpdump` finished writing, caught and corrected | `lab11-tcp.pcap` (SHA-256 verified) |
| [**LAB 12 — HTTP: Reading Streams and Extracting Files**](module03-traffic-analysis/lab12-http-streams-and-objects/) | Cleartext login and session cookie recovered with Follow TCP Stream; `clientes.csv` rebuilt with Export Objects, byte-identical to the original (SHA-256); navigation path from Referer; client profile from headers, with its limits | `lab12-http.pcap` (SHA-256 verified) |

---

## Lab environment

| Component | Detail |
|---|---|
| Analyst VM | Kali Linux 2026.1 |
| Target VM | Windows 10 Enterprise LTSC |
| Hypervisor | VirtualBox |
| Lab network | Host-only, `192.168.56.0/24`, for all lab traffic. A separate NAT adapter per VM is used only for updates and tool installation. |
| Scope rule | All scanning and testing is limited to VMs I own. No third-party networks are scanned. |

---

## Repository structure

```
network-defense-traffic-investigation-lab/
├── README.md                              ← you are here
├── LICENSE
├── module00-lab-environment/              ← VMs, network modes, isolation
├── module01-networking-fundamentals/
│   ├── README.md                          ← module overview and lab index
│   ├── lab01-network-communication/
│   │   ├── README.md                      ← lab write-up
│   │   ├── screenshots/
│   │   └── evidence/                      ← PCAP + SHA256SUMS
│   ├── lab02-dns-and-tcp/
│   ├── lab03-routing-and-traceroute/
│   └── lab04-ports-and-connections/
├── module02-network-architecture/
├── module03-traffic-analysis/
├── module04-network-reconnaissance/
├── module05-network-defense/
└── module06-dfir-investigation/
```

Each lab is self-contained: a write-up, screenshots, and the hashed evidence it analyses.

---

## Standards referenced

| Standard | Role in this project |
|---|---|
| RFC 3227 | Evidence collection and order of volatility (ARP cache, live connections, captures) |
| ISO/IEC 27037 | Identification, collection and preservation of digital evidence (save and hash captures immediately) |
| ISO/IEC 27042 | Analysis and interpretation of digital evidence |
| NIST SP 800-86 | Integrating forensic techniques into incident response, with network traffic as a data source |
| NIST SP 800-61 | Incident handling: detection, analysis, reporting (Modules 05–06) |
| Protocol RFCs | RFC 826 (ARP), RFC 792 (ICMP), and others per lab, as the technical basis of each analysis |

---

*Network Defense & Traffic Investigation Lab. Built and documented by Paulo Vaz. All activity takes place in an isolated, self-owned virtual lab. No third-party systems are tested and no personal data is published.*
