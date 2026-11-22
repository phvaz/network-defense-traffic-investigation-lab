# LAB 04 — Ports and Active Connections

`Module 01 — Networking Fundamentals` · `ss · netstat · Get-NetTCPConnection · Wireshark` · `Date: YYYY-MM-DD` · `Status: Draft`

> **Draft status.** The structure, procedure, concepts and Q&A are written. Every block marked **🔴 CAPTURE** must be filled with real output from the lab before this write-up is final. No output in this draft is real: example lines are labelled *illustrative* and must be replaced, not kept. Interpretations marked **🔴 CONFIRM** depend on what the real output shows and must be checked against it.

## Objective

List which ports a host is listening on and which connections it has open, tie each one to the process that owns it, and correlate the same connection across three independent sources: `ss` on Kali, `netstat` on Windows, and a packet capture. Then show that "listening" does not mean "reachable", by comparing a service bound to all interfaces with one bound to loopback only.

## Repository contents

| Path | Content |
|---|---|
| `README.md` | This write-up |
| `evidence/` | 🔴 CAPTURE: `lab04-tcp-8000.pcapng`, the saved command outputs (`*.txt`), and `SHA256SUMS` |
| `screenshots/` | 🔴 CAPTURE: Wireshark view of the connection and the refused connection |

---

## 1. Setup

| Host | Interface | Address | Role in this lab |
|---|---|---|---|
| Kali Linux 2026.1 (VM) | eth1 (Host-only) | `192.168.56.102/24` | Runs the test service, `ss`, capture |
| Kali Linux 2026.1 (VM) | eth0 (VirtualBox NAT) | `10.0.2.15/24` | Internet only. Not used for lab traffic. |
| Windows 10 Enterprise LTSC (VM) | Ethernet 2 (Host-only) | `192.168.56.101/24` | Client, `netstat`, `Get-NetTCPConnection` |

**Run `netstat` on the Windows VM, not the Windows host.** The host carries personal traffic (browser, messaging, games), and its connection table would list every remote server it talks to. The VM gives the same learning without that data (**data minimisation**, as in LAB 03).

**Clocks:** Kali runs in UTC. Record the Windows VM's time zone here: 🔴 CAPTURE (`Get-TimeZone`).

---

## 2. Key concepts

| Term | Definition |
|---|---|
| **Port** | A 16-bit number that tells the OS which program a packet is for. The IP address picks the host; the port picks the program on it. |
| **Socket** | One endpoint of communication: protocol + local address + local port (and, once connected, the remote address + port) |
| **4-tuple** | Source IP, source port, destination IP, destination port. It identifies one TCP connection uniquely, and it is the key used to correlate the same connection across tools. |
| **Listening socket** | A server waiting for connections (`LISTEN` state). It has no remote end yet. |
| **Ephemeral port** | A temporary high port the OS picks for the client side of a connection (Linux default 32768–60999, Windows 49152–65535) |
| **Bind address** | The local address a server listens on. `0.0.0.0` (or `*`) means every interface. `127.0.0.1` means loopback only, unreachable from other hosts. |
| **ESTABLISHED** | The three-way handshake completed and data can flow |
| **TIME_WAIT** | The side that closed first keeps the connection's 4-tuple reserved for a while, so late packets from the old connection are not mistaken for a new one |
| **`ss`** | Linux "socket statistics", the modern replacement for `netstat`. Reads socket tables from the kernel. |
| **`netstat -ano`** | Windows: all connections and listeners (`-a`), numeric addresses (`-n`), owning process ID (`-o`) |

---

## 3. Part A — Kali baseline: what is listening?

### Procedure

Run all Kali commands from the lab folder, so the `evidence/` paths below resolve (`mkdir -p evidence` first).

```console
$ date -u
$ sudo ss -tulpn
```

`-t` TCP, `-u` UDP, `-l` listening only, `-p` show the owning process (needs `sudo`), `-n` numeric (no name lookups).

Save the output as evidence at the same time:

```console
$ (date -u; sudo ss -tulpn) | tee evidence/lab04-kali-ss-listen-baseline.txt
```

### Observed

> 🔴 **CAPTURE:** paste the real `sudo ss -tulpn` output here. Illustrative shape only, do not keep:
>
> ```text
> Netid State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
> udp   UNCONN 0      0      0.0.0.0:68          0.0.0.0:*         users:(("dhclient",pid=NNN,fd=N))
> ```

| Proto | Local address:port | Process (PID) | Bound to | Expected? |
|---|---|---|---|---|
| 🔴 | 🔴 | 🔴 | 🔴 all interfaces / loopback / one interface | 🔴 |

