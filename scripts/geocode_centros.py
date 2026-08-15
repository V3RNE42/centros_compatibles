#!/usr/bin/env python3
"""Geocodifica los centros de data/centros.json sin lat/lng usando Nominatim.
Solo los que tienen dirección o nombre+municipio. Rate limit 1.1s (obligatorio Nominatim).
"""
import json, re, time, urllib.request, urllib.parse

DATA = "/root/centros_compatibles/data/centros.json"
centros = json.loads(open(DATA, encoding="utf-8").read())

def geo(query):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({
        "q": query, "format": "jsonv2", "limit": 1, "accept-language": "es", "countrycodes": "es"})
    req = urllib.request.Request(url, headers={"User-Agent": "censo-academias-sevilla/1.0 (julio@cabanillas.dev)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode())
        if d:
            return float(d[0]["lat"]), float(d[0]["lon"])
    except Exception as e:
        print("  ERR", e)
    return None, None

pend = [c for c in centros if c.get("lat") is None]
print(f"Sin coords: {len(pend)}")
for i, c in enumerate(pend):
    query = None
    if c.get("direccion_completa"):
        query = c["direccion_completa"] + ", España"
    elif c.get("direccion"):
        query = c["direccion"] + ", España"
    elif (c.get("nombre") or c.get("nombre_raw")) and c.get("municipio"):
        query = f"{c.get('nombre') or c.get('nombre_raw')}, {c['municipio']}, España"
    if query:
        lat, lng = geo(query)
        if lat:
            c["lat"], c["lng"] = lat, lng
            print(f"[{i+1}/{len(pend)}] OK  {(c.get('nombre') or c.get('nombre_raw') or '?')[:40]:42s} ({lat:.5f},{lng:.5f})")
        else:
            print(f"[{i+1}/{len(pend)}] --  {(c.get('nombre') or c.get('nombre_raw') or '?')[:40]:42s} NO geocodificado")
    time.sleep(1.1)

with open(DATA, "w", encoding="utf-8") as f:
    json.dump(centros, f, ensure_ascii=False, indent=2)
print(f"\nCon coords tras geocodificar: {sum(1 for c in centros if c.get('lat'))}/{len(centros)}")
