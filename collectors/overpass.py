#!/usr/bin/env python3
"""collectors/overpass.py — Q1-Q4 del plan §5.5. Descarga y parsea a JSONL."""
import json, time, urllib.request, urllib.parse, os

BBOX = "37.05,-6.45,37.68,-5.62"
OUT = "/root/centros_compatibles/raw"
os.makedirs(OUT, exist_ok=True)

QUERIES = {
    "q1_language_school": f'''
[out:json][timeout:180];
(
  nwr["amenity"="language_school"]({BBOX});
);
out center tags;''',
    "q2_lexico": f'''
[out:json][timeout:300];
(
  nwr["name"~"[Aa]cademia.*[Ii]ngl[eé]s|[Ii]ngl[eé]s.*[Aa]cademia",i]({BBOX});
  nwr["name"~"[Ii]diomas",i]({BBOX});
  nwr["name"~"[Ee]nglish",i]({BBOX});
  nwr["name"~"[Ll]anguage",i]({BBOX});
  nwr["name"~"[Ss]chool of [Ee]nglish",i]({BBOX});
);
out center tags;''',
    "q3_educativo": f'''
[out:json][timeout:300];
(
  nwr["amenity"="prep_school"]({BBOX});
  nwr["office"="educational_institution"]({BBOX});
  nwr["amenity"="training"]({BBOX});
  nwr["shop"="educational"]({BBOX});
  nwr["amenity"="school"]["school:subject"~"language|english",i]({BBOX});
);
out center tags;''',
}

def run(name, q):
    url = "https://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({"data": q}).encode()
    req = urllib.request.Request(url, data=data)
    req.add_header("User-Agent", "censo-academias-sevilla/1.0 (julio@cabanillas.dev)")
    for intento in range(4):
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            print(f"{name}: intento {intento+1} falló ({e}); esperando...")
            time.sleep(15 * (intento + 1))
    return None

def clean(e):
    tags = e.get("tags", {})
    c = e.get("center") or e.get("lat") and {"lat": e.get("lat"), "lon": e.get("lon")} or {}
    return {
        "osm_type": e.get("type"),
        "osm_id": e.get("id"),
        "nombre": tags.get("name"),
        "direccion": tags.get("addr:street") and f"{tags.get('addr:street','')}, {tags.get('addr:housenumber','')}".strip(", ") or None,
        "cp": tags.get("addr:postcode"),
        "municipio": tags.get("addr:city"),
        "telefono": tags.get("phone"),
        "web": tags.get("website") or tags.get("contact:website"),
        "email": tags.get("email") or tags.get("contact:email"),
        "lat": c.get("lat"),
        "lng": c.get("lon"),
        "osm_tags": {k: v for k, v in tags.items() if k in ("amenity","office","shop","name","operator","brand")},
    }

all_rows = []
for name, q in QUERIES.items():
    res = run(name, q)
    if res is None:
        print(f"{name}: FALLÓ tras 4 intentos")
        continue
    elems = res.get("elements", [])
    rows = [clean(e) for e in elems if e.get("tags", {}).get("name")]
    all_rows.extend(rows)
    with open(f"{OUT}/overpass_{name}.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{name}: {len(rows)} elementos")
    time.sleep(8)

# dedupe por (nombre, municipio) aproximado
vistos = set()
unicos = []
for r in all_rows:
    key = (r["nombre"] or "").lower().strip(), (r["municipio"] or "").lower().strip(), round(r["lat"] or 0, 3), round(r["lng"] or 0, 3)
    if key in vistos:
        continue
    vistos.add(key)
    unicos.append(r)

with open(f"{OUT}/overpass_todos.jsonl", "w") as f:
    for r in unicos:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"TOTAL únicos: {len(unicos)}")
