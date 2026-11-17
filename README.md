# Module 00 — Lab Environment

## Objective

Set up an isolated virtual lab in which two hosts can communicate with each other, and document how the VirtualBox network modes affect connectivity and isolation.

---

## Lab architecture

```
┌──────────────────────────────────────────────────────┐
│                    HOST (Windows)                    │
│                      VirtualBox                      │
│                                                      │
│  ┌──────────────────────┐  ┌──────────────────────┐  │
│  │  Windows 10 (target) │  │  Kali 2026.1 analyst │  │
│  │                      │  │                      │  │
│  │  NIC 1: NAT          │  │  NIC 1: NAT          │  │
│  │    10.0.2.15         │  │    10.0.2.15         │  │
│  │  NIC 2: Host-only    │  │  NIC 2: Host-only    │  │
│  │    192.168.56.101    │  │    192.168.56.102    │  │
│  │    (static)          │  │    (DHCP)            │  │
│  └──────────────────────┘  └──────────────────────┘  │
│                                                      │
│   Host-only network: 192.168.56.0/24                 │
│   DHCP server (VirtualBox): 192.168.56.100           │
└──────────────────────────────────────────────────────┘
```

---

## Hosts

| Field | Windows (target) | Kali (analyst) |
|---|---|---|
| Operating system | Windows 10 Enterprise LTSC | Kali Linux 2026.1 |
| Lab interface | Ethernet 2, `08:00:27:46:67:11` | eth1, `08:00:27:c3:37:eb` |
| Lab IPv4 | `192.168.56.101/24` (static) | `192.168.56.102/24` (DHCP) |
| Internet interface | Ethernet (NAT), `10.0.2.15` | eth0 (NAT), `08:00:27:8a:35:d2`, `10.0.2.15` |
| Guest Additions | Installed | Installed (`virtualbox-guest-x11`) |

![Windows VM — Adapter 2 attached to the Host-only network](screenshots/01-windows-adapter2-hostonly.png)

![Kali VM — Adapter 2 attached to the Host-only network](screenshots/02-kali-adapter2-hostonly.png)

### Configuration history (Kali)

| Date | Adapter 1 | Adapter 2 | Lab IP | Note |
|---|---|---|---|---|
| 2026-11-16 | Host-only (`08:00:27:8a:35:d2`) | — | `192.168.56.104` | Temporary layout used in LAB 01. No internet access. |
| 2026-11-17 | NAT (`08:00:27:8a:35:d2`) | Host-only (`08:00:27:c3:37:eb`) | `192.168.56.102` | Final layout. Internet and lab both verified. |

**Why this matters for investigations:** the same Kali VM appeared as `.104` on one day and `.102` on the next, because the DHCP server leased it a different address. **An IP address alone does not identify a machine.** Attributing an IP to a device requires the DHCP lease record (IP ↔ MAC ↔ time) for the moment in question.

### Connectivity verification

```console
$ ping -c 2 8.8.8.8
64 bytes from 8.8.8.8: icmp_seq=1 ttl=64 time=23.1 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=64 time=23.8 ms

$ ping -c 2 192.168.56.101
64 bytes from 192.168.56.101: icmp_seq=1 ttl=128 time=1.27 ms
64 bytes from 192.168.56.101: icmp_seq=2 ttl=128 time=0.609 ms
```

**TTL caveat observed:** the reply from `8.8.8.8` (an internet host many hops away) arrived with `ttl=64`, not a decremented value. The VirtualBox NAT engine answers on behalf of the remote host, so this TTL reflects the NAT engine, not Google's server. This is direct evidence that TTL is *consistent with* an OS at best, and that middleboxes can rewrite it.

> The first lab ping after reconfiguration returned `Destination Host Unreachable` from `192.168.56.102`, which means the ARP request got no reply. Cause: the Windows VM was powered off. Same root cause and diagnosis as the LAB 01 troubleshooting log.

---

## VirtualBox network modes

| Mode | What it is | Observed behaviour |
|---|---|---|
| **NAT** | A private "router" for each VM, used to reach the internet through the host | Each VM gets its **own isolated** NAT. Kali and Windows both received `10.0.2.15` with no conflict, and they could **not** reach each other. |
| **Host-only** | A private network **shared** by the VMs and the host, with no internet | Both VMs joined `192.168.56.0/24` and reached each other. |
| **NAT Network** | A NAT shared by several VMs (closer to a real office network) | Not used yet. Candidate for later modules. |

**Why Host-only for the lab:** it lets the VMs talk to each other while keeping all test traffic (scans, captures, simulated attacks) off the internet and off the physical home network.

**Recommended layout per VM:** Adapter 1 = NAT (updates and tool installation), Adapter 2 = Host-only (lab traffic). The adapter order is a convention; what matters is the combination.

---

## Isolation and scope

- All testing targets only the VMs in this lab.
- The Host-only network has no route to the internet.
- Outputs that reveal the physical network (for example, the host's ISP DNS servers that appear in the Windows NAT adapter) are **not** published.

---

## Setup checklist

- [x] Windows: Adapter 1 = NAT, Adapter 2 = Host-only (static `192.168.56.101`)
- [x] Kali: Adapter 1 = NAT, Adapter 2 = Host-only (2026-11-17)
- [x] Kali: VirtualBox Guest Additions installed (`virtualbox-guest-x11`); shared clipboard and drag-and-drop set to bidirectional
- [x] Connectivity verified: Kali → internet (NAT) and Kali → Windows (Host-only)
