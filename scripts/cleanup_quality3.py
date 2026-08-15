#!/usr/bin/env python3
"""Limpieza quirúrgica v3:
- Elimina SOLO falsos positivos nuevos (no baseline).
- Fusiona duplicados por dominio SOLO si comparten dirección normalizada o nombre-núcleo
  (regla del plan §6.5 paso 3: misma marca + misma dirección = mismo centro; misma marca
  + direcciones distintas = sedes distintas, NO fusionar).
"""
import json, re, unicodedata
from pathlib import Path

DATA = Path("/root/centros_compatibles/data/centros.json")
centros = json.loads(DATA.read_text(encoding="utf-8"))

def norm(s):
    if not s: return ""
    s = s.lower().strip()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def norm_nucleo(s):
    s = norm(s)
    RUIDO = r"\b(sevilla|sevile|centro|centro de idiomas|academia de idiomas|academia|idiomas|english|school|academy|escuela|colegio|oficial|s l|s a|c b|institute|language|learners|kids|us|lc|ls|ih|clic|el i|eli)\b"
    s = re.sub(RUIDO, " ", s)
    return re.sub(r"\s+", " ", s).strip()

def norm_dir(s):
    if not s: return ""
    s = norm(s)
    s = re.sub(r"\b(calle|cal|avda|avenida|av|plaza|paseo|carretera|camino|nº|num|numero)\b", " ", s)
    s = re.sub(r"\d{5}", "", s)
    s = re.sub(r"[^a-z\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

# 1. Falsos positivos NUEVOS
NO_INGLES = (
    "sanitario", "sanitaria", "jurídica", "juridica", "oposicion", "música", "música y danza",
    "baile", "danza", "animación 3d", "audiovisual", "deporte", "fitness", "informática",
    "autoescuela", "sol decathlon", "unidad de movilidad", "v-art", "cefoec", "naturalmente",
    "albéniz", "albeniz", "m10 centro", "centypol", "formatec", "okformación", "okformacion",
    "elcano", "cega", "aprobali", "victotia", "centro de apoyo", "centro educativo d.",
    "ceapro", "conoser", "san ildefonso", "mandarin centers", "t&t academia", "school of languages",
    "escuela de música",
)
# Overpass que SÍ son idiomas (whitelist de palabras que indican inglés/idiomas)
IDIOMAS = (
    "ingl", "english", "language", "idioma", "school", "academy", "kids", "world", "yes",
    "winners", "learn", "teb", "andrew", "go speak", "my english", "my castle", "giralda",
    "clic", "eli", "st. james", "st james", "ronan", "city school", "new language",
    "english house", "learning is fun", "my little", "afoban", "jr english", "british",
    "canadian", "instituto", "institute",
)

eliminados = []
keep = []
for c in centros:
    if c.get("fuente_origen") == "BASELINE":
        keep.append(c)
        continue
    n = (c.get("nombre") or "").lower()
    if any(k in n for k in NO_INGLES):
        eliminados.append(c)
        continue
    if c.get("fuente_origen") == "OVERPASS" and not any(k in n for k in IDIOMAS):
        eliminados.append(c)
        continue
    keep.append(c)

print(f"Eliminados (nuevos, sin evidencia): {len(eliminados)}")
for e in eliminados:
    print(f"  ✗ [{e.get('fuente_origen')}] {e.get('nombre')}")
centros = keep

# 2. Fusión por dominio + dirección/nombre (conservadora)
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
    vistos = []
    for c in grupo:
        cand = None
        dir_c = norm_dir(c.get("direccion_completa") or c.get("direccion") or "")
        nuc_c = norm_nucleo(c.get("nombre") or "")
        for v in vistos:
            dir_v = norm_dir(v.get("direccion_completa") or v.get("direccion") or "")
            nuc_v = norm_nucleo(v.get("nombre") or "")
            misma_dir = dir_c and dir_v and (dir_c == dir_v or dir_c[:20] == dir_v[:20])
            mismo_nuc = nuc_c and nuc_v and nuc_c == nuc_v
            if misma_dir or mismo_nuc:
                cand = v
                break
        if cand:
            for k in ("telefono","email","direccion_completa","lat","lng","web","cp"):
                if not cand.get(k) and c.get(k):
                    cand[k] = c[k]
            cand.setdefault("flags", []).append("DUPLICADO_FUSIONADO")
            cand["n_fuentes_independientes"] = cand.get("n_fuentes_independientes", 1) + 1
            centros.remove(c)
            fusionados += 1
        else:
            vistos.append(c)
print(f"Duplicados fusionados (conservador): {fusionados}")

centros.sort(key=lambda c: (c.get("nombre") or "").lower())
for i, c in enumerate(centros, 1):
    c["numero"] = i

DATA.write_text(json.dumps(centros, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nTOTAL FINAL: {len(centros)}")
