# LAB 15 — Investigation Challenge: The ACME Incident

`Module 03 — Traffic Analysis` · `Wireshark · tshark · Export Objects` · `Date: 2026-11-27` · `Status: Complete`

## About this lab

This is a **worked example**: a synthetic incident capture, followed by the full analysis written as a technical report. The capture was generated with a script (`scenario/generate_scenario.py`) so that every packet is known and the data is safe to publish:

- All names, addresses and data are fictitious. Internal addresses use RFC 1918 space; external hosts use the RFC 5737 documentation ranges and `example.*` domains (RFC 2606).
- The "malicious" file is inert text.
- The script uses a fixed random seed, so it regenerates the evidence file byte for byte.

It applies everything from LABs 11–14 (HTTP streams, Export Objects, hashes, scan and beacon signatures, upload ratios) to one case, and rehearses the full investigation planned for Module 06.

## Repository contents

| Path | Content |
|---|---|
| `README.md` | Case brief and technical report |
| `evidence/lab15-acme-incident.pcap` | The capture (1,543 packets, 29 min 25 s) |
| `evidence/SHA256SUMS` | SHA-256 of the capture |
| `scenario/generate_scenario.py` | Script that generated the capture (scapy) |

---

## 1. Case brief

> At 12:27 UTC on 2026-11-27 the antivirus on one of ACME's finance workstations flagged a suspicious file named `NF-e_38211.pdf.exe`. Nobody knows yet which workstation it was or what happened before the alert. The network team provides a capture from the core switch mirror port covering 12:00 to 12:30 UTC.

| Item | Value |
|---|---|
| Evidence | `lab15-acme-incident.pcap`, SHA-256 `ee0a05d7a77e6819be15689064482ead8070b035e7dee9f511bc4dd61fc4ceca` |
| Capture window | 2026-11-27 12:00:20 – 12:29:45 UTC |
| Internal network | `10.20.0.0/24`: gateway `.1`, DNS `.2`, file server FS01 `.10`, intranet `.20`, workstations `.31`, `.45`, `.52` |
| Questions | Which host? How did it start? Who is the C2 and what is its rhythm? What did the attacker do? What left, how much, and can it be proved? |

---

## 2. Executive summary

Workstation **`10.20.0.45` (WS-FIN-07)** downloaded `NF-e_38211.pdf.exe` from a fake invoice site at **12:05:16 UTC**. About 45 seconds later it started contacting **`cdn-sync.example.net` (`203.0.113.66`) on TCP 8080** roughly every 60 seconds, with random variation. This pattern is consistent with command-and-control (C2) beaconing.

The C2 ordered two actions, and both appear in the capture right after the order:

1. **12:12:10** — a scan of the internal network. The workstation swept all 254 addresses with ARP, probed six live hosts on ports 80, 445 and 3389, and reported the open ports back.
2. **12:19:03** — collection of `clientes_2026.csv` from the file server. The workstation downloaded the file (169,635 bytes) and **14 seconds later uploaded it to the C2**. Both copies were extracted from the capture and have the **same SHA-256**.

The implant was still beaconing at the end of the capture (12:29:45), after the 12:27 antivirus alert. No other workstation showed signs of compromise in this window. Recommendation: isolate WS-FIN-07, block the two external indicators, and treat the customer file as disclosed.

---

## 3. Method

1. Verified the evidence hash (`sha256sum -c SHA256SUMS`) before analysis.
2. Got the overall picture: **Statistics → Protocol Hierarchy** (DNS, HTTP, ARP only) and **Statistics → Conversations → IPv4**.
3. Pivoted from the only known fact, the file name: `frame contains "NF-e_38211"`.
4. Followed the suspect host forward in time: its DNS queries, its HTTP requests, and the gaps between them.
5. Read each C2 exchange with **Follow → HTTP Stream**, and rebuilt files with **File → Export Objects → HTTP**, hashing what was extracted.
6. Compared every "suspicious" pattern with the same behaviour on other hosts, to rule out benign look-alikes.

The command-line equivalents (`tshark`) are given with each finding so the results can be reproduced.

---

## 4. Findings

### 4.1 Patient zero and initial access

