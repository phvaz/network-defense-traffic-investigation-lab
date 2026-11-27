#!/usr/bin/env python3
"""LAB 14 - lab-only fake "command and control" server.

Plays the attacker's side on the isolated host-only network:
  GET  /beacon   the fake implant checks in; answers "sleep" (no real command)
  POST /upload   receives a file (simulated exfiltration); stores nothing,
                 only prints its size and SHA-256 so it can be compared.

Run on Kali only, inside the lab network. Never expose it.
"""
import hashlib
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORTA = 8081


def agora():
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


class Central(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep the terminal quiet; we print our own lines

    def responder(self, texto):
        corpo = texto.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        if self.path.startswith("/beacon"):
            print(f"{agora()} beacon de {self.client_address[0]}", flush=True)
            self.responder("sleep\n")
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path.startswith("/upload"):
            tamanho = int(self.headers.get("Content-Length", 0))
            h = hashlib.sha256()
            falta = tamanho
            while falta > 0:
                bloco = self.rfile.read(min(65536, falta))
                if not bloco:
                    break
                h.update(bloco)
                falta -= len(bloco)
            print(f"{agora()} upload de {self.client_address[0]}: "
                  f"{tamanho} bytes, sha256 {h.hexdigest()}", flush=True)
            self.responder("ok\n")
        else:
            self.send_error(404)


if __name__ == "__main__":
    print(f"central ouvindo na porta {PORTA}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORTA), Central).serve_forever()
