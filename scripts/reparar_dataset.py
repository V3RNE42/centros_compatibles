#!/usr/bin/env python3
"""reparar_dataset.py — repara el dataset tras el fix_coords_raras fallido:
1. Regenera IDs únicos (9 colisiones sev-9xxx)
2. Restaura SAINT GABRIEL EDUARDO DATO -> municipio Sevilla + dirección limpia
3. English Connection (#73) -> municipio Carmona (coords en Carmona, Calle Sinaí)
4. Kids&Us Sevilla: re-geocodifica con query precisa (República Argentina, Los Remedios)
5. Elimina duplicado Kids&Us Sevilla Este (sev-9180, sin coords, duplicado de sev-9182)
6. Corrige dirección SAINT GABRIEL (nº 22, 41018 Sevilla)"""
import json, time, urllib.parse, urllib.request
from collections import Counter

DATA = "/root/centros_compatibles/data/centros.json"
UA = {"User-Agent": "censo-academias-sevilla/1.0 (contacto@ejemplo.es)"}

def nominatim(q, limit=2):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "json", "limit": limit, "addressdetails": 1, "countrycodes": "es"})
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

centros = json.load(open(DATA, encoding="utf-8"))

# 1) IDs únicos: reasignar todos los sev-9xxx secuencialmente
ids_usados = set(c["id"] for c in centros)
cont = 9000
for c in centros:
    if c["id"].startswith("sev-9"):
        while f"sev-{cont}" in ids_usados:
            cont += 1
        c["id"] = f"sev-{cont}"
        ids_usados.add(c["id"])
        cont += 1
print("1. IDs regenerados (únicos):", len(ids_usados), "| total centros:", len(centros))

# 2) SAINT GABRIEL EDUARDO DATO -> Sevilla + dirección limpia
for c in centros:
    n = (c.get("nombre") or "").upper()
    if "SAINT GABRIEL EDUARDO DATO" in n:
        c["municipio"] = "Sevilla"
        c["direccion"] = "Avenida Eduardo Dato, 22"
        c["direccion_completa"] = "Avenida Eduardo Dato, 22, 41018 Sevilla"
        c["cp"] = "41018"
        print(f"2. {c.get('nombre')} -> Sevilla, dir corregida")

# 3) English Connection #73 -> Carmona
for c in centros:
    n = (c.get("nombre") or "").strip()
    if n == "English Connection" and c.get("lat"):
        c["municipio"] = "Carmona"
        print(f"3. English Connection ({c['lat']},{c['lng']}) -> Carmona (Calle Sinaí, 30)")

# 4) Kids&Us Sevilla -> re-geocodificar (República Argentina está en Los Remedios)
for c in centros:
    n = (c.get("nombre") or "").strip()
    if n == "Kids&Us Sevilla" and "República Argentina" in (c.get("direccion") or ""):
        # coords actuales 37.139,-6.176 = Isla Mayor (MAL). Query con distrito.
        try:
            res = nominatim("Avenida República Argentina, Los Remedios, Sevilla")
            time.sleep(1.1)
            if res:
                c["lat"] = float(res[0]["lat"]); c["lng"] = float(res[0]["lon"])
                c["municipio"] = "Sevilla"
                c["geocod_metodo"] = "NOMINATIM"
                print(f"4. Kids&Us Sevilla -> {c['lat']},{c['lng']} ({res[0].get('display_name','')[:60]})")
            else:
                # fallback: coords conocidas de Los Remedios (República Argentina ~37.377,-5.996)
                c["lat"], c["lng"] = 37.3769, -5.9959
                c["municipio"] = "Sevilla"
                c["geocod_metodo"] = "MANUAL_REFERENCIA"
                print(f"4. Kids&Us Sevilla -> fallback Los Remedios {c['lat']},{c['lng']}")
        except Exception as e:
            print(f"4. ERROR {e}")

# 5) Eliminar Kids&Us Sevilla Este duplicado (sin coords, id sev-9180 original)
antes = len(centros)
centros = [c for c in centros if not (c.get("id") == "sev-9180")]
print(f"5. Eliminado duplicado sev-9180 (Kids&Us Sevilla Este sin coords): {antes} -> {len(centros)}")

# renumera
centros.sort(key=lambda c: (c.get("nombre_raw") or c.get("nombre") or "").lower())
for i, c in enumerate(centros, 1):
    c["numero"] = i

# verificación final de ids
ids = Counter(c["id"] for c in centros)
dups = {k: v for k, v in ids.items() if v > 1}
print(f"\nFINAL: {len(centros)} centros | ids duplicados: {len(dups)}")
if dups:
    print("  DUPS:", dups)

json.dump(centros, open(DATA, "w"), ensure_ascii=False, indent=2)
print("Guardado.")