```console
$ tshark -r lab15-acme-incident.pcap -Y 'http.request.uri contains "38211"' -t ud \
    -T fields -e frame.number -e frame.time -e ip.src -e http.host -e http.request.uri
110  12:05:10.011  10.20.0.45  nfe-portal.example.com  /nota/38211
121  12:05:16.401  10.20.0.45  nfe-portal.example.com  /download/NF-e_38211.pdf.exe
```

| Frame | Time (UTC) | Event |
|---|---|---|
| 105–106 | 12:05:10 | `10.20.0.45` resolves `nfe-portal.example.com` → `198.51.100.23` |
| 110 → 112 | 12:05:10 | Page "Nota Fiscal Eletronica… Baixar NF-e 38211 (PDF)" |
| 121 → 141 | 12:05:16 | Download of `NF-e_38211.pdf.exe`, `application/octet-stream`, 21,504 B, with `Referer: …/nota/38211` |

**Interpretation:**

- The host is `10.20.0.45`, the only one that ever contacted `nfe-portal.example.com`.
- The flow (a landing page about an invoice, then a "PDF" that is really `.exe`) is consistent with a **phishing lure using a double file extension**. Windows hides known extensions by default, so the user sees `NF-e_38211.pdf`.
- The six seconds between the page and the download are consistent with a person clicking a link.
- The file rebuilt with Export Objects has SHA-256 `7b46f242fae9e4b35ba4a63cfeaba9d4d2c415ae950846c56482a960d22d1d06`. That is the hash to search for on other endpoints.

### 4.2 Command and control

```console
$ tshark -r lab15-acme-incident.pcap -Y 'http.request.uri contains "/api/v2/ping"' -T fields -e frame.time_epoch \
  | awk 'NR>1{d=$1-p; s+=d; if(!m||d<m)m=d; if(d>M)M=d; n++} {p=$1} END{printf "n=%d mean=%.1f min=%.1f max=%.1f\n",n+1,s/n,m,M}'
n=25 mean=59.3 min=51.7 max=67.0
```

| Property | Value |
|---|---|
| First DNS lookup | 12:06:01.98, `cdn-sync.example.net` → `203.0.113.66` (frame 176), 45 s after the download |
| Channel | Plain HTTP to TCP **8080**, `GET /api/v2/ping?id=WS-FIN-07` |
| Check-ins | **25**, from 12:06:02 to 12:29:45 (still active at the end of the capture) |
| Interval | mean **59.3 s**, range 51.7–67.0 s, i.e. 60 s with about ±15 % jitter |
| Normal reply | `{"cmd":"sleep"}` |
| User-Agent | `Mozilla/5.0 (Windows NT 10.0; Win64; x64)`, a truncated string, unlike the full Edge User-Agent the same host sends when browsing |
| Host's own label | `id=WS-FIN-07` in every request |

**Interpretation:**

- A new external host contacted on a fixed schedule, starting right after the download, is consistent with the downloaded file being an implant that beacons to its C2.
- Unlike LAB 14, the interval **varies** (jitter), which is what real implants do to avoid perfect regularity. The rhythm is still obvious over 25 samples.
- The truncated User-Agent supports this: the program pretends to be a browser but does not match the real browser on the same machine.

**Ruling out the look-alike.** Another periodic pattern exists in the capture:

```console
$ tshark -r lab15-acme-incident.pcap -Y 'http.request.uri == "/v2/check"' -T fields -e ip.src | sort | uniq -c
      6 10.20.0.31
      6 10.20.0.45
      6 10.20.0.52
```

`updates.example.com/v2/check` is called **exactly every 300.00 s by all three workstations**, with the User-Agent `AcmeUpdater/24.11`. The reply is `{"status":"up-to-date"}`. A schedule shared by every host, to a vendor update endpoint, with a self-identifying agent, is consistent with legitimate software. It was **not** treated as malicious. Regularity is a lead, not a verdict (LAB 14).

### 4.3 Discovery: internal scan on command

At 12:12:10 the C2 reply changed:

```text
frame 366   {"cmd":"scan","args":"10.20.0.0/24 80,445,3389"}
```

Four seconds later the workstation did exactly that:

| Frames | Time (UTC) | Activity |
|---|---|---|
| 372–630 | 12:12:14.29 – 12:12:14.82 | **ARP sweep**: 253 `who-has` requests for every address in `10.20.0.0/24`, in 0.53 s. Only 6 hosts answered. |
| 631–663 | 12:12:15.22 – 12:12:15.24 | **SYN probes** to ports 80, 445 and 3389 on those 6 hosts only (18 SYNs, `Win=1024`, MSS-only, as in LAB 14) |
| 667 | 12:12:18 | `POST /api/v2/report` to the C2 |