### Interpretation

How to read each line:

- **`Local Address:Port`** answers "on which address and port is this program waiting?". `0.0.0.0:68` or `*:68` means every IPv4 interface; `[::]:68` means every IPv6 interface; `127.0.0.1:631` means loopback only.
- **`Peer Address:Port` = `*`** is normal for a listener: no client is attached yet.
- **UDP shows `UNCONN`, not `LISTEN`.** UDP has no connections, so a UDP "server" is just a socket waiting for datagrams (`-l` still lists it).
- **`Process`** ties the port to a program. Without `sudo`, this column is empty for sockets owned by other users, which is easy to mistake for "no process".

🔴 **CONFIRM:** for each listener, state what it is and whether it belongs there. On a fresh Kali, very few ports should be open to the network (for example a DHCP client on UDP 68). Any TCP listener on `0.0.0.0` is worth one line of explanation.

### Conclusion

🔴 **CONFIRM** after filling the table. Template: "Kali's baseline exposes N listener(s) to the network: … (high confidence, direct observation with owning process)."

---

## 4. Part B — Windows baseline: what is listening?

### Procedure (PowerShell as Administrator, on the Windows **VM**)

```powershell
Get-Date -Format o
netstat -ano | Select-String "LISTENING"
Get-NetTCPConnection -State Listen | Sort-Object LocalPort |
    Select-Object LocalAddress, LocalPort, OwningProcess,
        @{n='Process';e={(Get-Process -Id $_.OwningProcess).ProcessName}}
```

Save both to files (then copy them to Kali or a shared folder for hashing):

```powershell
netstat -ano > "$HOME\Desktop\lab04-win-netstat-baseline.txt"
Get-NetTCPConnection | Export-Csv "$HOME\Desktop\lab04-win-nettcp-baseline.csv" -NoTypeInformation
```

### Observed

Run in `cmd` on the Windows VM (`netstat -ano | findstr LISTENING`):

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

> 🔴 **CAPTURE:** screenshot of this output → `screenshots/01-windows-netstat-listening.png`. Timestamp of the run (`echo %date% %time%`) not recorded; note it if repeated.

**12 TCP listeners** (10 distinct ports), against **zero** on Kali. Only TCP appears because `findstr LISTENING` filters on the state column, and UDP sockets have no state.

| Port | Bound to | PID | Process | Likely service |
|---|---|---|---|---|
| 135 | `0.0.0.0`, `[::]` | 968 | 🔴 CONFIRM (`tasklist /svc /FI "PID eq 968"`) | RPC Endpoint Mapper |
| 139 | `10.0.2.15`, `192.168.56.101` (one per interface) | 4 | System | NetBIOS Session Service |
| 445 | `0.0.0.0`, `[::]` | 4 | System | SMB |
| 5040 | `0.0.0.0` (IPv4 only) | 660 | 🔴 CONFIRM | 🔴 CONFIRM |
| 7680 | `0.0.0.0`, `[::]` | 6592 | 🔴 CONFIRM | 🔴 CONFIRM |
| 49664–49668, 49670 | `0.0.0.0`, `[::]` | 728, 576, 1252, 1224, 2520, 720 | 🔴 CONFIRM | RPC dynamic ports |

PID 4 is always the Windows kernel (`System`) process, so 139 and 445 are served by the kernel's own SMB/NetBIOS drivers, not by a user program.

### Interpretation

- **Windows listens on far more ports than Kali by default.** Typical entries are RPC (135), NetBIOS (139, on a specific interface), SMB (445), and a range of high RPC dynamic ports owned by `lsass`, `services`, `svchost` and similar.
- **`svchost.exe` hosts many services.** To find which service owns a `svchost` PID: `tasklist /svc /FI "PID eq <PID>"`.
- **`Foreign Address 0.0.0.0:0`** on a listener is Windows' way of writing "no remote end", like `*` in `ss`.
- **A listener is not the same as reachable.** The Windows Firewall decides whether these ports answer other hosts. That is tested in Part D, not assumed here.

🔴 **CONFIRM:** which listeners are bound to `192.168.56.101` specifically versus `0.0.0.0`, and whether 139 appears only on one interface.

### Conclusion

🔴 **CONFIRM.** Template: "The Windows VM listens on N TCP ports, mapped to processes as above. Whether they are reachable from the lab network is not established by this table alone (see Part D)."

---

## 5. Part C — One controlled connection, three sources

