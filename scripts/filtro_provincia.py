#!/usr/bin/env python3
"""filtro_provincia.py — verifica cada centro de data/centros.json contra el
polígono de la provincia de Sevilla (Overpass rel 349008, INE 41) y devuelve
los que están FUERA (por coordenadas)."""
import json
from shapely.geometry import LineString, Polygon, MultiPolygon, Point
from shapely.ops import unary_union

DATA = "/root/centros_compatibles/data/centros.json"
GEOJSON = "/tmp/sevilla_prov.geojson"

d = json.load(open(GEOJSON))
r = [e for e in d["elements"] if e["type"] == "relation"][0]
mems = r["members"]

# líneas outer
lineas_outer = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
                for m in mems if m.get("role") == "outer" and "geometry" in m]
lineas_inner = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
                for m in mems if m.get("role") == "inner" and "geometry" in m]

# unir en un solo polígono (los ways comparten nodos → unary_union los encadena)
union = unary_union(lineas_outer)
print("tipo union:", union.geom_type)
if union.geom_type == "MultiLineString":
    # encadenar manualmente: polygonize falla si no hay anillo cerrado completo
    from shapely.ops import polygonize
    polys = list(polygonize(lineas_outer))
    print("poligonos polygonize:", len(polys))
    if polys:
        prov = unary_union(polys)
    else:
        raise SystemExit("No se pudo cerrar el polígono")
else:
    prov = Polygon(union)

# aplicar agujeros (inner)
if lineas_inner:
    inner_union = unary_union(lineas_inner)
    if inner_union.geom_type in ("Polygon", "MultiPolygon"):
        prov = prov.difference(inner_union)

print("provincia:", prov.geom_type, "| área km²:", round(prov.area * 111.32 * 111.32, 1))
print("bounds:", prov.bounds)

centros = json.load(open(DATA, encoding="utf-8"))
fuera = []
dentro = 0
sin_coords = []
for c in centros:
    lat, lng = c.get("lat"), c.get("lng")
    if lat is None or lng is None:
        sin_coords.append(c)
        continue
    pt = Point(lng, lat)
    if prov.contains(pt) or prov.boundary.distance(pt) < 1e-6:
        dentro += 1
    else:
        fuera.append(c)

print(f"\nDENTRO: {dentro} | FUERA: {len(fuera)} | SIN COORDS: {len(sin_coords)}")
print("\n=== FUERA DE LA PROVINCIA ===")
for c in sorted(fuera, key=lambda x: (x.get('municipio') or '')):
    print(f"  {c.get('numero'):3d} | {str(c.get('nombre'))[:50]:50s} | {c.get('municipio')} | {str(c.get('direccion'))[:45]} | {c.get('lat')},{c.get('lng')}")
json.dump([c.get("id") for c in fuera], open("/tmp/fuera_provincia_ids.json", "w"))