Results seen on the wire, and the report the implant sent:

| Host | 80 | 445 | 3389 |
|---|---|---|---|
| `10.20.0.10` FS01 | **open** | **open** | closed (RST) |
| `10.20.0.20` intranet | **open** | closed | closed |
| `10.20.0.1`, `.2` | closed | closed | closed |
| `10.20.0.31`, `.52` (workstations) | filtered (no reply) | filtered | filtered |

```json
{"id":"WS-FIN-07","open":["10.20.0.10:80","10.20.0.10:445","10.20.0.20:80"]}
```

**Interpretation:**

- The scan used ARP first, so it touched only machines that exist. This is consistent with a tool working inside the local segment, where ARP is the fastest way to find live hosts.
- The report matches the SYN/ACK replies in the capture exactly, which links the scan and the report to the same actor.
- The workstations' host firewalls dropped the probes, showing the `filtered` vs `closed` difference from LAB 14 on a real target set.

### 4.4 Collection and exfiltration

At 12:19:03 the C2 sent the second order:

```text
frame 837   {"cmd":"collect","args":"http://fs01.acme.lab/financeiro/clientes_2026.csv"}
```

| Frame | Time (UTC) | Event |
|---|---|---|
| 848 → 1021 | 12:19:05 | `GET http://fs01.acme.lab/financeiro/clientes_2026.csv` with `Cookie: fs_session=4e7d21a9` → `200`, `text/csv`, **169,635 B** |
| 1217 | 12:19:17 | `POST /api/v2/upload?f=clientes_2026.csv` to `203.0.113.66:8080`, `application/octet-stream`, **169,635 B** |
| 1222 | 12:19:17 | C2 reply `{"ok":true,"bytes":169635}` |

Both bodies were extracted with **Export Objects → HTTP** and hashed:

```console
$ sha256sum clientes_2026.csv upload%3ff=clientes_2026.csv
c747877e640d4e7a801b89fe01a7e9864e0bc2ef6dadaac1a1f3df53217d31f6  clientes_2026.csv
c747877e640d4e7a801b89fe01a7e9864e0bc2ef6dadaac1a1f3df53217d31f6  upload%3ff=clientes_2026.csv
```

**Interpretation:**

- The file that left the network is **byte-identical** to the file taken from FS01 12 seconds earlier. The C2's own reply confirms the byte count.
- The file holds 2,400 (fictitious) customer records: name, e-mail, city, credit limit and last four card digits.
- The upload went to the same host and port as the beacons. This is the LAB 14 pattern (large outbound transfer to the beacon destination), now with the content proven.
- The request to FS01 carried a valid session cookie and the implant's User-Agent, not the browser's. This is consistent with the implant reusing the logged-in user's access. The user's normal browsing on this host never touched FS01 in the capture window.
- **Volume:** in the IPv4 Conversations table, `10.20.0.45 → 203.0.113.66` totals 190 kB out vs 15 kB back.

### 4.5 Scope

- No other workstation contacted `nfe-portal.example.com`, `cdn-sync.example.net`, `198.51.100.23` or `203.0.113.66`.
- `10.20.0.31` accessed FS01 twice (`/rh/escala_dezembro.txt`, its own session cookie, full Edge User-Agent). This is consistent with normal work and was not linked to the incident.
- The capture only shows traffic crossing the core switch. Activity inside WS-FIN-07 (persistence, other files read locally) cannot be seen here and needs endpoint forensics.

---

## 5. Timeline (UTC, 2026-11-27)

| Time | Frame | Event |
|---|---|---|
| 12:05:10 | 110 | WS-FIN-07 opens the fake invoice page on `nfe-portal.example.com` |
| 12:05:16 | 121 | Downloads `NF-e_38211.pdf.exe` (21,504 B) |
| 12:06:02 | 181 | First C2 check-in to `cdn-sync.example.net:8080` |
| 12:12:10 | 366 | C2 orders an internal scan |
| 12:12:14 – 12:12:15 | 372–663 | ARP sweep of `/24`, then SYN probes to 6 hosts |
| 12:12:18 | 667 | Scan results sent to the C2 |
| 12:19:03 | 837 | C2 orders collection of `clientes_2026.csv` |
| 12:19:05 | 848 | File downloaded from FS01 (169,635 B) |
| 12:19:17 | 1217 | Same file uploaded to the C2 (hash match) |
| 12:27 | — | Antivirus alert (from the case brief) |
| 12:29:45 | 1536 | Last check-in seen; implant still active |

