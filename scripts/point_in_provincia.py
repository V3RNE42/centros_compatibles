#!/usr/bin/env python3
"""point_in_provincia.py — verifica que cada centro de data/centros.json
cae dentro del polígono de la provincia de Sevilla (admin_level=4, INE 41)
extraído del PBF de Andalucía. Salida: lista de centros FUERA de la provincia."""
import json, sys
import osmium

PBF = "/tmp/andalucia.osm.pbf"
DATA = "/root/centros_compatibles/data/centros.json"

class ProvinciaHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.rel = None  # relation id de la provincia de Sevilla
    def relation(self, r):
        if self.rel is not None:
            return
        t = r.tags
        if (t.get("boundary") == "administrative" and t.get("admin_level") == "4"
                and t.get("name") == "Sevilla" and t.get("ref") == "41"):
            self.rel = r.id

h = ProvinciaHandler()
h.apply_file(PBF)
print("Provincia Sevilla relation:", h.rel)
if h.rel is None:
    sys.exit("NO encontrada la relación de la provincia de Sevilla")
