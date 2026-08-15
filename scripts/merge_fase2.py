#!/usr/bin/env python3
"""merge_fase2.py — integra los hallazgos de Fase 2 en data/centros.json:
1. overpass_municipios_todos.jsonl (barrido Q4 por municipio)
2. languagecert_partners.jsonl (red SevillaCert)
3. dorks_municipios (pistas — solo como nota, no altas directas)
Aplica el mismo dedup por nombre-núcleo + municipio y por web.
"""
import json, re, unicodedata
from pathlib import Path

ROOT = Path("/root/centros_compatibles")
RAW = ROOT / "raw"
DATA = ROOT / "data" / "centros.json"

def norm(s):
    if not s: return ""
    s = s.lower().strip()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def norm_nucleo(s):
    s = norm(s)
    RUIDO = r"\b(sevilla|sevile|centro|centro de idiomas|academia de idiomas|academia|idiomas|english|school|academy|escuela|colegio|oficial|s l|s a|c b|institute|language|learners|kids|us|lc|ls|ih|clic|el i|eli|sevilla|sevilla)\b"
    s = re.sub(RUIDO, " ", s)
    return re.sub(r"\s+", " ", s).strip()

def dominio(w):
    if not w: return None
    m = re.search(r"https?://(?:www\.)?([^/]+)", w)
    return m.group(1).lower().rstrip(".") if m else None

centros = json.loads(DATA.read_text(encoding="utf-8"))

# índice existente
indice_nuc = {}
indice_dom = {}
for c in centros:
    nuc = norm_nucleo(c.get("nombre") or "")
    if nuc:
        indice_nuc.setdefault(nuc, []).append(c)
    d = dominio(c.get("web"))
    if d:
        indice_dom.setdefault(d, []).append(c)

def buscar_duplicado(nombre, municipio, web):
    nuc = norm_nucleo(nombre)
    if nuc and nuc in indice_nuc:
        for c in indice_nuc[nuc]:
            if not municipio or not c.get("municipio") or c["municipio"] == municipio:
                return c
    d = dominio(web)
    if d and d in indice_dom:
        return indice_dom[d][0]
    return None

nuevos = []
def add(nombre, municipio=None, direccion=None, cp=None, web=None, telefono=None, email=None,
        marca=None, fuente="", source_url=None, lat=None, lng=None, certificacion=None):
    global nuevos
    dup = buscar_duplicado(nombre, municipio, web)
    if dup:
        for k, v in (("telefono", telefono), ("web", web), ("email", email), ("direccion_completa", direccion),
                     ("cp", cp), ("lat", lat), ("lng", lng)):
            if v and not dup.get(k):
                dup[k] = v
        if certificacion:
            dup.setdefault("certificadoras", [])
            if certificacion not in dup["certificadoras"]:
                dup["certificadoras"].append(certificacion)
        dup.setdefault("flags", []).append("CONFIRMADO_FASE2")
        dup["n_fuentes_independientes"] = dup.get("n_fuentes_independientes", 1) + 1
        return False
    n = {
        "id": f"sev-{9000+len(centros)+len(nuevos)}", "nombre": nombre, "nombre_raw": nombre,
        "nombre_normalizado": norm(nombre), "municipio": municipio, "cp": cp,
        "direccion": direccion, "direccion_completa": direccion, "lat": lat, "lng": lng,
        "telefono": telefono, "web": web, "email": email, "marca_id": marca,
        "estado": "ACTIVO", "confianza": "MEDIA", "fuente_origen": fuente,
        "fuentes": [{"source": fuente, "source_url": source_url, "fecha_captura": "2026-08-15",
                     "campos": [k for k,v in (("nombre",nombre),("direccion",direccion),("telefono",telefono),("web",web),("lat",lat)) if v]}],
        "n_fuentes_independientes": 1, "flags": [],
    }
    if certificacion:
        n["certificadoras"] = [certificacion]
    nuevos.append(n)
    nuc = norm_nucleo(nombre)
    if nuc:
        indice_nuc.setdefault(nuc, []).append(n)
    d = dominio(web)
    if d:
        indice_dom.setdefault(d, []).append(n)
    return True

# 1. Overpass por municipio (API) + OSM local (Geofabrik PBF)
fuera_ambito = ("burguillos", "almonte", "tocina", "lebrija", "osuna", "ecija", "saucejo", "cantillana", "el cuervo")
for src, path in (("OVERPASS_MUN", "overpass_municipios_v2.jsonl"), ("OSM_LOCAL", "osm_local_potaus.jsonl")):
    p = RAW / path
    if not p.exists():
        continue
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"{src}: {len(rows)} candidatos")
    NO = ("baile", "música", "música y danza", "sanitaria", "sanitario", "oposicion", "autoescuela",
          "informática", "fitness", "deporte", "animación", "audiovisual", "unidad de movilidad",
          "v-art", "cefoec", "naturalmente", "albéniz", "centypol", "formatec", "okformación", "elcano")
    IDIOMAS = ("ingl", "english", "language", "idioma", "school", "academy", "kids", "world", "yes",
               "winners", "learn", "teb", "andrew", "go speak", "my english", "my castle", "giralda",
               "clic", "eli", "st. james", "st james", "ronan", "city school", "new language",
               "english house", "learning is fun", "my little", "afoban", "jr english", "british",
               "canadian", "instituto", "institute", "abbla", "helen doron", "kids&us", "premier",
               "willow", "real english", "american", "thompson", "english 1", "ingles a mano", "teb",
               "bus idiomas", "winchester", "the english plaza", "english connection")
    cont = 0
    for r in rows:
        nombre = r.get("nombre") or ""
        n = norm(nombre)
        if any(x in n for x in fuera_ambito):
            continue
        if any(x in n for x in NO):
            continue
        if src == "OVERPASS_MUN" and not any(x in n for x in IDIOMAS):
            continue
        if add(nombre, municipio=r.get("municipio_potaus"), direccion=r.get("direccion"),
               cp=r.get("cp"), web=r.get("web"), telefono=r.get("telefono"), email=r.get("email"),
               fuente=src, source_url="https://overpass-api.de" if src == "OVERPASS_MUN" else "geofabrik:andalucia-latest.osm.pbf",
               lat=r.get("lat"), lng=r.get("lng")):
            cont += 1
    print(f"  nuevos {src}: {cont}")

# 2. LanguageCert partners
p = RAW / "languagecert_partners.jsonl"
if p.exists():
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"LanguageCert partners: {len(rows)}")
    cont = 0
    for r in rows:
        if add(r["nombre"], municipio=r.get("municipio"), direccion=r.get("direccion"),
               cp=r.get("cp"), fuente="SEVILLACERT_LANGUAGECERT",
               source_url="https://sevillacert.com/centros-preparadores-languagecert-en-sevilla/",
               certificacion="LanguageCert"):
            cont += 1
    print(f"  nuevos LanguageCert: {cont}")

# 3. Dorks: no altas directas (pistas de prensa, no confirmación), solo log
p = RAW / "dorks_municipios_20260815.jsonl"
if p.exists():
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"Dorks: {len(rows)} pistas de prensa (no altas directas — solo descubrimiento)")

centros.extend(nuevos)
centros.sort(key=lambda c: (c.get("nombre") or "").lower())
for i, c in enumerate(centros, 1):
    c["numero"] = i

DATA.write_text(json.dumps(centros, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nTOTAL: {len(centros)} (antes 167, nuevos Fase 2: {len(nuevos)})")
from collections import Counter
print("Por fuente:", dict(Counter(c["fuente_origen"] for c in centros)))
