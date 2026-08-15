#!/usr/bin/env python3
"""Asigna municipio POTAUS a centros sin municipio usando CP o texto de dirección."""
import json, re

DATA = "/root/centros_compatibles/data/centros.json"
centros = json.loads(open(DATA, encoding="utf-8").read())

# Rangos CP de municipios POTAUS (aproximado, verificado contra INE/Correos)
CP_MUN = [
    ("Sevilla", range(41001, 41021)),
    ("Dos Hermanas", {41700, 41701, 41702, 41703, 41704, 41089}),
    ("Alcalá de Guadaíra", {41500}),
    ("Utrera", {41710}),
    ("Mairena del Aljarafe", {41927}),
    ("La Rinconada", {41300, 41309}),
    ("Los Palacios y Villafranca", {41720}),
    ("Camas", {41900}),
    ("Tomares", {41940}),
    ("Bormujos", {41930}),
    ("Carmona", {41410}),
    ("Coria del Río", {41100}),
    ("San Juan de Aznalfarache", {41920}),
    ("Castilleja de la Cuesta", {41950}),
    ("Albaida del Aljarafe", {41809}),
    ("Alcalá del Río", {41200}),
    ("La Algaba", {41980}),
    ("Aznalcázar", {41849}),
    ("Aznalcóllar", {41870}),
    ("Brenes", {41310}),
    ("Carrión de los Céspedes", {41820}),
    ("Espartinas", {41807}),
    ("Gerena", {41860}),
    ("Guillena", {41210}),
    ("Huévar del Aljarafe", {41830}),
    ("Isla Mayor", {41140}),
    ("Mairena del Alcor", {41510}),
    ("Olivares", {41804}),
    ("Palomares del Río", {41928}),
    ("Pilas", {41840}),
    ("La Puebla del Río", {41130}),
    ("Salteras", {41909}),
    ("Sanlúcar la Mayor", {41800}),
    ("Santiponce", {41970}),
    ("Umbrete", {41806}),
    ("Valencina de la Concepción", {41907}),
    ("Villamanrique de la Condesa", {41850}),
    ("Villanueva del Ariscal", {41808}),
    ("El Viso del Alcor", {41520}),
    ("Almensilla", {41111}),
    ("Benacazón", {41805}),
    ("Bollullos de la Mitación", {41110}),
    ("Castilleja de Guzmán", {41908}),
    ("Castilleja del Campo", {41810}),
    ("Gelves", {41120}),
    ("Gines", {41960}),
]

def cp_a_municipio(cp):
    if not cp: return None
    cp = int(cp)
    for mun, rng in CP_MUN:
        if cp in rng:
            return mun
    return None

def texto_a_municipio(texto):
    if not texto: return None
    t = texto.lower()
    for mun, _ in CP_MUN:
        if mun.lower() in t:
            return mun
    return None

asignados = 0
for c in centros:
    if c.get("municipio"):
        continue
    cp = c.get("cp") or (re.search(r"\b(\d{5})\b", c.get("direccion_completa") or "") or [None, None])[1]
    mun = cp_a_municipio(cp) if cp else None
    if not mun:
        mun = texto_a_municipio(c.get("direccion_completa") or "") or texto_a_municipio(c.get("nombre") or "")
    if mun:
        c["municipio"] = mun
        asignados += 1

with open(DATA, "w", encoding="utf-8") as f:
    json.dump(centros, f, ensure_ascii=False, indent=2)

from collections import Counter
sin = [c for c in centros if not c.get("municipio")]
print(f"Asignados: {asignados} | Quedan sin municipio: {len(sin)}")
for c in sin[:12]:
    print(f"  {c['nombre'][:45]:47s} | {(c.get('direccion_completa') or '')[:40]}")
