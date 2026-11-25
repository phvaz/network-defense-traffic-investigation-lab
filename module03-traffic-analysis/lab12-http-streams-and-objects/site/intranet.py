# LAB 12 lab-only fake intranet: login form (POST, cleartext HTTP) + file download.
# Runs on the isolated host-only network. Data in clientes.csv is fictitious.
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs
LOGIN = b"""<html><body><h2>Intranet ACME</h2>
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
HTTPServer(("0.0.0.0", 8080), Intranet).serve_forever()
