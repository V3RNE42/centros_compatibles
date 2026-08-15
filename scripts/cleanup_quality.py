#!/usr/bin/env python3
"""Limpieza de calidad post-fusión:
1. Elimina falsos positivos (centros sin evidencia de inglés en nombre/web).
2. Fusiona duplicados por dominio web o nombre+municipio que el dedup inicial no captó.
"""
import json, re
from pathlib import Path

DATA = Path("/root/centros_compatibles/data/centros.json")
centros = json.loads(DATA.read_text(encoding="utf-8"))

# 1. Falsos positivos: el nombre no sugiere inglés/idiomas y no hay web de idiomas
#    (son ruido del barrido léxico de Overpass: prep_school, office=educational_institution, etc.)
NO_INGLES_NOMBRE = (
    "sanitario", "sanitaria", "jurídica", "oposicion", "música", "baile", "danza",
    "animación", "animacion", "audiovisual", "deporte", "fitness", "informática",
    "informatica", "autoescuela", "academias de arte", "academia de arte", "sol decathlon",
    "unidad de movilidad", "v-art", "cefoec", "naturalmente", "albéniz", "albeniz",
    "m10 centro", "centypol", "formatec", "okformación", "okformacion", "elcano",
    "cega", "aprobali", "victotia",
)
SOSPE_CHOSOS = ("Centro de Apoyo Escolar", "Centro Educativo D. José", "Centro De Estudios")

eliminados = []
for c in centros:
    n = (c.get("nombre") or "").lower()
    web = (c.get("web") or "").lower()
    es_idiomas = any(k in n for k in ("ingl", "english", "language", "idioma", "school", "academy",
                                      "kids", "helen doron", "berlitz", "inlingua", "wall street",
                                      "vaughan", "clic", "eli ", "eli ", "st. james", "st james",
                                      "notting hill", "giralda", "macarena", "norteamericano",
                                      "british", "international house", "ih ", "gospeak", "take english",
                                      "penny lane", "winchester", "abbla", "bls idiomas", "cbs",
                                      "the english", "my english", "my castle", "go speak", "afoban",
                                      "teb", "andrew", "ronan", "aprobali", "aprobalia", "world",
                                      "winners", "yes ", "yes!", "new language", "city school",
                                      "jr english", "learning is fun", "my little", "english house",
                                      "el centro de inglés", "premier", "willow", "real english",
                                      "american", "sanlúcar", "thompson", "carlos v", "english 1",
                                      "ingles a mano", "inglés a mano", "global english", "global home",
                                      "school of languages", "the english plaza", "english world",
                                      "helen doron", "kids&us", "kids us", "english connection",
                                      "english dos hermanas", "escuela idiomas", "academia de idiomas",
                                      "academia de inglés", "academia de ingles", "centro de idiomas",
                                      "escuela de idiomas", "escuela oficial"))
    if not es_idiomas:
        eliminados.append(c)
        continue
    # revisar el caso especial: ELI con nombre raro
    c["_keep"] = True

if eliminados:
    keep = [c for c in centros if not any(c is e for e in eliminados)]
    print(f"Eliminados por no-evidencia: {len(eliminados)}")
    for e in eliminados:
        print(f"  ✗ {e.get('nombre')}")
    centros = keep

# 2. Fusión de duplicados por dominio web
def dominio(w):
    if not w: return None
    m = re.search(r"https?://(?:www\.)?([^/]+)", w)
    return m.group(1).lower().rstrip(".") if m else None

por_dom = {}
for c in centros:
    d = dominio(c.get("web"))
    if d:
        por_dom.setdefault(d, []).append(c)

fusionados = 0
for d, grupo in por_dom.items():
    if len(grupo) < 2:
        continue
    # mismo dominio y mismo municipio → duplicado
    por_mun = {}
    for c in grupo:
        por_mun.setdefault(c.get("municipio"), []).append(c)
    for mun, sub in por_mun.items():
        if len(sub) < 2:
            continue
        # conservar el más completo, fusionar campos
        sub.sort(key=lambda c: sum(1 for k in ("web","telefono","email","direccion_completa","lat") if c.get(k)), reverse=True)
        base = sub[0]
        for dup in sub[1:]:
            for k in ("telefono","email","direccion_completa","lat","lng","web"):
                if not base.get(k) and dup.get(k):
                    base[k] = dup[k]
            base.setdefault("flags", []).append("DUPLICADO_FUSIONADO")
            base["n_fuentes_independientes"] = base.get("n_fuentes_independientes", 1) + 1
            centros.remove(dup)
            fusionados += 1

print(f"Duplicados fusionados por dominio: {fusionados}")

# 3. limpiar campos auxiliares
for c in centros:
    c.pop("_keep", None)
    if isinstance(c.get("flags"), list):
        c["flags"] = list(dict.fromkeys(c["flags"]))

# renumerar
centros.sort(key=lambda c: (c.get("nombre") or "").lower())
for i, c in enumerate(centros, 1):
    c["numero"] = i

DATA.write_text(json.dumps(centros, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nTOTAL FINAL: {len(centros)}")
