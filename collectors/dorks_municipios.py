#!/usr/bin/env python3
"""collectors/dorks_municipios.py — Fase 2: dorks léxicos por municipio vía Google News RSS.
Busca 'academia de inglés {MUNICIPIO}' y 'escuela de idiomas {MUNICIPIO}' para los
municipios sin cobertura. Los resultados son pistas de descubrimiento, no confirmación.
"""
import json, re, time, urllib.request, urllib.parse, os

OUT = "/root/centros_compatibles/raw"
os.makedirs(OUT, exist_ok=True)

FALTAN = ["Los Palacios y Villafranca","Coria del Río","Albaida del Aljarafe","La Algaba","Aznalcázar","Aznalcóllar","Brenes","Carrión de los Céspedes","Gerena","Guillena","Huévar del Aljarafe","Isla Mayor","Olivares","Palomares del Río","La Puebla del Río","Salteras","Santiponce","Umbrete","Valencina de la Concepción","Villamanrique de la Condesa","Villanueva del Ariscal","Almensilla","Benacazón","Castilleja de Guzmán","Castilleja del Campo","Gelves"]

def gnews(q):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q, "hl": "es", "gl": "ES", "ceid": "ES:es"})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:
        return None

def parse(rss):
    items = re.findall(r"<item>(.*?)</item>", rss, re.S)
    out = []
    for it in items:
        t = re.search(r"<title>(.*?)</title>", it, re.S)
        l = re.search(r"<link>(.*?)</link>", it, re.S)
        d = re.search(r"<pubDate>(.*?)</pubDate>", it, re.S)
        if t:
            out.append({"titulo": t.group(1).strip(), "link": l.group(1).strip() if l else None,
                        "fecha": d.group(1).strip() if d else None})
    return out

resultados = []
for mun in FALTAN:
    for q in [f'"academia de inglés" {mun}', f'"escuela de idiomas" {mun}', f'"academia de idiomas" {mun}']:
        rss = gnews(q)
        if rss:
            items = parse(rss)
            for it in items:
                resultados.append({**it, "query": q, "municipio": mun})
            print(f"{mun} [{q.split(' ')[0]}]: {len(items)} noticias")
        time.sleep(1.2)

with open(f"{OUT}/dorks_municipios_{time.strftime('%Y%m%d')}.jsonl", "w") as f:
    for r in resultados:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"\nTotal pistas de noticias: {len(resultados)}")
# resumen por municipio con resultados
from collections import Counter
por_mun = Counter(r["municipio"] for r in resultados)
for mun, n in por_mun.most_common():
    print(f"  {mun}: {n}")
