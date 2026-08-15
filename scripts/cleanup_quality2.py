#!/usr/bin/env python3
"""Limpieza quirúrgica: elimina SOLO falsos positivos nuevos (no baseline).
Conserva las 70 fichas originales + academias reales. Fusiona duplicados por dominio."""
import json, re
from pathlib import Path

DATA = Path("/root/centros_compatibles/data/centros.json")
centros = json.loads(DATA.read_text(encoding="utf-8"))

# Falsos positivos NUEVOS (fuente != BASELINE) sin evidencia de inglés
# = ruido del barrido léxico de Overpass (office=educational_institution, prep_school, etc.)
NO_INGLES = (
    "sanitario", "sanitaria", "jurídica", "juridica", "oposicion", "música", "música y danza",
    "baile", "danza", "animación 3d", "audiovisual", "deporte", "fitness", "informática",
    "autoescuela", "sol decathlon", "unidad de movilidad", "v-art", "cefoec", "naturalmente",
    "albéniz", "albeniz", "m10 centro", "centypol", "formatec", "okformación", "okformacion",
    "elcano", "cega", "aprobali", "victotia", "centro de apoyo", "centro educativo d.",
    "ceapro", "conoser", "san ildefonso", "mandarin centers", "t&t academia", "school of languages",
)

eliminados = []
keep = []
for c in centros:
    if c.get("fuente_origen") == "BASELINE":
        keep.append(c)  # nunca tocar las fichas originales (S2)
        continue
    n = (c.get("nombre") or "").lower()
    if any(k in n for k in NO_INGLES):
        eliminados.append(c)
        continue
    # regla del eje 3 (§7.1): sin evidencia de inglés en nombre, se descarta si viene de OVERPASS
    # (Overpass con amenity=prep_school/office=educational_institution es ruido sin nombre de idiomas)
    if c.get("fuente_origen") == "OVERPASS":
        es_idiomas = any(k in n for k in ("ingl", "english", "language", "idioma", "school", "academy",
                                           "kids", "world", "yes", "winners", "learn", "teb", "andrew",
                                           "go speak", "my english", "my castle", "giralda", "clic",
                                           "eli", "st. james", "st james", "ronan", "city school",
                                           "new language", "english house", "learning is fun",
                                           "my little", "afoban", "jr english"))
        if not es_idiomas:
            eliminados.append(c)
            continue
    keep.append(c)

if eliminados:
    print(f"Eliminados (nuevos, sin evidencia): {len(eliminados)}")
    for e in eliminados:
        print(f"  ✗ [{e.get('fuente_origen')}] {e.get('nombre')}")
    centros = keep

# Fusión de duplicados por dominio web
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
    por_mun = {}
    for c in grupo:
        por_mun.setdefault(c.get("municipio"), []).append(c)
    for mun, sub in por_mun.items():
        if len(sub) < 2:
            continue
        sub.sort(key=lambda c: sum(1 for k in ("web","telefono","email","direccion_completa","lat") if c.get(k)), reverse=True)
        base = sub[0]
        for dup in sub[1:]:
            for k in ("telefono","email","direccion_completa","lat","lng","web","cp"):
                if not base.get(k) and dup.get(k):
                    base[k] = dup[k]
            base.setdefault("flags", []).append("DUPLICADO_FUSIONADO")
            base["n_fuentes_independientes"] = base.get("n_fuentes_independientes", 1) + 1
            centros.remove(dup)
            fusionados += 1
print(f"Duplicados fusionados por dominio: {fusionados}")

# renumerar y ordenar
centros.sort(key=lambda c: (c.get("nombre") or "").lower())
for i, c in enumerate(centros, 1):
    c["numero"] = i

DATA.write_text(json.dumps(centros, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nTOTAL FINAL: {len(centros)}")
