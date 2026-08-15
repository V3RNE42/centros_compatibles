#!/usr/bin/env python3
"""merge_sources.py — construye data/centros.json canónico desde:
baseline_70.json + raw/overpass_potaus.jsonl + raw/aceia_sevilla.jsonl
+ raw/kidsus_sevilla.jsonl + raw/helendoron_sevilla.jsonl
Aplica: asignación de marca EC, corrección de propagación (D2/D3), dedup.
"""
import json, re, unicodedata
from pathlib import Path

ROOT = Path("/root/centros_compatibles")
RAW = ROOT / "raw"

def norm(s):
    if not s: return ""
    s = s.lower().strip()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def norm_nucleo(s):
    s = norm(s)
    RUIDO = r"\b(sevilla|sevile|centro|centro de idiomas|academia de idiomas|academia|idiomas|english|school|academy|escuela|colegio|oficial|s l|s a|c b|institute|language|learners|kids|us|lc|ls|ih|clic)\b"
    s = re.sub(RUIDO, " ", s)
    return re.sub(r"\s+", " ", s).strip()

# ── 1. Baseline (70 fichas existentes) ──
baseline = json.loads((ROOT / "baseline_70.json").read_text(encoding="utf-8"))
for f in baseline:
    f["id"] = f"sev-{f['numero']:04d}"
    f["marca_id"] = "english_connection" if "english connection" in norm(f["nombre_raw"]) else None
    f["fuente_origen"] = "BASELINE"
    f["estado"] = "ACTIVO"
    f["confianza"] = "MEDIA"
    f["fuentes"] = [{"source": "BASELINE_REPO", "fecha_captura": "2026-08-15", "campos": ["nombre","telefono","direccion","web","email"]}]
    f["n_fuentes_independientes"] = 1
    # normalizar dirección: Seville -> Sevilla (D9)
    if f.get("direccion_raw"):
        f["direccion_completa"] = f["direccion_raw"].replace("Seville", "Sevilla")
        f["direccion_raw"] = f["direccion_completa"]
    f["nombre_normalizado"] = norm(f["nombre_raw"])
    f["telefono"] = f.get("telefono_raw")
    f["web"] = f.get("web_raw")
    f["email"] = f.get("email_raw")

# Corrección D2/D3: limpiar emails/direcciones propagados (solo baseline; los nuevos ya vienen limpios)
# - email @carmelitassevilla.es en 5 fichas de colegios distintos: dejar solo el legítimo
# - dirección C/ Bailén 32 en 3 municipios distintos: propagación
EMAILS_PROPAGADOS = {"secretaria@carmelitassevilla.es", "secretaria@colegiosanjosesevilla.com"}
def municipio_de(f):
    d = f.get("direccion_raw") or ""
    parts = [p.strip() for p in d.split(",") if p.strip()]
    if parts and re.match(r"^\d{5}", parts[-1]):
        parts = parts[:-1]
    return norm(parts[-1]) if parts else ""

# localizar la ficha legítima por dirección
legit = {}
for f in baseline:
    if f.get("email_raw") in EMAILS_PROPAGADOS:
        m = municipio_de(f)
        legit.setdefault(f["email_raw"], {}).setdefault(m, f["id"])

for f in baseline:
    em = f.get("email_raw") or ""
    if em in EMAILS_PROPAGADOS and legit.get(em, {}).get(municipio_de(f)) != f["id"]:
        f["email"] = None
        f["email_raw"] = None
        f.setdefault("flags", []).append("EMAIL_PROPAGADO_LIMPIADO")

# dirección C/ Bailén 32 (3 fichas, municipios distintos) → limpiar 2
por_dir = {}
for f in baseline:
    d = norm(f.get("direccion_raw") or "")
    if "bailen" in d and "32" in d:
        por_dir.setdefault(d, []).append(f)
for d, grupo in por_dir.items():
    if len(grupo) > 1:
        # conservar la primera (Sevilla), limpiar el resto
        for f in grupo[1:]:
            f["direccion_completa"] = None
            f.setdefault("flags", []).append("DIRECCION_PROPAGADA_LIMPIADA")

# ── 2. Fuentes nuevas ──
nuevos = []
def leer(path):
    p = RAW / path
    if not p.exists(): return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

for r in leer("overpass_potaus.jsonl"):
    nombre = r.get("nombre") or ""
    # filtrar ruido: no-academias evidentes
    if any(x in norm(nombre) for x in ("baile", "música", "sanitaria", "oposiciones", "animación", "deporte", "solares", "unidad de movilidad")):
        continue
    nuevos.append({
        "id": None, "nombre": nombre, "nombre_raw": nombre,
        "nombre_normalizado": norm(nombre),
        "municipio": r.get("municipio_potaus"), "cp": r.get("cp"),
        "direccion": r.get("direccion"), "direccion_completa": r.get("direccion"),
        "lat": r.get("lat"), "lng": r.get("lng"),
        "telefono": r.get("telefono"), "web": r.get("web"), "email": r.get("email"),
        "marca_id": None, "estado": "ACTIVO", "confianza": "BAJA",
        "fuente_origen": "OVERPASS",
        "fuentes": [{"source": "OSM_OVERPASS", "fecha_captura": "2026-08-15", "campos": [k for k in ("nombre","lat","lng","telefono","web") if r.get(k)]}],
        "n_fuentes_independientes": 1,
        "flags": [],
    })

