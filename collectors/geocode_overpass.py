#!/usr/bin/env python3
"""Geocodifica los centros Overpass sin municipio via Nominatim (1 req/s) y asigna municipio POTAUS."""
import json, time, urllib.request, urllib.parse, re

# 46 municipios POTAUS (para matching)
POTAUS = ["Sevilla","Dos Hermanas","Alcalá de Guadaíra","Utrera","Mairena del Aljarafe","La Rinconada",
"Los Palacios y Villafranca","Camas","Tomares","Bormujos","Carmona","Coria del Río","San Juan de Aznalfarache",
"Castilleja de la Cuesta","Albaida del Aljarafe","Alcalá del Río","La Algaba","Aznalcázar","Aznalcóllar","Brenes",
"Carrión de los Céspedes","Espartinas","Gerena","Guillena","Huévar del Aljarafe","Isla Mayor","Mairena del Alcor",
"Olivares","Palomares del Río","Pilas","La Puebla del Río","Salteras","Sanlúcar la Mayor","Santiponce","Umbrete",
"Valencina de la Concepción","Villamanrique de la Condesa","Villanueva del Ariscal","El Viso del Alcor","Almensilla",
"Benacazón","Bollullos de la Mitación","Castilleja de Guzmán","Castilleja del Campo","Gelves","Gines"]

def geo(lat, lng):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=jsonv2&accept-language=es"
    req = urllib.request.Request(url, headers={"User-Agent": "censo-academias-sevilla/1.0 (julio@cabanillas.dev)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode())
        addr = d.get("address", {})
        return addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality")
    except Exception as e:
        print("  err:", e)
        return None

rows = [json.loads(l) for l in open("/root/centros_compatibles/raw/overpass_todos.jsonl")]
out = []
for i, r in enumerate(rows):
    if not r.get("municipio"):
        if r.get("lat") is not None:
            mun = geo(r["lat"], r["lng"])
            r["municipio"] = mun
            print(f"[{i+1}/{len(rows)}] {r['nombre'][:40]:42s} -> {mun}")
            time.sleep(1.1)
    out.append(r)

# clasificar dentro/fuera POTAUS
def mun_norm(m):
    if not m: return None
    m = m.replace("Sevilla (ciudad)","Sevilla").strip()
    for p in POTAUS:
        if m.lower() == p.lower() or p.lower() in m.lower():
            return p
    return None

dentro = [r for r in out if mun_norm(r.get("municipio"))]
fuera  = [r for r in out if not mun_norm(r.get("municipio"))]
print(f"\nDENTRO POTAUS: {len(dentro)} | FUERA/desconocido: {len(fuera)}")
with open("/root/centros_compatibles/raw/overpass_potaus.jsonl","w") as f:
    for r in dentro:
        r["municipio_potaus"] = mun_norm(r.get("municipio"))
        f.write(json.dumps(r, ensure_ascii=False)+"\n")
print("\n=== DENTRO POTAUS ===")
for r in sorted(dentro, key=lambda x: x["municipio_potaus"]):
    print(f"{r['nombre'][:42]:44s} | {r['municipio_potaus'][:22]:24s} | {(r['web'] or '')[:32]}")