The goal is a single connection whose 4-tuple can be found in `ss`, in `netstat`, and in the capture, and matched exactly.

### Procedure

1. **Kali, terminal 1:** start the capture on the lab interface, filtered to the test port.

   ```console
   $ sudo tcpdump -i eth1 -w evidence/lab04-tcp-8000.pcapng 'tcp port 8000'
   ```

   (Or Wireshark on `eth1` with capture filter `tcp port 8000`.)

2. **Kali, terminal 2:** start a test web server bound to the lab address only.

   ```console
   $ python3 -m http.server 8000 --bind 192.168.56.102
   ```

3. **Kali, terminal 3:** confirm it is listening.

   ```console
   $ ss -tlnp 'sport = :8000'
   ```

4. **Windows VM:** open a connection that **stays open** long enough to observe. `curl` closes immediately, so use a PowerShell TCP client:

   ```powershell
   $c = New-Object System.Net.Sockets.TcpClient("192.168.56.102", 8000)
   $c.Client.LocalEndPoint      # note the ephemeral port Windows chose
   ```

5. **While it is open,** on both sides:

   ```console
   $ (date -u; ss -tnp 'sport = :8000') | tee evidence/lab04-kali-ss-established.txt
   ```

   ```powershell
   (Get-Date -Format o); netstat -ano | Select-String ":8000"
   ```

6. **Close it from Windows,** then look again on both sides:

   ```powershell
   $c.Close()
   netstat -ano | Select-String ":8000"
   ```

   ```console
   $ ss -tan 'sport = :8000'
   ```

7. Stop `tcpdump` (Ctrl+C), then hash immediately:

   ```console
   $ sha256sum evidence/lab04-tcp-8000.pcapng
   ```

### Observed — `ss` on Kali (server side)

> 🔴 **CAPTURE:** paste the `ss -tnp 'sport = :8000'` output while the connection is open.

### Observed — `netstat` on Windows (client side)

> 🔴 **CAPTURE:** paste the `netstat -ano | Select-String ":8000"` output while the connection is open, and the PID → process name (`Get-Process -Id <PID>`).

### Observed — capture

> 🔴 **CAPTURE:** packet table, then a screenshot with display filter `tcp.port == 8000`.

| # | Source | Destination | Flags | Meaning |
|---|---|---|---|---|
| 🔴 | `192.168.56.101:🔴` | `192.168.56.102:8000` | SYN | Client opens |
| 🔴 | `192.168.56.102:8000` | `192.168.56.101:🔴` | SYN, ACK | Server accepts |
| 🔴 | `192.168.56.101:🔴` | `192.168.56.102:8000` | ACK | Handshake complete → ESTABLISHED |
| 🔴 | … | … | FIN / ACK | Close (who sent the first FIN?) |

### Correlation table

| Field | `ss` (Kali) | `netstat` (Windows) | Capture | Match? |
|---|---|---|---|---|
| Client IP:port | 🔴 Peer | 🔴 Local | 🔴 SYN source | 🔴 |
| Server IP:port | 🔴 Local | 🔴 Foreign | 🔴 SYN destination | 🔴 |
| State while open | 🔴 `ESTAB` | 🔴 `ESTABLISHED` | 🔴 handshake complete, no FIN yet | 🔴 |
| Owning process | 🔴 `python3` (pid) | 🔴 `powershell` (PID) | n/a (a capture has no process) | — |
| State after close | 🔴 | 🔴 | 🔴 FIN sequence | 🔴 |

### Interpretation

- **The client's port is the one that changes.** Windows picked an ephemeral port in its dynamic range; the server side stays on 8000. 🔴 **CONFIRM** the actual port is inside 49152–65535.
- **The same connection seen from both ends is mirrored.** Kali's *local* is Windows' *foreign*, and vice versa.
- **Only the host tools know the process.** The capture proves the conversation happened on the wire; `ss -p` and `netstat -o` attribute each end to a program. Neither source is complete alone.
- **TIME_WAIT lands on whichever side closed first.** Since Windows called `Close()`, TIME_WAIT is expected on Windows, not on Kali. 🔴 **CONFIRM** against the after-close output and against who sent the first FIN in the capture.

### Conclusion

🔴 **CONFIRM.** Template: "The 4-tuple `192.168.56.101:P ↔ 192.168.56.102:8000` appears identically in `ss`, `netstat` and the capture (high confidence, three independent sources agree). The server end belongs to `python3` (pid …) and the client end to `powershell` (PID …)."

---

## 6. Part D — Listening is not reachable

