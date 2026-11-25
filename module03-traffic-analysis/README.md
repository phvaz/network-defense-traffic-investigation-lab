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
| LAB 12 — HTTP: Following Streams and Extracting Files | Follow TCP Stream, Export Objects, cleartext content | ⬜ Planned |
| LAB 13 — TLS: Analysing What Cannot Be Read | Handshake, SNI, certificates, timing and volume | ⬜ Planned |
| LAB 14 — Suspicious Patterns | Port scan, beaconing, exfiltration-like transfers | ⬜ Planned |
| LAB 15 — Investigation Challenge | Analyse a mixed PCAP and write a technical report | ⬜ Planned |

---

## Key takeaways

- **Traffic shows what the software did, not what the user intended.** One click produced two connections; a cached revisit produced a 304 with no content.
- **Packet loss has a signature** (duplicate ACKs → fast retransmissions) that shows loss, not its cause.
- **The capture point shapes the evidence:** a sender-side capture misses locally dropped packets and shows unsplit TSO frames.
- **Hash only after the capture process has exited.**
