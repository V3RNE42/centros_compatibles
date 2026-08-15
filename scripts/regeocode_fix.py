#!/usr/bin/env python3
"""regeocode_fix.py — re-geocodifica centros con coordenadas erróneas (fuera de la
provincia) y asigna municipio a los que no lo tienen, usando Nominatim (1 req/s)."""
import json, time, urllib.parse, urllib.request

DATA = "/root/centros_compatibles/data/centros.json"
UA = {"User-Agent": "censo-academias-sevilla/1.0 (contacto@ejemplo.es)"}

def nominatim(q, limit=1):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "json", "limit": limit, "addressdetails": 1})
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def reverse(lat, lng):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

centros = json.load(open(DATA, encoding="utf-8"))
cambios = 0

for c in centros:
    # 1) re-geocodificar los 6 con coords fuera (lat/lng claramente fuera del rango de Sevilla)
    lat, lng = c.get("lat"), c.get("lng")
    fuero = lat is not None and not (36.7 < lat < 38.4 and -6.8 < lng < -4.5)
    if fuero:
        q = " ".join(x for x in [c.get("direccion"), c.get("municipio"), "Sevilla", "España"] if x)
        print(f"[{c.get('numero')}] {c.get('nombre')}: coords {lat},{lng} ERRÓNEAS -> re-geocodificando '{q}'")
        try:
            res = nominatim(q)
            time.sleep(1.1)
            if res:
                c["lat"] = float(res[0]["lat"]); c["lng"] = float(res[0]["lon"])
                ad = res[0].get("address", {})
                if c.get("municipio") is None:
                    c["municipio"] = ad.get("city") or ad.get("town") or ad.get("village") or ad.get("municipality")
                c["geocod_metodo"] = "NOMINATIM"
                c["flags"] = [f for f in c.get("flags", []) if f != "SIN_COORDENADAS"]
                print(f"   -> {c['lat']},{c['lng']} | municipio: {c.get('municipio')}")
                cambios += 1
            else:
                print("   -> SIN RESULTADO; lat/lng a None")
                c["lat"] = None; c["lng"] = None
                c.setdefault("flags", []).append("SIN_COORDENADAS")
        except Exception as e:
            print(f"   -> ERROR {e}; lat/lng a None")
            c["lat"] = None; c["lng"] = None
            c.setdefault("flags", []).append("SIN_COORDENADAS")
    # 2) asignar municipio a Jr English School (sin municipio, con coords válidas)
    if not c.get("municipio") and c.get("lat") and c.get("lng"):
        print(f"[{c.get('numero')}] {c.get('nombre')}: sin municipio -> reverse de {c['lat']},{c['lng']}")
        try:
            rev = reverse(c["lat"], c["lng"])
            time.sleep(1.1)
            ad = rev.get("address", {})
            c["municipio"] = ad.get("city") or ad.get("town") or ad.get("village") or ad.get("municipality")
            print(f"   -> municipio: {c.get('municipio')}")
            cambios += 1
        except Exception as e:
            print(f"   -> ERROR {e}")

json.dump(centros, open(DATA, "w"), ensure_ascii=False, indent=2)
print(f"\nCambios: {cambios}")
