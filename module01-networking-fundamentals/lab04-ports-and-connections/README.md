# LAB 04 — Ports and Active Connections

`Module 01 — Networking Fundamentals` · `ss · netstat · tasklist` · `Date: 2026-11-22` · `Status: Complete`

## Objective

Find out which ports each lab host is listening on and which connections it has open, then tie every one of them to the program that owns it. Compare a minimal Linux analyst VM with a default Windows target, and read the result the way an investigator would: what is exposed, who owns it, and where each connection goes.

## Repository contents

| Path | Content |
|---|---|
| `README.md` | This write-up |
| `screenshots/` | Terminal output of each step |

No packet capture was taken in this lab: the evidence is the hosts' own socket tables, recorded as screenshots and transcribed below.

---

## 1. Setup

| Host | Interface | Address | Role in this lab |
|---|---|---|---|
| Kali Linux 2026.1 (VM) | eth0 (VirtualBox NAT) | `10.0.2.15/24` | Internet only |
| Kali Linux 2026.1 (VM) | eth1 (Host-only) | `192.168.56.102/24` | Lab network. `ss` baseline. |
| Windows 10 Enterprise LTSC (VM) | Ethernet (VirtualBox NAT) | `10.0.2.15/24` | Internet only |
| Windows 10 Enterprise LTSC (VM) | Ethernet 2 (Host-only) | `192.168.56.101/24` | Lab network. `netstat` and `tasklist`. |

**`netstat` was run on the Windows VM, not the Windows host PC.** The host carries personal traffic (browser, messaging, games), and its connection table would list every remote server it talks to. The VM gives the same learning without that data (**data minimisation**, as in LAB 03).

---

## 2. Key concepts

| Term | Definition |
|---|---|
| **Port** | A number that tells the OS which program a packet is for. The IP address picks the building; the port picks the apartment. |
| **Listening (`LISTEN`)** | A program waiting for someone to knock on its port. A listener is what makes a host reachable, and it is attack surface. |
| **Established (`ESTABLISHED`)** | A connection that completed the TCP handshake and is carrying data |
| **Bind address** | The local address a listener waits on. `0.0.0.0` (or `[::]` for IPv6) means every interface. A specific IP means that interface only. |
| **Ephemeral port** | A temporary high port the OS picks for the client side of a connection (Windows 49152–65535) |
| **PID** | Process ID. The number that links a socket to the program that owns it. |
| **`ss -tuln`** | Linux: TCP and UDP (`-t -u`) listening sockets (`-l`), numeric (`-n`) |
| **`netstat -ano`** | Windows: all sockets (`-a`), numeric (`-n`), with the owning PID (`-o`) |
| **`tasklist /svc`** | Windows: which program, and which services inside it, a PID belongs to |

---

## 3. Part A — Kali: what is listening?

```console
$ ss -tuln
```

> 🔴 **CAPTURE:** paste the exact `ss -tuln` output (header line only, expected) and add the screenshot `screenshots/01-kali-ss-no-listeners.png`.

**Observed:** no listening sockets, TCP or UDP. The prediction before running it was the same: nothing listening.

**Interpretation:** a default Kali install starts no network services. Nothing on this VM is waiting for connections, so another host has nothing to connect to.

**Conclusion (high confidence, direct observation):** the Kali VM exposes no listening ports. Its network attack surface at the time of the check was minimal.

---

## 4. Part B — Windows: what is listening?

