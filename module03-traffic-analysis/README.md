# Module 03 — Network Traffic Analysis

`Status: In progress`

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
| LAB 14 — Suspicious Patterns | Port scan, beaconing, exfiltration-like transfers | ⬜ Planned |
| LAB 15 — Investigation Challenge | Analyse a mixed PCAP and write a technical report | ⬜ Planned |

---

## Key takeaways

- **Traffic shows what the software did, not what the user intended.** One click produced two connections; a cached revisit produced a 304 with no content.
- **Packet loss has a signature** (duplicate ACKs → fast retransmissions) that shows loss, not its cause.
- **The capture point shapes the evidence:** a sender-side capture misses locally dropped packets and shows unsplit TSO frames.
- **Hash only after the capture process has exited.**
- **Cleartext HTTP exposes credentials, session cookies and whole files;** a file rebuilt from a capture can be hash-matched to the original.
- **A session cookie authenticates on its own,** so stealing it is as good as stealing the password.
- **HTTPS hides the content, not the envelope:** site name (SNI), timing, volume and client fingerprint stay visible. Decryption needs keys taken from an endpoint.