for r in leer("aceia_sevilla.jsonl"):
    nombre = r.get("nombre") or ""
    # filtrar fuera de ámbito POTAUS por municipio mencionado en el nombre
    fuera = ("Lebrija", "Osuna", "Tocina", "Écija", "El Cuervo", "El Saucejo", "Saucejo")
    if any(x.lower() in norm(nombre) for x in ("lebrija", "osuna", "tocina", "ecija", "el cuervo", "saucejo")):
        continue
    m = None
    # ACEIA da provincia Sevilla; municipio en el nombre o en dirección
    direc = r.get("direccion_aceia") or ""
    cp = re.search(r"\b(\d{5})\b", direc)
    nuevos.append({
        "id": None, "nombre": nombre, "nombre_raw": nombre,
        "nombre_normalizado": norm(nombre),
        "municipio": None, "cp": cp.group(1) if cp else None,
        "direccion": direc, "direccion_completa": direc or None,
        "lat": None, "lng": None,
        "telefono": r.get("telefono_aceia"), "web": r.get("web_aceia"), "email": r.get("email_aceia"),
        "marca_id": None, "estado": "ACTIVO", "confianza": "MEDIA",
        "fuente_origen": "ACEIA",
        "fuentes": [{"source": "ACEIA", "source_url": r.get("url_aceia"), "fecha_captura": "2026-08-15", "campos": [k for k in ("nombre","direccion","telefono","web") if r.get(k)]}],
        "n_fuentes_independientes": 1,
        "flags": [],
    })

for r in leer("kidsus_sevilla.jsonl"):
    nuevos.append({
        "id": None, "nombre": f"Kids&Us {r['sede']}", "nombre_raw": f"Kids&Us {r['sede']}",
        "nombre_normalizado": norm(f"kids us {r['sede']}"),
        "municipio": r.get("municipio", r["sede"].split(" - ")[0] if " - " in r["sede"] else "Sevilla"),
        "direccion": r.get("direccion"), "direccion_completa": r.get("direccion"),
        "lat": None, "lng": None, "telefono": r.get("telefono"),
        "web": "https://www.kidsandus.es/", "email": None,
        "marca_id": "kidsus", "estado": "ACTIVO", "confianza": "MEDIA",
        "fuente_origen": "KIDSUS",
        "fuentes": [{"source": "KIDSUS_LOCALIZADOR", "source_url": r.get("web"), "fecha_captura": "2026-08-15", "campos": ["nombre","direccion"]}],
        "n_fuentes_independientes": 1, "flags": [],
    })

for r in leer("helendoron_sevilla.jsonl"):
    nuevos.append({
        "id": None, "nombre": f"Helen Doron {r['sede']}", "nombre_raw": f"Helen Doron {r['sede']}",
        "nombre_normalizado": norm(f"helen doron {r['sede']}"),
        "municipio": r.get("municipio"), "cp": r.get("cp"),
        "direccion": r.get("direccion"), "direccion_completa": r.get("direccion"),
        "lat": None, "lng": None,
        "telefono": r.get("telefono"), "web": "https://helendoron.es/", "email": r.get("email"),
        "marca_id": "helendoron", "estado": "ACTIVO", "confianza": "MEDIA",
        "fuente_origen": "HELENDORON",
        "fuentes": [{"source": "HELENDORON_LOCATIONS", "source_url": "https://helendoron.es/locations/", "fecha_captura": "2026-08-15", "campos": ["nombre","direccion","cp","telefono","email"]}],
        "n_fuentes_independientes": 1, "flags": [],
    })

# ── 3. Deduplicación simple: nucleo nombre + municipio, o web idéntica ──
vistos = {}
for f in baseline:
    vistos[f["id"]] = f

def clave_dedup(f):
    nuc = norm_nucleo(f.get("nombre_normalizado") or f.get("nombre") or "")
    if not nuc:
        return norm(f.get("web") or f.get("direccion") or "")
    return nuc

indice = {}
for f in baseline:
    indice[clave_dedup(f)] = f["id"]

dups = 0
for n in nuevos:
    cl = clave_dedup(n)
    if cl and cl in indice:
        # fusionar: actualizar campos del existente si faltan
        exist = vistos[indice[cl]]
        for k in ("telefono", "web", "email", "direccion_completa", "lat", "lng"):
            if not exist.get(k) and n.get(k):
                exist[k] = n[k]
        exist.setdefault("flags", []).append("CONFIRMADO_2DA_FUENTE")
        exist["n_fuentes_independientes"] = exist.get("n_fuentes_independientes", 1) + 1
        dups += 1
    else:
        n["id"] = f"sev-{9000 + len(vistos)}"
        vistos[n["id"]] = n
        if cl:
            indice[cl] = n["id"]

# ── 4. Salida ──
centros = sorted(vistos.values(), key=lambda c: (c.get("nombre_normalizado") or c.get("nombre") or "").lower())
for i, c in enumerate(centros, 1):
    c["numero"] = i

(DATA := ROOT / "data").mkdir(exist_ok=True)
(DATA / "centros.json").write_text(json.dumps(centros, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"TOTAL centros: {len(centros)} | baseline: {len(baseline)} | nuevos añadidos: {len(centros)-len(baseline)} | dups fusionados: {dups}")

# resumen por fuente
from collections import Counter
print("Por fuente_origen:", dict(Counter(c["fuente_origen"] for c in centros)))
print("Con web:", sum(1 for c in centros if c.get("web")))
print("Con telefono:", sum(1 for c in centros if c.get("telefono")))
print("Con coords:", sum(1 for c in centros if c.get("lat")))
print("Con email:", sum(1 for c in centros if c.get("email")))
