#!/usr/bin/env python3
"""fix_coords_raras.py — corrige los 11 descuadres detectados + Kids&Us:
- Re-geocodifica baseline con coords que apuntan a otro municipio (dir correcta en Sevilla)
- Corrige municipio declarado cuando las coords son correctas pero el municipio no
- Elimina duplicados Kids&Us genéricos; completa sede Sevilla Este"""
import json, time, urllib.parse, urllib.request

DATA = "/root/centros_compatibles/data/centros.json"
UA = {"User-Agent": "censo-academias-sevilla/1.0 (contacto@ejemplo.es)"}

def nominatim(q):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "json", "limit": 1, "addressdetails": 1, "countrycodes": "es"})
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

centros = json.load(open(DATA, encoding="utf-8"))
by_id = {c["id"]: c for c in centros}

def regeo(c, query, municipio=None):
    """Re-geocodifica c con query; asigna municipio si se da."""
    print(f"  regeo #{c.get('numero')} {str(c.get('nombre_raw') or c.get('nombre'))[:40]}: '{query}'")
    try:
        res = nominatim(query)
        time.sleep(1.1)
        if res:
            c["lat"] = float(res[0]["lat"]); c["lng"] = float(res[0]["lon"])
            c["geocod_metodo"] = "NOMINATIM"
            ad = res[0].get("address", {})
            if municipio is None:
                c["municipio"] = ad.get("city") or ad.get("town") or ad.get("village") or ad.get("municipality")
            else:
                c["municipio"] = municipio
            c.setdefault("flags", [])
            c["flags"] = [f for f in c["flags"] if f not in ("SIN_COORDENADAS", "COORDENADAS_FUERA_MUNICIPIO")]
            print(f"    -> {c['lat']},{c['lng']} | municipio: {c['municipio']}")
        else:
            print("    -> SIN RESULTADO")
    except Exception as e:
        print(f"    -> ERROR {e}")
    time.sleep(1.1)

def set_municipio(c, m):
    c["municipio"] = m
    print(f"  #{c.get('numero')} {str(c.get('nombre_raw') or c.get('nombre'))[:40]} -> municipio {m} (coords ya correctas)")

# === 1. Baseline con coords erróneas (re-geocodificar desde dirección real) ===
regeo(by_id[[c["id"] for c in centros if c["numero"]==12][0]], "Calle San Juan de la Cruz 1, 41010 Sevilla")
regeo(by_id[[c["id"] for c in centros if c["numero"]==30][0]], "Calle San José 5, 41003 Sevilla")
regeo(by_id[[c["id"] for c in centros if c["numero"]==36][0]], "Avenida de la Ciencia 73, 41020 Sevilla")
regeo(by_id[[c["id"] for c in centros if c["numero"]==59][0]], "Carretera de Utrera km 4.5 Montequinto, Dos Hermanas, Sevilla")
regeo(by_id[[c["id"] for c in centros if c["numero"]==60][0]], "Calle Torneo 167, 41010 Sevilla", municipio="Sevilla")

# === 2. Coords correctas pero municipio declarado mal ===
# #19 Asunción (Carmona): nombre dice Carmona, coords en Carmona → municipio Carmona
set_municipio(by_id[[c["id"] for c in centros if c["numero"]==19][0]], "Carmona")
# #68 St. Angela: dirección dice Salteras, coords en Salteras → municipio Salteras
set_municipio(by_id[[c["id"] for c in centros if c["numero"]==68][0]], "Salteras")
# #84 CBS Bormujos: nombre y coords en Bormujos → municipio Bormujos
set_municipio(by_id[[c["id"] for c in centros if c["numero"]==84][0]], "Bormujos")
# #105 English Connection: coords en Carmona → municipio Carmona
set_municipio(by_id[[c["id"] for c in centros if c["numero"]==105][0]], "Carmona")

# === 3. Kids&Us ===
# #137 Sevilla: coords en Isla Mayor (mal) → re-geocodificar República Argentina
regeo(by_id[[c["id"] for c in centros if c["numero"]==137][0]], "Avenida de la República Argentina, Sevilla", municipio="Sevilla")
# #136 Mairena: coords correctas, municipio mal → Mairena
set_municipio(by_id[[c["id"] for c in centros if c["numero"]==136][0]], "Mairena del Aljarafe")
# #132/133/134 genéricos duplicados (mismas coords, sin dirección) → eliminar 2, el que quede = sede genérica Sevilla (no tiene dirección)
kids = [c for c in centros if c.get("id") in ("sev-9080","sev-9169","sev-9182")]
print(f"\nKids&Us genéricos duplicados: {[(k['id'], k.get('nombre'), k.get('municipio')) for k in kids]}")
# conservar uno con la dirección de Avenida de las Ciencias 17 (Sevilla Este) — la sede que falta
keep = kids[0]
keep["nombre"] = "Kids&Us Sevilla Este"
keep["direccion"] = "Avenida de las Ciencias 17, local 1, Sevilla"
keep["direccion_completa"] = "Avenida de las Ciencias 17, local 1, Sevilla"
keep["municipio"] = "Sevilla"
print(f"  -> conservado {keep['id']} como Kids&Us Sevilla Este (Avenida de las Ciencias 17)")
# re-geocodificar Sevilla Este
regeo(keep, "Avenida de las Ciencias 17, Sevilla", municipio="Sevilla")
# eliminar los otros 2
for k in kids[1:]:
    centros.remove(k)
    print(f"  -> eliminado {k['id']}")

# renumera
centros.sort(key=lambda c: (c.get("nombre_raw") or c.get("nombre") or "").lower())
for i, c in enumerate(centros, 1):
    c["numero"] = i

json.dump(centros, open(DATA, "w"), ensure_ascii=False, indent=2)
print(f"\nTOTAL: {len(centros)}")
