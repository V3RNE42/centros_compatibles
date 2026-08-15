#!/usr/bin/env python3
"""collectors/overpass_municipios_v2.py — barrido por municipio con:
- escritura incremental (cada municipio se guarda al momento, no se pierde nada)
- timeout corto por consulta (60s) + reintentos
- salto de municipios que fallen sin bloquear el resto
"""
import json, time, urllib.request, urllib.parse, os, sys

OUT = "/root/centros_compatibles/raw"
os.makedirs(OUT, exist_ok=True)
SALIDA = f"{OUT}/overpass_municipios_v2.jsonl"
RESUMEN = f"{OUT}/overpass_municipios_v2_progress.json"

POTAUS = ["Sevilla","Dos Hermanas","Alcalá de Guadaíra","Utrera","Mairena del Aljarafe","La Rinconada",
"Los Palacios y Villafranca","Camas","Tomares","Bormujos","Carmona","Coria del Río","San Juan de Aznalfarache",
"Castilleja de la Cuesta","Albaida del Aljarafe","Alcalá del Río","La Algaba","Aznalcázar","Aznalcóllar","Brenes",
"Carrión de los Céspedes","Espartinas","Gerena","Guillena","Huévar del Aljarafe","Isla Mayor","Mairena del Alcor",
"Olivares","Palomares del Río","Pilas","La Puebla del Río","Salteras","Sanlúcar la Mayor","Santiponce","Umbrete",
"Valencina de la Concepción","Villamanrique de la Condesa","Villanueva del Ariscal","El Viso del Alcor","Almensilla",
"Benacazón","Bollullos de la Mitación","Castilleja de Guzmán","Castilleja del Campo","Gelves","Gines"]

QUERY_LIGHT = '''
[out:json][timeout:45];
area["name"="{MUN}"]["admin_level"="8"]["boundary"="administrative"]->.mun;
(
  nwr["amenity"="language_school"](area.mun);
  nwr["name"~"[Ii]diomas|[Ii]ngl[eé]s|[Ee]nglish|[Ll]anguage",i](area.mun);
);
out center tags;
'''

def run(mun):
    q = QUERY_LIGHT.replace("{MUN}", mun)
    url = "https://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({"data": q}).encode()
    req = urllib.request.Request(url, data=data)
    req.add_header("User-Agent", "censo-academias-sevilla/1.0 (julio@cabanillas.dev)")
    for intento in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if intento < 2:
                time.sleep(10 * (intento + 1))
    return None

def clean(e, mun):
    tags = e.get("tags", {})
    c = e.get("center") or {}
    return {
        "osm_type": e.get("type"), "osm_id": e.get("id"),
        "nombre": tags.get("name"), "municipio": mun, "municipio_potaus": mun,
        "direccion": tags.get("addr:street") and f"{tags.get('addr:street','')}, {tags.get('addr:housenumber','')}".strip(", ") or None,
        "cp": tags.get("addr:postcode"),
        "telefono": tags.get("phone"),
        "web": tags.get("website") or tags.get("contact:website"),
        "email": tags.get("email") or tags.get("contact:email"),
        "lat": c.get("lat"), "lng": c.get("lon"),
        "osm_tags": {k: v for k, v in tags.items() if k in ("amenity","office","shop","name","operator","brand")},
    }

# progreso previo
hechos = set()
if os.path.exists(RESUMEN):
    hechos = set(json.load(open(RESUMEN)))

f = open(SALIDA, "a", encoding="utf-8")
total = 0
for i, mun in enumerate(POTAUS):
    if mun in hechos:
        print(f"[{i+1}/{len(POTAUS)}] {mun}: ya hecho")
        continue
    res = run(mun)
    if res is None:
        print(f"[{i+1}/{len(POTAUS)}] {mun}: FALLÓ (skip)")
        hechos.add(mun)
        json.dump(sorted(hechos), open(RESUMEN, "w"))
        continue
    elems = res.get("elements", [])
    valid = [e for e in elems if e.get("tags", {}).get("name") and e.get("type") in ("node","way")]
    for e in valid:
        row = clean(e, mun)
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        total += 1
    f.flush()
    print(f"[{i+1}/{len(POTAUS)}] {mun}: {len(valid)} candidatos (acumulado {total})")
    hechos.add(mun)
    json.dump(sorted(hechos), open(RESUMEN, "w"))
    time.sleep(5)

f.close()
print(f"\nDONE. Total: {total}")