Dwell time from infection to exfiltration: **about 14 minutes**.

---

## 6. Indicators of compromise

| Type | Value | Context |
|---|---|---|
| Domain | `nfe-portal.example.com` | Delivery site |
| IP | `198.51.100.23` | Delivery site |
| URL | `/download/NF-e_38211.pdf.exe` | Payload download |
| File | `NF-e_38211.pdf.exe`, SHA-256 `7b46f242…2d1d06` | Payload (inert in this scenario) |
| Domain | `cdn-sync.example.net` | C2 |
| IP:port | `203.0.113.66:8080` | C2 |
| URL paths | `/api/v2/ping?id=`, `/api/v2/report`, `/api/v2/upload?f=` | C2 protocol |
| User-Agent | `Mozilla/5.0 (Windows NT 10.0; Win64; x64)` (exact, truncated) | Implant |
| Behaviour | ~60 s ±15 % HTTP check-ins; ARP sweep of the full `/24` | Implant |

## 7. MITRE ATT&CK mapping

| Tactic | Technique | Evidence |
|---|---|---|
| Initial Access | T1566.002 Phishing: Spearphishing Link | Invoice landing page → download (inferred: the e-mail itself is not in the capture) |
| Execution | T1204.002 User Execution: Malicious File | Download followed 45 s later by the first beacon |
| Defense Evasion | T1036.007 Masquerading: Double File Extension | `.pdf.exe` |
| Command and Control | T1071.001 Application Layer Protocol: Web Protocols | HTTP C2 on 8080 |
| Discovery | T1018 Remote System Discovery; T1046 Network Service Discovery | ARP sweep; SYN probes |
| Collection | T1039 Data from Network Shared Drive | `clientes_2026.csv` from FS01 |
| Exfiltration | T1041 Exfiltration Over C2 Channel | `POST /api/v2/upload` to the C2 |

## 8. Recommendations

1. **Contain:** isolate WS-FIN-07 from the network now; the implant was still active at the end of the capture.
2. **Block** `198.51.100.23`, `203.0.113.66` and both domains at the firewall and DNS; search proxy, DNS and firewall logs for earlier contacts.
3. **Hunt** for the file hash and the exact User-Agent on all endpoints.
4. **Treat `clientes_2026.csv` as disclosed:** 2,400 customer records left the network. Involve legal and privacy (in Brazil, an LGPD incident assessment).
5. **Invalidate** the FS01 session `fs_session=4e7d21a9` and reset the user's credentials.
6. **Reduce exposure:** show file extensions on workstations; restrict outbound traffic to non-standard ports such as 8080; serve FS01 over HTTPS with per-share access control; alert on internal ARP sweeps.

## 9. Limitations

- This is a **synthetic scenario**: the traffic was generated, not recorded from real systems, and is cleaner than a real network. The analysis method is the same.
- Network evidence shows what crossed the wire. It cannot show what ran on the endpoint, how the user was lured (no e-mail in scope), or whether data left by another path outside the capture window.
- The C2 used cleartext HTTP, so content was readable. Over TLS, the same conclusions would rest on timing, sizes and destinations only (LAB 13, LAB 14).

---

## Reproduce / verify

```console
cd evidence
sha256sum -c SHA256SUMS                       # lab15-acme-incident.pcap: OK

# Regenerate the capture from the script (needs scapy) and compare
cd ../scenario && python3 generate_scenario.py
sha256sum lab15-acme-incident.pcap            # ee0a05d7...ceca
```

Key Wireshark filters: `frame contains "NF-e_38211"` · `http.request.uri contains "/api/v2/"` · `arp.opcode == 1 && arp.src.proto_ipv4 == 10.20.0.45` · `tcp.flags == 0x002 && ip.src == 10.20.0.45` · `http.request.method == "POST"`

**References:** NIST SP 800-61 (incident handling), NIST SP 800-86 (forensic techniques), RFC 3227 (evidence collection), MITRE ATT&CK, RFC 5737 and RFC 2606 (documentation addresses and names).
