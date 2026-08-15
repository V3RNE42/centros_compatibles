#!/usr/bin/env python3
"""filtro_provincia_v2.py — verificación fiable: polígono de la provincia de Sevilla
vía Nominatim (rel OSM 349008) + reverse-geocode de cada centro con coordenadas
para confirmar que el municipio real coincide con el declarado."""
import json, time, urllib.parse, urllib.request
from shapely.geometry import shape, Point

DATA = "/root/centros_compatibles/data/centros.json"
UA = {"User-Agent": "censo-academias-sevilla/1.0 (contacto@ejemplo.es)"}

# 1) polígono fiable
url = "https://nominatim.openstreetmap.org/lookup?osm_ids=R349008&format=json&polygon_geojson=1"
req = urllib.request.Request(url, headers=UA)
res = json.load(urllib.request.urlopen(req, timeout=60))
prov = shape(res[0]["geojson"])
print(f"provincia: {prov.geom_type} | área km²: {round(prov.area*111.32*111.32,1)} | bounds: {tuple(round(x,3) for x in prov.bounds)}")

def reverse(lat, lng):
    u = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1&zoom=10"
    r = urllib.request.Request(u, headers=UA)
    return json.load(urllib.request.urlopen(r, timeout=30))

centros = json.load(open(DATA, encoding="utf-8"))
fuera = []
descuadrados = []
dentro = 0
sin_coords = []
for c in centros:
    lat, lng = c.get("lat"), c.get("lng")
    if lat is None or lng is None:
        sin_coords.append(c)
        continue
    pt = Point(lng, lat)
    if not (prov.contains(pt) or prov.boundary.distance(pt) < 1e-6):
        fuera.append(c)
        continue
    dentro += 1
    # reverse-geocode para confirmar municipio
    try:
        rev = reverse(lat, lng)
        ad = rev.get("address", {})
        mun_real = ad.get("city") or ad.get("town") or ad.get("village") or ad.get("municipality") or ""
        mun_dec = c.get("municipio") or ""
        # normalizar comparación
        def norm(s):
            s = s.lower().replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").replace("ñ","n").replace("ü","u")
            return " ".join(s.split())
        if mun_real and mun_dec and norm(mun_real) not in norm(mun_dec) and norm(mun_dec) not in norm(mun_real) and norm(mun_real) not in ("sevilla","sevilla provincia"):
            # excepción: Sevilla capital a veces devuelve distrito
            if "sevilla" not in norm(mun_dec) or "sevilla" not in norm(mun_real):
                descuadrados.append((c, mun_real))
        time.sleep(1.05)
    except Exception as e:
        pass

print(f"\nDENTRO: {dentro} | FUERA: {len(fuera)} | SIN COORDS: {len(sin_coords)}")
print("\n=== FUERA DEL POLÍGONO ===")
for c in sorted(fuera, key=lambda x: (x.get('municipio') or '')):
    print(f"  {c.get('numero'):3d} | {str(c.get('nombre'))[:45]:45s} | {c.get('municipio')} | {c.get('lat')},{c.get('lng')}")
print("\n=== DENTRO PERO MUNICIPIO REAL DIFERENTE ===")
for c, mun in descuadrados:
    print(f"  {c.get('numero'):3d} | {str(c.get('nombre'))[:45]:45s} | declara:{c.get('municipio')} | real:{mun} | {c.get('lat')},{c.get('lng')}")
json.dump({"fuera": [c.get("id") for c in fuera], "descuadrados": [c.get("id") for c, _ in descuadrados]},
          open("/tmp/coords_raras.json", "w"))
