#!/usr/bin/env bash
# Redacts one IPv4 address from a capture, replacing it with a documentation
# address (RFC 5737). The original file is only read, never modified.
#
# Usage:   ./sanitize.sh <ip-to-redact> <original.pcapng> <sanitized.pcapng>
# Example: ./sanitize.sh 203.0.113.10 lab02-dns.pcapng lab02-dns-sanitized.pcapng
#
# The address being redacted is passed at run time on purpose, so it is never
# stored in this repository.
#
# Requirements: editcap and tshark (Wireshark), tcprewrite (apt install tcpreplay)

set -euo pipefail

ORIG_IP="$1"
IN="$2"
OUT="$3"
DOC_IP="198.51.100.53"

echo "[*] Original SHA-256 (before):"
sha256sum "$IN"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# tcprewrite works on pcap, so convert, rewrite, and convert back to pcapng.
editcap -F pcap "$IN" "$tmp/in.pcap"
tcprewrite --pnat="${ORIG_IP}/32:${DOC_IP}/32" --fixcsum -i "$tmp/in.pcap" -o "$tmp/out.pcap"
editcap -F pcapng "$tmp/out.pcap" "$OUT"

echo "[*] Original SHA-256 (after, must be identical):"
sha256sum "$IN"

echo "[*] Packets in original / sanitized (must match):"
echo "    $(tshark -r "$IN" | wc -l) / $(tshark -r "$OUT" | wc -l)"

echo "[*] Packets still containing ${ORIG_IP} (must be 0):"
echo "    $(tshark -r "$OUT" -Y "ip.addr==${ORIG_IP}" | wc -l)"

echo "[*] Packets now containing ${DOC_IP}:"
echo "    $(tshark -r "$OUT" -Y "ip.addr==${DOC_IP}" | wc -l)"

echo "[*] Sanitized SHA-256:"
sha256sum "$OUT"
