#!/usr/bin/env python3
"""Corrige el campo web_aceia: re-busca la web oficial real en cada ficha."""
import json, re, time, urllib.request

rows = [json.loads(l) for l in open("/root/centros_compatibles/raw/aceia_sevilla.jsonl")]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "censo-academias-sevilla/1.0 (julio@cabanillas.dev)"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return None

BLOCK = ("aceia.es","yoast","schema.org","facebook.com","twitter.com","linkedin.com","instagram.com",
         "youtube.com","vimeo.com","google.com","maps.google","wordpress.org","gmpg.org","w3.org",
         "addtoany","gravatar","pinterest","tiktok.com","wa.me","whatsapp","tel:","mailto:")

for r in rows:
    h = fetch(r["url_aceia"])
    if not h:
        continue
    # 1) enlaces <a href>
    for m in re.finditer(r'<a[^>]+href="(https?://[^"]+)"[^>]*>', h):
        w = m.group(1).rstrip("/")
        if any(b in w for b in BLOCK):
            continue
        r["web_aceia"] = w
        break
    if not r.get("web_aceia"):
        # 2) URLs en texto plano
        for m in re.finditer(r'https?://([a-z0-9\-]+\.)+[a-z]{2,}(?:/[^\s"<>]*)?', h):
            w = m.group(0).rstrip("/.,;")
            if any(b in w for b in BLOCK):
                continue
            r["web_aceia"] = w
            break
    # normalizar dirección (quitar colas)
    d = r.get("direccion_aceia") or ""
    d = re.sub(r"Datos de contacto.*$|Localizar en Google Maps.*$|Tel[eé]fono:.*$|Email:.*$", "", d).strip()
    r["direccion_aceia"] = d or None
    time.sleep(1.2)

with open("/root/centros_compatibles/raw/aceia_sevilla.jsonl", "w") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print("ACEIA con web real:", sum(1 for r in rows if r.get("web_aceia")))
for r in rows:
    if r.get("web_aceia"):
        print(f"  {r['nombre'][:40]:42s} -> {r['web_aceia']}")
