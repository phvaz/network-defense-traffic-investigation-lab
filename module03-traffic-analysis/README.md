# Module 03 — Network Traffic Analysis

`Status: Planned`

## Objective

Receive a PCAP and produce a technical analysis of the communications it contains.

## Scope

Packet capture · PCAP · TCP handshake and flags · retransmissions · DNS · HTTP · TLS handshake · conversations · Follow TCP Stream · display filters · protocol hierarchy · communication timelines.

**Investigative challenges:** a suspicious domain, scanning patterns, data transfer, possible C2 indicators, behaviour consistent with exfiltration.

**Limitation addressed explicitly:** the content of encrypted (TLS) traffic cannot be read directly. Analysis relies on metadata such as endpoints, timing, volume, SNI, and certificates.

**Main tool:** Wireshark.
