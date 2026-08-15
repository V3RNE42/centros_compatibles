#!/usr/bin/env python3
"""auditoria_coords_v2.py — reverse-geocode de TODOS los centros con coords.
Solo reporta los que NO cuadran: municipio real (city/town/village) != municipio
declarado. Sin falsos positivos por 'state' (comunidad autónoma)."""
import json, time, urllib.parse, urllib.request

DATA = "/root/centros_compatibles/data/centros.json"
UA = {"User-Agent": "censo-academias-sevilla/1.0 (contacto@ejemplo.es)"}

def reverse(lat, lng):
    u = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1&zoom=10"
    r = urllib.request.Request(u, headers=UA)
    return json.load(urllib.request.urlopen(r, timeout=30))

def norm(s):
    if not s: return ""
    s = s.lower()
    for a, b in (("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n"),("ü","u")):
        s = s.replace(a, b)
    return " ".join(s.split())

# municipios que son pedanías/entidades menores de Sevilla capital o del ámbito
PEDANIAS_SEVILLA = {"torre de la reina", "guillena"}  # Torre de la Reina pertenece a Guillena

centros = json.load(open(DATA, encoding="utf-8"))
problemas = []
n = 0
for c in centros:
    lat, lng = c.get("lat"), c.get("lng")
    if lat is None or lng is None:
        continue
    n += 1
    try:
        rev = reverse(lat, lng)
        ad = rev.get("address", {})
        mun_real = ad.get("city") or ad.get("town") or ad.get("village") or ad.get("municipality") or ""
        mun_dec = c.get("municipio") or ""
        nr, nd = norm(mun_real), norm(mun_dec)
        if nr and nd and nr != nd:
            problemas.append((c, mun_real))
        time.sleep(0.9)
    except Exception as e:
        print(f"ERROR reverse #{c.get('numero')}: {e}")
        time.sleep(0.9)

print(f"Revisados: {n} con coordenadas")
print(f"\n=== DESCUADRES MUNICIPIO REAL vs DECLARADO ({len(problemas)}) ===")
for c, mr in problemas:
    print(f"  #{c.get('numero'):3d} | {str(c.get('nombre_raw') or c.get('nombre'))[:42]:42s} | declara:{c.get('municipio')} | real:{mr} | {c.get('lat')},{c.get('lng')}")
