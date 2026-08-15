#!/usr/bin/env python3
"""collectors/overpass_municipios.py — Fase 2: barrido Overpass Q4 por municipio POTAUS.
Para cada uno de los 46 municipios, consulta por área administrativa (admin_level=8)
buscando: language_school, prep_school, office=educational_institution, training,
y nombre con léxico de idiomas. Rate limit 6s entre consultas (instancia pública).
"""
import json, time, urllib.request, urllib.parse, re, os

OUT = "/root/centros_compatibles/raw"
os.makedirs(OUT, exist_ok=True)

POTAUS = ["Sevilla","Dos Hermanas","Alcalá de Guadaíra","Utrera","Mairena del Aljarafe","La Rinconada",
"Los Palacios y Villafranca","Camas","Tomares","Bormujos","Carmona","Coria del Río","San Juan de Aznalfarache",
"Castilleja de la Cuesta","Albaida del Aljarafe","Alcalá del Río","La Algaba","Aznalcázar","Aznalcóllar","Brenes",
"Carrión de los Céspedes","Espartinas","Gerena","Guillena","Huévar del Aljarafe","Isla Mayor","Mairena del Alcor",
"Olivares","Palomares del Río","Pilas","La Puebla del Río","Salteras","Sanlúcar la Mayor","Santiponce","Umbrete",
"Valencina de la Concepción","Villamanrique de la Condesa","Villanueva del Ariscal","El Viso del Alcor","Almensilla",
"Benacazón","Bollullos de la Mitación","Castilleja de Guzmán","Castilleja del Campo","Gelves","Gines"]

QUERY_TMPL = '''
[out:json][timeout:120];
area["name"="{MUN}"]["admin_level"="8"]["boundary"="administrative"]->.mun;
(
  nwr["amenity"="language_school"](area.mun);
  nwr["amenity"="prep_school"](area.mun);
  nwr["office"="educational_institution"](area.mun);
  nwr["amenity"="training"](area.mun);
  nwr["name"~"[Ii]diomas|[Ii]ngl[eé]s|[Ee]nglish|[Ll]anguage|[Aa]cademy",i](area.mun);
);
out center tags;
'''

def run(mun):
    q = QUERY_TMPL.replace("{MUN}", mun)
    url = "https://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({"data": q}).encode()
    req = urllib.request.Request(url, data=data)
    req.add_header("User-Agent", "censo-academias-sevilla/1.0 (julio@cabanillas.dev)")
    for intento in range(4):
        try:
            with urllib.request.urlopen(req, timeout=150) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            print(f"  {mun}: intento {intento+1} falló ({e}); esperando {20*(intento+1)}s")
            time.sleep(20 * (intento + 1))
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
        "osm_tags": {k: v for k, v in tags.items() if k in ("amenity","office","shop","name","operator","brand","addr:city")},
    }

rows = []
for i, mun in enumerate(POTAUS):
    res = run(mun)
    if res is None:
        print(f"[{i+1}/{len(POTAUS)}] {mun}: FALLÓ")
        continue
    elems = res.get("elements", [])
    # solo elementos con nombre y que sean plausibles (no viviendas ni calles)
    valid = [e for e in elems if e.get("tags", {}).get("name") and e.get("type") in ("node","way","relation")]
    mrows = [clean(e, mun) for e in valid]
    rows.extend(mrows)
    print(f"[{i+1}/{len(POTAUS)}] {mun}: {len(mrows)} candidatos")
    time.sleep(6)

with open(f"{OUT}/overpass_municipios_{time.strftime('%Y%m%d')}.jsonl", "w") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

# dedupe
vistos = set()
unicos = []
for r in rows:
    key = (r["nombre"] or "").lower().strip(), (r["municipio"] or "").lower(), round(r["lat"] or 0, 3), round(r["lng"] or 0, 3)
    if key in vistos:
        continue
    vistos.add(key)
    unicos.append(r)

with open(f"{OUT}/overpass_municipios_todos.jsonl", "w") as f:
    for r in unicos:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"\nTOTAL candidatos por municipio: {len(unicos)}")
