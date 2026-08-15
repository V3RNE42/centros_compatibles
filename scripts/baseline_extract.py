#!/usr/bin/env python3
"""baseline_extract.py — Fase 0 del plan OSINT academias Sevilla.
Convierte index.html en el dataset canónico de partida (baseline_70.json)
y aplica las reglas de detección de propagación del §7.3.
"""
import re, json
from bs4 import BeautifulSoup

HTML = "/root/centros_compatibles/index.html"
html = open(HTML, encoding="utf-8").read()
soup = BeautifulSoup(html, "html.parser")

# (a) fichas
fichas = {}
for card in soup.select("div.school-card"):
    num_el = card.select_one(".card-number")
    num = int(num_el.get_text(strip=True))
    name = card.select_one(".card-name").get_text(" ", strip=True)
    name = re.sub(r"^\s*%d\s*" % num, "", name).strip()
    phone_el = card.select_one(".card-phone")
    addr_el  = card.select_one(".card-addr")
    web_el   = card.select_one("a.link-chip")
    mail_el  = card.select_one(".email-chip")
    fichas[num] = {
        "numero": num,
        "nombre_raw": name,
        "telefono_raw": phone_el.get_text(" ", strip=True).replace("📞", "").strip() if phone_el else None,
        "direccion_raw": addr_el.get_text(" ", strip=True) if addr_el else None,
        "web_raw": web_el["href"] if web_el else None,
        "email_raw": mail_el.get("data-email") if mail_el else None,
    }

# (b) coordenadas
coords = {}
for m in re.finditer(
    r'\{\s*number:\s*(\d+),\s*name:\s*"([^"]*)",\s*area:\s*"([^"]*)",\s*lat:\s*(-?[\d.]+),\s*lng:\s*(-?[\d.]+)\s*\}',
    html):
    n = int(m.group(1))
    coords[n] = {"name_map": m.group(2), "area": m.group(3),
                 "lat": float(m.group(4)), "lng": float(m.group(5))}

for n, f in fichas.items():
    f.update(coords.get(n, {"lat": None, "lng": None, "area": None}))
    f["_sin_coordenadas"] = n not in coords

json.dump(list(fichas.values()), open("/root/centros_compatibles/baseline_70.json", "w"), ensure_ascii=False, indent=2)
print("fichas:", len(fichas), "| sin coords:", sorted(n for n in fichas if n not in coords))

# --- Detección de propagación (§7.3) ---
from collections import defaultdict

def norm_direccion(d):
    return re.sub(r"\s+", " ", d.strip().lower()).strip()

def todos_coords(a, b):
    return a.get("lat") is not None and b.get("lat") is not None

def haversine(lat1, lng1, lat2, lng2):
    from math import radians, sin, cos, asin, sqrt
    R = 6371000
    p1, p2 = radians(lat1), radians(lat2)
    dp = radians(lat2 - lat1)
    dl = radians(lng2 - lng1)
    h = sin(dp/2)**2 + cos(p1)*cos(p2)*sin(dl/2)**2
    return 2*R*asin(sqrt(h))

def combinaciones(grupo, n=2):
    for i in range(len(grupo)):
        for j in range(i+1, len(grupo)):
            yield grupo[i], grupo[j]

def norm_dominio(url):
    if not url: return None
    m = re.match(r"https?://([^/]+)", url)
    if not m: return None
    host = m.group(1).lower()
    if host.startswith("www."): host = host[4:]
    return host

def municipio_de_dir(d):
    # heurística: último token que no sea CP
    if not d: return None
    parts = [p.strip() for p in d.split(",") if p.strip()]
    if parts and re.match(r"^\d{5}$", parts[-1]):
        parts = parts[:-1]
    return parts[-1].lower() if parts else None

centros = []
for n, f in sorted(fichas.items()):
    f["id"] = f"sev-{n:04d}"
    f["municipio"] = municipio_de_dir(f["direccion_raw"]) or "?"
    centros.append(f)

flags = defaultdict(list)
# R1 — dirección idéntica en municipios distintos
por_dir = defaultdict(list)
for c in centros:
    if c.get("direccion_raw"):
        por_dir[norm_direccion(c["direccion_raw"])].append(c)
for dir_, grupo in por_dir.items():
    if len({municipio_de_dir(c["direccion_raw"]) for c in grupo}) > 1:
        for c in grupo:
            flags[c["id"]].append("DIRECCION_COMPARTIDA_MUNICIPIOS_DISTINTOS")

# R2 — email compartido
por_email = defaultdict(list)
for c in centros:
    if c.get("email_raw"):
        por_email[c["email_raw"].lower()].append(c)
for em, grupo in por_email.items():
    if len(grupo) < 2: continue
    municipios = {municipio_de_dir(c["direccion_raw"]) for c in grupo}
    if len(municipios) > 1:
        for c in grupo:
            flags[c["id"]].append("EMAIL_COMPARTIDO_MUNICIPIOS_DISTINTOS")

# R3 — dominio email vs web
for c in centros:
    if c.get("email_raw") and c.get("web_raw"):
        dom_email = c["email_raw"].split("@")[-1].lower()
        if norm_dominio(c["web_raw"]) and norm_dominio(c["web_raw"]) not in dom_email:
            flags[c["id"]].append("DOMINIO_EMAIL_NO_COINCIDE_WEB")

# R4 — teléfono compartido entre distantes
por_tel = defaultdict(list)
for c in centros:
    if c.get("telefono_raw"):
        por_tel[c["telefono_raw"]].append(c)
for tel, grupo in por_tel.items():
    if len(grupo) < 2: continue
    for a, b in combinaciones(grupo):
        if todos_coords(a, b) and haversine(a["lat"],a["lng"],b["lat"],b["lng"]) > 2000:
            flags[a["id"]].append("TELEFONO_COMPARTIDO_DISTANTE")
            flags[b["id"]].append("TELEFONO_COMPARTIDO_DISTANTE")

# R6 — sin coordenadas
for c in centros:
    if c.get("lat") is None:
        flags[c["id"]].append("SIN_COORDENADAS")

print("\n=== FLAGS DETECTADOS (§7.3) ===")
for c in centros:
    if flags.get(c["id"]):
        print(f"#{c['numero']:02d} {c['nombre_raw'][:45]:47s} -> {', '.join(flags[c['id']])}")

# Estadísticas propagación
print("\n=== RESUMEN ===")
print("emails compartidos:", {k: len(v) for k, v in por_email.items() if len(v) > 1})
print("direcciones compartidas:", {k: len(v) for k, v in por_dir.items() if len(v) > 1})
print("telefonos compartidos:", {k: len(v) for k, v in por_tel.items() if len(v) > 1})
