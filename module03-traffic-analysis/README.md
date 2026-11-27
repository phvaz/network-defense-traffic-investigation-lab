# Module 03 — Network Traffic Analysis

`Status: Complete`

## Objective

Receive a PCAP and produce a technical analysis of the communications it contains.

## Scope

Packet capture · PCAP · TCP handshake and flags · retransmissions · DNS · HTTP · TLS handshake · conversations · Follow TCP Stream · display filters · protocol hierarchy · communication timelines.

**Investigative challenges:** a suspicious domain, scanning patterns, data transfer, possible C2 indicators, behaviour consistent with exfiltration.

**Limitation addressed explicitly:** the content of encrypted (TLS) traffic cannot be read directly. Analysis relies on metadata such as endpoints, timing, volume, SNI, and certificates.

**Main tool:** Wireshark.

---

## Labs

| Lab | Topic | Status |
|---|---|---|
| [**LAB 11 — TCP in Depth: Handshakes, Retransmissions and Capture Integrity**](lab11-tcp-in-depth/) | Handshake and teardown, ephemeral ports, browser side-traffic (favicon, 304, pre-connections), induced packet loss, duplicate ACKs and fast retransmission, capture-point artefacts, a hash taken too early | ✅ Complete |
| [**LAB 12 — HTTP: Reading Streams and Extracting Files**](lab12-http-streams-and-objects/) | Fake intranet login over cleartext HTTP; credentials and session cookie read with Follow TCP Stream; file rebuilt with Export Objects and hash-matched to the original; client headers as a (forgeable) profile | ✅ Complete |
| [**LAB 13 — TLS: What Encryption Hides and What Still Leaks**](lab13-tls-metadata/) | The LAB 12 login over HTTPS: SNI, timing, volume and JA4 visible without keys; content recovered with the browser key log; file hash-matched from inside TLS; 15 `Certificate Unknown` alerts explained; key log filtered before publishing | ✅ Complete |
| [**LAB 14 — Suspicious Patterns: Scan, Beaconing and Exfiltration**](lab14-suspicious-patterns/) | SYN scan blocked silently by the firewall (2,000 probes, 0 replies); 12 PowerShell check-ins to a fake C2 at 10.2 s intervals; 5 MiB upload with an 850:1 out/in ratio, hash-matched on both ends; a capture that missed 4 % of the upload | ✅ Complete |
| [**LAB 15 — Investigation Challenge: The ACME Incident**](lab15-investigation-challenge/) | Worked example on a synthetic, reproducible capture: phishing download, jittered HTTP beacon (a benign periodic look-alike ruled out), ARP sweep and port scan on C2 command, file pulled from a file server and exfiltrated to the C2 (hash-matched); timeline, IOCs, ATT&CK mapping, recommendations | ✅ Complete |

---

## Key takeaways

- **Traffic shows what the software did, not what the user intended.** One click produced two connections; a cached revisit produced a 304 with no content.
- **Packet loss has a signature** (duplicate ACKs → fast retransmissions) that shows loss, not its cause.
- **The capture point shapes the evidence:** a sender-side capture misses locally dropped packets and shows unsplit TSO frames.
- **Hash only after the capture process has exited.**
- **Cleartext HTTP exposes credentials, session cookies and whole files;** a file rebuilt from a capture can be hash-matched to the original.
- **A session cookie authenticates on its own,** so stealing it is as good as stealing the password.
- **HTTPS hides the content, not the envelope:** site name (SNI), timing, volume and client fingerprint stay visible. Decryption needs keys taken from an endpoint.
- **A report ties signals into a story:** order of events, matching hashes and C2 commands that precede each action turn separate patterns into one incident.
- **Attacks have shapes:** a scan fans out across ports, a beacon ticks like a clock, exfiltration flows one way. Each has innocent look-alikes; together on one host they make a case.