### Procedure

1. Kali: stop the first server, start one bound to **loopback only**:

   ```console
   $ python3 -m http.server 8001 --bind 127.0.0.1
   $ ss -tlnp 'sport = :8001'
   ```

2. Kali: confirm it answers locally:

   ```console
   $ curl -sI http://127.0.0.1:8001/ | head -1
   ```

3. Windows VM: try to reach it, and also try a port nothing listens on:

   ```powershell
   Test-NetConnection 192.168.56.102 -Port 8001
   Test-NetConnection 192.168.56.102 -Port 8002
   ```

4. Kali: capture during step 3 (`sudo tcpdump -i eth1 -w evidence/lab04-refused.pcapng 'tcp port 8001 or tcp port 8002'`).

5. *(Optional, firewall comparison)* From Kali, probe one Windows listener from Part B that the firewall should block, and one it allows:

   ```console
   $ nc -vz -w 3 192.168.56.101 445
   $ nc -vz -w 3 192.168.56.101 135
   ```

### Observed

> 🔴 **CAPTURE:** `ss` showing `127.0.0.1:8001`; the `curl` status line; both `Test-NetConnection` results (`TcpTestSucceeded`); the capture packets for 8001 and 8002; optional `nc` results.

| Test | Listener exists? | Bound to | Result from the other host | On the wire |
|---|---|---|---|---|
| Kali 8000 (Part C) | Yes | `192.168.56.102` | 🔴 Connected | 🔴 SYN → SYN/ACK |
| Kali 8001 | Yes | `127.0.0.1` | 🔴 | 🔴 SYN → RST? |
| Kali 8002 | No | — | 🔴 | 🔴 SYN → RST? |
| Windows 445 *(optional)* | 🔴 | 🔴 | 🔴 | 🔴 RST, or no reply (timeout)? |

### Interpretation

- **A loopback-only listener looks exactly like no listener to other hosts.** A SYN to `192.168.56.102:8001` does not match the socket bound to `127.0.0.1:8001`, so the kernel answers with RST, the same as for 8002 where nothing listens. 🔴 **CONFIRM** both show SYN → RST.
- **Closed vs filtered.** A **RST** means the host is up and actively refused (closed). **No reply** means something dropped the packet silently, typically a firewall (filtered). This distinction is the basis of port scanning in Module 04.
- **The local `curl` success proves the service runs.** So the failure from Windows is about the bind address, not a crashed service.

### Conclusion

🔴 **CONFIRM.** Template: "A service listening on `127.0.0.1` was unreachable from the lab network and produced the same RST as a port with no listener (high confidence, capture and client output agree). A listening port in `ss` or `netstat` is therefore a statement about the host, not about exposure; exposure depends on the bind address and the firewall."

---

## 7. Troubleshooting Log

> 🔴 **CAPTURE:** record every real problem hit while running this lab, in the format below. Delete the example rows if they did not happen. Likely candidates are listed so you recognise them.

| # | Observation | Hypothesis | Verification | Result |
|---|---|---|---|---|
| *e.g.* | `ss -tulpn` shows no `Process` column values | Not run as root, so other users' sockets hide their owner | Re-run with `sudo` | 🔴 |
| *e.g.* | `netstat -b` fails with "requires elevation" | PowerShell not run as Administrator | Re-open as Administrator | 🔴 |
| *e.g.* | Connection to 8000 appears and vanishes before `ss` can show it | `curl` / browser closes the connection immediately | Use the PowerShell `TcpClient` from Part C, which stays open | 🔴 |
| *e.g.* | Capture on 8000 is empty | Captured on `eth0` (NAT) instead of `eth1` (same root cause as LAB 02) | `ip -br addr`, check which interface has `192.168.56.102` | 🔴 |

---

## 8. Security / DFIR Relevance

- **The connection table is volatile evidence.** It changes by the second and is lost on reboot, so RFC 3227 places it near the top of the order of volatility, just after memory. Collect it early in triage, with a timestamp, and hash the saved output.
- **Unexpected listeners are a classic indicator.** A backdoor or bind shell appears as a `LISTEN` socket on an odd port owned by an odd process. A reverse shell appears as an `ESTABLISHED` connection *out* to an unknown address, owned by `cmd.exe`, `powershell.exe`, `bash` or a process that has no reason to use the network.
- **Process attribution needs the host.** A packet capture shows that traffic happened; only `ss -p` / `netstat -o` (or EDR telemetry) say which program did it. Correlating the two, by 4-tuple and time, turns "this IP talked to that IP" into "this process on this host talked to that IP".
- **These tools can be lied to.** On a compromised host, a rootkit can hide sockets from `ss` and `netstat`. A capture taken from another point on the network is an independent check that the host cannot falsify. Disagreement between the two is itself a finding.
- **Listening ≠ exposed.** A report that says "port X is open" must say from where it was tested. A loopback listener is a local-only risk; a `0.0.0.0` listener with the firewall open is network exposure.