```console
C:\Users\NEXCHAIN-WS01>netstat -ano | findstr LISTENING
  TCP    0.0.0.0:135            0.0.0.0:0              LISTENING       968
  TCP    0.0.0.0:445            0.0.0.0:0              LISTENING       4
  TCP    0.0.0.0:5040           0.0.0.0:0              LISTENING       660
  TCP    0.0.0.0:7680           0.0.0.0:0              LISTENING       6592
  TCP    0.0.0.0:49664          0.0.0.0:0              LISTENING       728
  TCP    0.0.0.0:49665          0.0.0.0:0              LISTENING       576
  TCP    0.0.0.0:49666          0.0.0.0:0              LISTENING       1252
  TCP    0.0.0.0:49667          0.0.0.0:0              LISTENING       1224
  TCP    0.0.0.0:49668          0.0.0.0:0              LISTENING       2520
  TCP    0.0.0.0:49670          0.0.0.0:0              LISTENING       720
  TCP    10.0.2.15:139          0.0.0.0:0              LISTENING       4
  TCP    192.168.56.101:139     0.0.0.0:0              LISTENING       4
  TCP    [::]:135               [::]:0                 LISTENING       968
  TCP    [::]:445               [::]:0                 LISTENING       4
  TCP    [::]:7680              [::]:0                 LISTENING       6592
  TCP    [::]:49664             [::]:0                 LISTENING       728
  TCP    [::]:49665             [::]:0                 LISTENING       576
  TCP    [::]:49666             [::]:0                 LISTENING       1252
  TCP    [::]:49667             [::]:0                 LISTENING       1224
  TCP    [::]:49668             [::]:0                 LISTENING       2520
  TCP    [::]:49670             [::]:0                 LISTENING       720
```

> 🔴 **CAPTURE:** `screenshots/02-windows-netstat-listening.png`

**Observed:** 21 listening sockets on 10 distinct TCP ports, against zero on Kali. Only TCP appears, because `findstr LISTENING` filters on the state column and UDP sockets have no state.

### Who owns each port

The PIDs were mapped to programs and services with `tasklist /svc`:

```console
C:\Users\NEXCHAIN-WS01>tasklist /svc /fi "PID eq 968"
svchost.exe                    968 RpcEptMapper, RpcSs

C:\Users\NEXCHAIN-WS01>tasklist /svc /fi "PID eq 4"
System                           4 N/A

C:\Users\NEXCHAIN-WS01>tasklist /svc /fi "PID eq 6592"
svchost.exe                   6592 DoSvc

C:\Users\NEXCHAIN-WS01>tasklist /svc | findstr /r "\<2836\> \<2816\> \<660\> \<728\> \<576\> \<1252\> \<1224\> \<2520\> \<720\>"
wininit.exe                    576 N/A
services.exe                   720 N/A
lsass.exe                      728 KeyIso, SamSs, VaultSvc
svchost.exe                   1224 Schedule
svchost.exe                   1252 EventLog
spoolsv.exe                   2520 Spooler
MpDefenderCoreService.exe     2816 MDCoreSvc
svchost.exe                   2836 WpnService
svchost.exe                    660 CDPSvc
```

*(Header lines of the `tasklist` output omitted.)*

> 🔴 **CAPTURE:** `screenshots/03-windows-tasklist-pid-mapping.png`

| Port | Bound to | PID | Program | Service(s) | What it is |
|---|---|---|---|---|---|
| 135 | all interfaces (v4 + v6) | 968 | `svchost.exe` | `RpcEptMapper`, `RpcSs` | RPC Endpoint Mapper: the "reception desk" that tells clients which high port a given RPC service is on |
| 139 | `10.0.2.15` and `192.168.56.101` separately | 4 | `System` | — | NetBIOS Session Service (legacy file sharing) |
| 445 | all interfaces (v4 + v6) | 4 | `System` | — | SMB, Windows file and printer sharing |
| 5040 | all IPv4 interfaces only | 660 | `svchost.exe` | `CDPSvc` | Connected Devices Platform (device-to-device features) |
| 7680 | all interfaces (v4 + v6) | 6592 | `svchost.exe` | `DoSvc` | Delivery Optimization: Windows Update peer-to-peer sharing |
| 49664 | all interfaces (v4 + v6) | 728 | `lsass.exe` | `KeyIso`, `SamSs`, `VaultSvc` | Local Security Authority: credentials and authentication |
| 49665 | all interfaces (v4 + v6) | 576 | `wininit.exe` | — | Windows start-up process |
| 49666 | all interfaces (v4 + v6) | 1252 | `svchost.exe` | `EventLog` | Windows Event Log |
| 49667 | all interfaces (v4 + v6) | 1224 | `svchost.exe` | `Schedule` | Task Scheduler |
| 49668 | all interfaces (v4 + v6) | 2520 | `spoolsv.exe` | `Spooler` | Print Spooler |
| 49670 | all interfaces (v4 + v6) | 720 | `services.exe` | — | Service Control Manager |

