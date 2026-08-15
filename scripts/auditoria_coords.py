#!/usr/bin/env python3
"""auditoria_coords.py — barrido COMPLETO: reverse-geocode de TODOS los centros
con coordenadas y reporte de los que no cuadran con su municipio declarado.
Sin excepciones. Decide el problema: coordenada mala vs municipio mal declarado."""
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
        # provincia real
        prov_real = ad.get("state", "")
        if norm(mun_real) and norm(mun_dec) and norm(mun_real) != norm(mun_dec):
            problemas.append((c, mun_real, prov_real))
        elif "sevilla" not in norm(prov_real) and prov_real:
            problemas.append((c, mun_real, prov_real))
        time.sleep(1.0)
    except Exception as e:
        print(f"ERROR reverse {c.get('numero')} {c.get('nombre')}: {e}")
        time.sleep(1.0)

print(f"Revisados: {n} con coordenadas")
print(f"\n=== PROBLEMAS ({len(problemas)}) ===")
for c, mun_real, prov_real in problemas:
    print(f"  #{c.get('numero'):3d} | {str(c.get('nombre'))[:42]:42s} | declara:{c.get('municipio')} | real:{mun_real} ({prov_real}) | {c.get('lat')},{c.get('lng')}")

json.dump([{"id": c.get("id"), "numero": c.get("numero"), "nombre": c.get("nombre"),
            "municipio_declarado": c.get("municipio"), "municipio_real": mr, "provincia_real": pr}
           for c, mr, pr in problemas], open("/tmp/auditoria_coords.json", "w"), ensure_ascii=False, indent=2)
print("\nGuardado en /tmp/auditoria_coords.json")