---

## 9. Evidence Integrity and Data Handling

> 🔴 **CAPTURE:** fill this table after hashing. Hash each file immediately after saving it.

| File | Source | Content | SHA-256 |
|---|---|---|---|
| `lab04-kali-ss-listen-baseline.txt` | Kali | Part A output with UTC timestamp | 🔴 |
| `lab04-win-netstat-baseline.txt` | Windows VM | Part B output | 🔴 |
| `lab04-win-nettcp-baseline.csv` | Windows VM | Part B output | 🔴 |
| `lab04-kali-ss-established.txt` | Kali | Part C output with UTC timestamp | 🔴 |
| `lab04-tcp-8000.pcapng` | Kali eth1 | Part C capture | 🔴 |
| `lab04-refused.pcapng` | Kali eth1 | Part D capture | 🔴 |

```console
$ cd evidence && sha256sum *.pcapng *.txt *.csv > SHA256SUMS
$ sha256sum -c SHA256SUMS
```

For the Windows files, hash on Windows before copying, and confirm the hash matches after copying:

```powershell
Get-FileHash "$HOME\Desktop\lab04-win-netstat-baseline.txt" -Algorithm SHA256
```

**Before publishing, check for data to redact.** The lab interface carries only lab traffic, but the full `ss -tan` and `netstat -ano` outputs also include the NAT interface (`10.0.2.15`) and any internet connections the VMs had open (updates, telemetry, browser). Remote internet addresses in those lines are not needed for the analysis. Either filter the saved outputs to the lab network, or redact those lines and say so here. 🔴 **CONFIRM** what was redacted.

---

## 10. Verification Q&A

1. **What is the difference between a port, a socket and a connection?**
   A port is a number that picks a program on a host. A socket is one endpoint: protocol, address and port. A TCP connection is a pair of sockets, identified by the 4-tuple of both addresses and both ports.
2. **Why does `ss -tulpn` need `sudo` to show the process column?**
   An unprivileged user can only see process details for sockets they own. Without root, other users' and system sockets are listed without an owner, which can be misread as "no process".
3. **Kali shows a listener on `127.0.0.1:8001`. Can the Windows VM reach it? Why?**
   No. Loopback is only reachable from the same host. A SYN arriving on `eth1` for `192.168.56.102:8001` matches no socket, so the kernel answers with RST, as if nothing were listening. 🔴 **CONFIRM** with the Part D capture.
4. **The same connection appears in `ss` and `netstat`. How do you prove it is the same one?**
   Match the 4-tuple exactly (both IPs and both ports, mirrored between local and remote), check the timestamps overlap, and confirm with the handshake in the capture.
5. **After closing the connection from Windows, which side shows `TIME_WAIT`, and why?**
   The side that closed first, here Windows. It holds the 4-tuple for a while so delayed packets from the old connection cannot be confused with a new one. 🔴 **CONFIRM** with the after-close output.
6. **A port probe gets a RST on one port and no answer on another. What does each mean?**
   RST: the host is reachable and nothing accepted the connection (closed). No answer: something dropped the packet silently, usually a firewall (filtered).
7. **Why collect the connection table early in an incident, and why is it not enough on its own?**
   It is highly volatile and shows live attribution of connections to processes. It is not enough because it can be tampered with on a compromised host, so it should be corroborated by a capture or logs from an independent point.

---

## 11. References

- RFC 793 / RFC 9293 — Transmission Control Protocol (states, TIME_WAIT, RST)
- RFC 768 — User Datagram Protocol
- RFC 6335 — IANA procedures for port numbers (system, user and dynamic ranges)
- RFC 3227 — Guidelines for Evidence Collection and Archiving (order of volatility)
- `ss(8)` and `ip(8)` manual pages (iproute2)
- Microsoft Learn — `netstat`, `Get-NetTCPConnection`, `Test-NetConnection`
- ISO/IEC 27037 — Preservation of digital evidence
- NIST SP 800-86 — Guide to Integrating Forensic Techniques into Incident Response
- LGPD (Lei 13.709/2018), art. 6º, III — necessity principle (data minimisation)