### Interpretation

- **Windows is a "busy building", Kali an empty one.** The same lab, two default installs, ten listening ports versus zero. Each listener is a door someone could knock on.
- **PID 4 is the Windows kernel.** Ports 139 and 445 are served by the kernel's own SMB/NetBIOS drivers, not by a user program, which is why `tasklist` shows no service for it.
- **Port 139 is bound per interface; everything else to all interfaces.** NetBIOS attaches to each IPv4 address separately, which is why it appears twice, once on the NAT adapter and once on the lab adapter.
- **The 4966x ports are RPC dynamic ports.** Port 135 is the reception desk; the high ports are the offices behind it. Each one belongs to a core Windows component (`lsass`, `EventLog`, `Schedule`, `Spooler`, ...).
- **Some listeners exist for features the lab does not use.** Delivery Optimization (7680), Connected Devices (5040) and the Print Spooler are open on a VM that shares no updates, pairs no devices and prints nothing. That is attack surface nobody asked for.
- **Listening is not the same as reachable.** This table shows what the host is ready to accept. Whether another host can actually reach these ports also depends on the Windows Firewall, which this lab did not test (see Module 04).

**Conclusion (high confidence, two sources agree, `netstat` and `tasklist`):** the Windows VM listens on 10 TCP ports, all owned by built-in Windows components. No listener belongs to a third-party or unknown program.

---

## 5. Part C — Windows: active connections

```console
C:\Users\NEXCHAIN-WS01>netstat -ano | findstr ESTABLISHED
  TCP    10.0.2.15:49685        172.172.255.217:443    ESTABLISHED     2836
  TCP    10.0.2.15:49738        172.172.255.217:443    ESTABLISHED     2836
  TCP    10.0.2.15:49774        52.123.244.145:443     ESTABLISHED     2816
```

> 🔴 **CAPTURE:** `screenshots/04-windows-netstat-established.png`

| Local (VM) | Remote | PID | Program | Service |
|---|---|---|---|---|
| `10.0.2.15:49685` | `172.172.255.217:443` | 2836 | `svchost.exe` | `WpnService` (Windows Push Notifications) |
| `10.0.2.15:49738` | `172.172.255.217:443` | 2836 | `svchost.exe` | `WpnService` |
| `10.0.2.15:49774` | `52.123.244.145:443` | 2816 | `MpDefenderCoreService.exe` | `MDCoreSvc` (Microsoft Defender) |

No browser or other user application was open on the VM when this was run.

### Interpretation

- **All three connections are outbound.** The VM's side uses ephemeral ports (49685, 49738, 49774) and the remote side is 443 (HTTPS). The VM called out; nothing called in.
- **All three leave through the NAT adapter (`10.0.2.15`), none through the lab network.** Consistent with LAB 03: internet destinations follow the default route, which points to the NAT adapter.
- **Both owners are built-in Windows components.** Push Notifications keeps a standing connection open so the cloud can send it messages, and Defender talks to its cloud service. This is consistent with normal background traffic of a Windows 10 install.
- **The remote addresses were not looked up.** Ownership of `172.172.255.217` and `52.123.244.145` is not established here. The link to Microsoft rests only on the owning processes; a WHOIS/RDAP lookup would be needed to state it directly.

**Conclusion (moderate confidence):** the three active connections are consistent with routine Windows background services (Push Notifications and Defender) contacting their cloud endpoints over HTTPS. Moderate rather than high because the remote addresses were not independently attributed.

---

## 6. Troubleshooting Log

No problems came up during this lab. The one practical lesson was about method: `netstat -ano` gives only a PID, which means nothing on its own. A second tool (`tasklist /svc`) is needed to turn that number into a program and a service. A single `findstr /r` with word boundaries (`\<PID\>`) mapped nine PIDs at once without matching longer numbers that contain them.

---

## 7. Security / DFIR Relevance

