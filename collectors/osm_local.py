#!/usr/bin/env python3
"""collectors/osm_local.py v2 — procesa el PBF YA FILTRADO por osmium tags-filter.
"""
import json, re, os

PBF = "/tmp/andalucia_edu2.osm.pbf"
OUT = "/root/centros_compatibles/raw/osm_local_potaus.jsonl"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
BBOX = (36.98, -6.55, 37.72, -5.55)

import osmium

class Handler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.lex = re.compile(r"[Aa]cademia.*[Ii]ngl|ingl.*academia|[Ii]diomas|[Ee]nglish|[Ll]anguage school|[Ss]chool of english", re.I)

    def _check(self, tags, lat, lon):
        if lat is None or lon is None:
            return
        if not (BBOX[0] <= lat <= BBOX[2] and BBOX[1] <= lon <= BBOX[3]):
            return
        name = tags.get("name")
        if not name:
            return
        amenity = tags.get("amenity", "")
        is_lang = amenity == "language_school"
        is_lex = bool(self.lex.search(name))
        is_school = amenity in ("prep_school", "training")
        if not (is_lang or is_lex or is_school):
            return
        tags_dict = {k: v for k, v in tags}
        self.rows.append({
            "osm_type": "node",
            "nombre": name,
            "direccion": tags_dict.get("addr:street") and f"{tags_dict.get('addr:street','')}, {tags_dict.get('addr:housenumber','')}".strip(", ") or None,
            "cp": tags_dict.get("addr:postcode"),
            "telefono": tags_dict.get("phone"),
            "web": tags_dict.get("website") or tags_dict.get("contact:website"),
            "email": tags_dict.get("email") or tags_dict.get("contact:email"),
            "lat": lat, "lng": lon,
            "osm_tags": {k: v for k, v in tags_dict.items() if k in ("amenity","office","shop","name","operator","brand")},
        })

    def node(self, n):
        self._check(n.tags, n.location.lat if n.location else None, n.location.lon if n.location else None)

    def way(self, w):
        try:
            locs = [x.location for x in w.nodes if x.location]
            if not locs:
                return
            lat = sum(x.lat for x in locs) / len(locs)
            lon = sum(x.lon for x in locs) / len(locs)
            self._check(w.tags, lat, lon)
        except Exception:
            pass

h = Handler()
print("Procesando PBF filtrado...")
h.apply_file(PBF)

vistos = set()
unicos = []
for r in h.rows:
    key = (r["nombre"] or "").lower().strip(), round(r["lat"], 3), round(r["lng"], 3)
    if key in vistos:
        continue
    vistos.add(key)
    unicos.append(r)

with open(OUT, "w", encoding="utf-8") as f:
    for r in unicos:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"Candidatos OSM local en bbox POTAUS: {len(unicos)}")
for r in sorted(unicos, key=lambda x: x["nombre"]):
    print(f"  {r['nombre'][:45]:47s} | {(r['web'] or '')[:30]}")
