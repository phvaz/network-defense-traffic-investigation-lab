# LAB 13 lab-only fake intranet over HTTPS (TLS). Same pages as LAB 12, now encrypted.
# Runs on the isolated host-only network. Needs cert.pem and key.pem in the same folder.
import ssl
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs
LOGIN = b"""<html><body><h2>Intranet ACME (HTTPS)</h2>
<form method="POST" action="/login">
Usuario: <input name="usuario"><br>
Senha: <input type="password" name="senha"><br>
<button>Entrar</button></form></body></html>"""
class Intranet(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(LOGIN)
        else:
            super().do_GET()
    def do_POST(self):
        tamanho = int(self.headers["Content-Length"])
        dados = parse_qs(self.rfile.read(tamanho).decode())
        nome = dados.get("usuario", [""])[0]
        pagina = f'<html><body><h2>Bem-vindo, {nome}</h2><a href="/clientes.csv">Baixar relatorio de clientes</a></body></html>'
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Set-Cookie", "sessao=7f3a9c21")
        self.end_headers()
        self.wfile.write(pagina.encode())
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain("cert.pem", "key.pem")
servidor = ThreadingHTTPServer(("0.0.0.0", 8443), Intranet)
servidor.socket = ctx.wrap_socket(servidor.socket, server_side=True, do_handshake_on_connect=False)
servidor.serve_forever()
