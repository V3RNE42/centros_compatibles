#!/usr/bin/env python3
"""Enriquece las fichas ACEIA: dirección, teléfono, web, email. Rate limit 1.5s.
robots.txt de aceia.es PERMITE /portfolio/ (solo bloquea wp-admin) — verificado 2026-08-15.
"""
import json, re, time, urllib.request

rows = [json.loads(l) for l in open("/root/centros_compatibles/raw/aceia_sevilla.jsonl")]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "censo-academias-sevilla/1.0 (julio@cabanillas.dev)"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:
        print("  ERR", url, e)
        return None

def limpiar(s):
    return re.sub(r"\s+", " ", s.replace("&#8211;", "-").replace("&#8217;", "'").replace("&nbsp;", " ")).strip()

def extraer(h):
    out = {}
    # dirección: patrones de calle
    m = re.search(r"(C/|Calle|Avda|Avenida|Paseo|Plaza|Camino|Carretera)[^<]{5,90}(?:&#8211;|-\s*)?\s*(\d{5})?", h)
    if m:
        out["direccion_aceia"] = limpiar(m.group(0))
    # teléfono 9 dígitos (fijo) o móvil
    tels = re.findall(r"(?<![\d])(9[0-8]\d{7}|6\d{8}|7[1-9]\d{7})(?![\d])", h)
    if tels:
        out["telefono_aceia"] = list(dict.fromkeys(tels))[0]
    # email
    em = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", h)
    if em:
        out["email_aceia"] = em[0]
    # web oficial: primer enlace externo no-aceia no-yoast no-schema
    ws = re.findall(r'<a[^>]+href="(https?://[^"]+)"[^>]*>', h)
    for w in ws:
        if any(x in w for x in ("aceia.es", "yoast", "schema.org", "facebook.com", "twitter", "linkedin", "instagram", "youtube.com", "google.com", "maps.google", "wordpress.org", "gmpg.org", "w3.org")):
            continue
        out["web_aceia"] = w.rstrip("/")
        break
    return out

for i, r in enumerate(rows):
    h = fetch(r["url_aceia"])
    if h:
        r.update(extraer(h))
    print(f"[{i+1}/{len(rows)}] {r['nombre'][:45]:47s} | {r.get('direccion_aceia','')[:45]:47s} | {r.get('telefono_aceia',''):10s} | {r.get('web_aceia','')[:35]}")
    time.sleep(1.5)

with open("/root/centros_compatibles/raw/aceia_sevilla.jsonl", "w") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

con_datos = sum(1 for r in rows if r.get("direccion_aceia") or r.get("telefono_aceia") or r.get("web_aceia"))
print(f"\nEnriquecidas: {con_datos}/{len(rows)} con algún dato")