- **The connection table is volatile evidence.** It changes by the second and is lost on reboot, so RFC 3227 places it near the top of the order of volatility, just after memory. Collect it early in triage, with a timestamp, and save the output.
- **Unexpected listeners are a classic indicator.** A backdoor or bind shell shows up as a listening port owned by an odd program. In this lab every listener mapped to a known Windows component, which is the baseline to compare against later.
- **Watch who owns outbound connections.** A reverse shell or C2 implant shows up as an `ESTABLISHED` connection out to an unknown address, owned by something like `cmd.exe`, `powershell.exe`, `rundll32.exe`, or a program in a user folder. Here the owners were `WpnService` and Defender, which is what a clean baseline looks like.
- **A PID is only a pointer.** Attribution needs the second step (`tasklist /svc` here, or EDR telemetry) to name the program, and ideally its path and signature.
- **These tools trust the host.** On a compromised machine, a rootkit can hide sockets from `netstat`. A capture taken from another point on the network is an independent check that the host cannot falsify (Module 03).
- **Default services are attack surface.** SMB (445), RPC (135) and the Print Spooler have all been behind major Windows worms and exploits. Knowing they are open by default is the first step to deciding whether they should be.

---

## 8. Evidence and Data Handling

| Evidence | Form |
|---|---|
| Kali `ss -tuln` | Screenshot 01 |
| Windows `netstat -ano \| findstr LISTENING` | Screenshot 02, transcribed in Part B |
| Windows `tasklist /svc` (PID mapping) | Screenshot 03, transcribed in Part B |
| Windows `netstat -ano \| findstr ESTABLISHED` | Screenshot 04, transcribed in Part C |

The command outputs were not saved to files at the time, so there are no hashes for them. In a real case, the outputs would be redirected to a file (`netstat -ano > netstat.txt`), timestamped and hashed immediately, like the packet captures in LABs 01 to 03.

**Published as-is:** the VirtualBox NAT address `10.0.2.15` (identical in every VirtualBox VM, so it identifies nothing) and the two remote cloud addresses (public service endpoints, not the examiner's network). Nothing from the examiner's home network or ISP appears in this lab.

---

## 9. Verification Q&A

1. **Why did Kali show zero listening ports and Windows ten?**
   A default Kali install starts no network services. Windows starts many by default (file sharing, RPC, update sharing, printing, device features), and each one opens a listening port.
2. **What does `0.0.0.0:445` mean, compared with `192.168.56.101:139`?**
   `0.0.0.0` means the service listens on every interface. `192.168.56.101` means only on that one interface. That is why port 139 appears twice, once per adapter.
3. **`netstat` shows PID 4 on port 445. What is PID 4?**
   The Windows kernel (`System`). SMB is served by kernel drivers, not by a normal program.
4. **How do you go from a PID to a program and a service on Windows?**
   `tasklist /svc /fi "PID eq <PID>"`. The `/svc` flag lists which services run inside a shared `svchost.exe`.
5. **How do you know the three ESTABLISHED connections were opened by the VM and not by someone connecting in?**
   The VM's side uses ephemeral high ports and the remote side uses a well-known service port (443). The client is the one with the ephemeral port.
6. **Why is a listening port not proof that the port is reachable?**
   It only shows that the host is ready to accept connections. A firewall can still block them, and that has to be tested from another host.
7. **Why collect the connection table early in an incident, and why is it not enough on its own?**
   It is highly volatile and links live connections to programs. It is not enough because a compromised host can hide sockets, so it should be corroborated by a capture or logs from an independent point.

---

## 10. References

- RFC 9293 — Transmission Control Protocol (connection states)
- RFC 6335 — IANA procedures for port numbers (system, user and dynamic ranges)
- RFC 3227 — Guidelines for Evidence Collection and Archiving (order of volatility)
- `ss(8)` manual page (iproute2)
- Microsoft Learn — `netstat`, `tasklist`, "Service overview and network port requirements for Windows"
- NIST SP 800-86 — Guide to Integrating Forensic Techniques into Incident Response
- LGPD (Lei 13.709/2018), art. 6º, III — necessity principle (data minimisation)
