#!/usr/bin/env python3
"""punto_en_provincia.py — verifica cada centro de data/centros.json contra el
polígono real de la provincia de Sevilla (relación OSM 349008, INE 41).
Salida: centros FUERA de la provincia (por coordenadas), con distancia al límite."""
import json, sys
import osmium

PBF = "/tmp/andalucia.osm.pbf"
DATA = "/root/centros_compatibles/data/centros.json"
REL_PROVINCIA = 349008

# Pasada 1: recoger los ways outer de la provincia
class WaysHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.outer_way_ids = set()
        self.inner_way_ids = set()
    def relation(self, r):
        if r.id == REL_PROVINCIA:
            for m in r.members:
                if m.type == "w":
                    if m.role == "outer":
                        self.outer_way_ids.add(m.ref)
                    elif m.role == "inner":
                        self.inner_way_ids.add(m.ref)

wh = WaysHandler()
wh.apply_file(PBF)
print(f"ways outer: {len(wh.outer_way_ids)}, inner: {len(wh.inner_way_ids)}")

# Pasada 2: geometrías de esos ways (coordenadas de nodos)
class GeoHandler(osmium.SimpleHandler):
    def __init__(self, way_ids):
        super().__init__()
        self.way_ids = way_ids
        self.ways = {}  # way_id -> [(lat, lng), ...]
    def way(self, w):
        if w.id in self.way_ids:
            self.ways[w.id] = [(n.lat, n.lon) for n in w.nodes if n.location.valid()]

gh = GeoHandler(wh.outer_way_ids | wh.inner_way_ids)
gh.apply_file(PBF)
print(f"ways con geometría: {len(gh.ways)} / {len(wh.outer_way_ids | wh.inner_way_ids)}")

# Ensamblar anillos: encadenar ways por nodos extremos
def ensamblar_anillos(ways):
    """Une ways que comparten nodos extremos en anillos cerrados."""
    usados = set()
    anillos = []
    for wid, coords in ways.items():
        if wid in usados or not coords:
            continue
        anillo = list(coords)
        usados.add(wid)
        # crecer hacia delante
        while True:
            ext = anillo[-1]
            for wid2, coords2 in ways.items():
                if wid2 in usados or not coords2:
                    continue
                if coords2[0] == ext:
                    anillo.extend(coords2[1:]); usados.add(wid2); break
                elif coords2[-1] == ext:
                    anillo.extend(reversed(coords2[:-1])); usados.add(wid2); break
            else:
                break
        # crecer hacia atrás
        while True:
            ext = anillo[0]
            for wid2, coords2 in ways.items():
                if wid2 in usados or not coords2:
                    continue
                if coords2[-1] == ext:
                    anillo = list(coords2[:-1]) + anillo; usados.add(wid2); break
                elif coords2[0] == ext:
                    anillo = list(reversed(coords2[1:])) + anillo; usados.add(wid2); break
            else:
                break
        if len(anillo) >= 4 and anillo[0] == anillo[-1]:
            anillos.append(anillo)
        else:
            anillos.append(anillo)  # igual lo guardamos (abierto = límite truncado)
    return anillos

anillos = ensamblar_anillos(gh.ways)
print(f"anillos ensamblados: {len(anillos)}, tamaños: {sorted((len(a) for a in anillos), reverse=True)[:5]}")

# Point-in-polygon (ray casting)
def punto_en_anillo(lat, lng, anillo):
    dentro = False
    j = len(anillo) - 1
    for i in range(len(anillo)):
        yi, xi = anillo[i]
        yj, xj = anillo[j]
        if ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            dentro = not dentro
        j = i
    return dentro

def punto_en_provincia(lat, lng):
    # el anillo más largo es el perímetro exterior
    exterior = max(anillos, key=len)
    if not punto_en_anillo(lat, lng, exterior):
        return False
    # agujeros (inner / otros anillos)
    for a in anillos:
        if a is exterior:
            continue
        if punto_en_anillo(lat, lng, a):
            return False
    return True

# Distancia aproximada (haversine) del punto al anillo exterior
from math import radians, sin, cos, sqrt, atan2
def dist_hav(a, b):
    R = 6371000
    la1, lo1, la2, lo2 = map(radians, [a[0], a[1], b[0], b[1]])
    dla, dlo = la2 - la1, lo2 - lo1
    h = sin(dla/2)**2 + cos(la1)*cos(la2)*sin(dlo/2)**2
    return 2*R*asin(sqrt(h))

def dist_al_limite(lat, lng):
    ext = max(anillos, key=len)
    return min(dist_hav((lat, lng), (la, lo)) for la, lo in ext)

centros = json.load(open(DATA, encoding="utf-8"))
fuera = []
dentro = 0
sin_coords = []
for c in centros:
    lat, lng = c.get("lat"), c.get("lng")
    if lat is None or lng is None:
        sin_coords.append(c)
        continue
    if punto_en_provincia(lat, lng):
        dentro += 1
    else:
        d = dist_al_limite(lat, lng)
        fuera.append((c, d))

print(f"\nDENTRO: {dentro} | FUERA: {len(fuera)} | SIN COORDS: {len(sin_coords)}")
print("\n=== FUERA DE LA PROVINCIA ===")
for c, d in sorted(fuera, key=lambda x: -x[1]):
    print(f"  {c.get('numero'):3d} | {c.get('nombre','')[:50]:50s} | {c.get('municipio')} | {c.get('direccion','')[:40]} | dist={d/1000:.1f} km")
print("\n=== SIN COORDENADAS (38) — municipio asignado ===")
from collections import Counter
print(Counter(c.get('municipio') for c in sin_coords))
