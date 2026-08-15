#!/usr/bin/env python3
"""build_html.py — ÚNICA vía de escritura de index.html.
Lee data/centros.json (canónico) y genera fichas + mapLocations sincronizados.
Resuelve D1 por construcción: ficha y mapa salen del mismo registro.
"""
import json, re, html as htmlmod
from pathlib import Path

ROOT = Path("/root/centros_compatibles")
DATA = ROOT / "data" / "centros.json"
OUT = ROOT / "index.html"

def leer_plantilla():
    """Partes del index.html actual que NO se regeneran: head+css, y la cola JS."""
    h = (ROOT / "index.html").read_text(encoding="utf-8")
    # sección de cards: desde '<div class="cards-section"' (o 'cards-grid') hasta el cierre '</section>'
    start_marker = 'class="cards-section"'
    end_marker = '<!-- ===== MAP SECTION'
    i = h.find(start_marker)
    j = h.find(end_marker)
    if i == -1 or j == -1:
        # fallback: buscar 'cards-grid'
        i = h.find('class="cards-grid"')
        j = h.find('<section aria-labelledby="fallback-title"')
    head = h[:i]
    # quitar desde el inicio de la primera card hasta el final de la última + cierre
    first_card = head.find('<div class="school-card">')
    if first_card != -1:
        head = head[:first_card]
    tail = h[j:]
    return head, tail

def esc(s):
    return htmlmod.escape(str(s)) if s else ""

def card_html(c):
    web = c.get("web") or ""
    email = c.get("email") or ""
    nombre = c.get("nombre") or c.get("nombre_raw") or "?"
    telefono = c.get("telefono_display") or c.get("telefono_raw") or c.get("telefono") or ""
    direccion = c.get("direccion_completa") or c.get("direccion_raw") or ""
    num = c.get("numero")
    if web:
        web_html = f'<a class="link-chip" href="{esc(web)}" rel="noopener" target="_blank">{esc(web)}</a>'
    else:
        web_html = '<span class="link-chip" style="background:#f7f8fb;color:#999;border-color:#ddd;cursor:default;">no website found</span>'
    if email:
        email_html = f'<span class="email-chip" data-email="{esc(email)}" role="button" tabindex="0">{esc(email)}</span>'
    else:
        email_html = '<span class="email-chip" style="background:#f7f8fb;color:#999;border-color:#ddd;cursor:default;">contact via website</span>'
    phone_html = f'<strong>📞</strong> {esc(telefono)}' if telefono else ""
    phone_div = f'<div class="card-phone">{phone_html}</div>' if telefono else ""
    return f'''<div class="school-card">
  <div class="card-body">
    <div class="card-name"><span class="card-number">{num}</span> {esc(nombre)}</div>
    {phone_div}
    <div class="card-addr">{esc(direccion)}</div>
    <div class="card-links">
      {web_html}
      {email_html}
    </div>
  </div>
</div>'''

def map_js(c):
    area = c.get("area") or c.get("barrio") or c.get("distrito") or ""
    name = c.get("nombre") or c.get("nombre_raw") or "?"
    name = name.replace('"', '\\"')
    return f'{{ number: {c["numero"]}, name: "{name}", area: "{esc(area)}", lat: {c["lat"]}, lng: {c["lng"]} }}'

def main():
    centros = json.loads(DATA.read_text(encoding="utf-8"))
    # reasignar numeración: orden alfabético del nombre normalizado (regla del plan §6.2)
    ordenados = sorted(centros, key=lambda c: (c.get("nombre_normalizado") or c.get("nombre") or "").lower())
    for i, c in enumerate(ordenados, 1):
        c["numero"] = i

    head, tail = leer_plantilla()
    cards = "\n\n  \n".join(card_html(c) for c in ordenados)
    con_coords = [c for c in ordenados if c.get("lat") is not None and c.get("lng") is not None]
    map_entries = ",\n        ".join(map_js(c) for c in con_coords)

    # insertar cards en head (que termina justo antes de la primera card)
    # y mapLocations en tail
    out = head + cards + "\n" + tail
    # reemplazar el array mapLocations
    out = re.sub(
        r"const mapLocations = \[.*?\];",
        "const mapLocations = [\n        " + map_entries + "\n      ];",
        out,
        flags=re.S,
    )
    OUT.write_text(out, encoding="utf-8")
    n_cards = out.count('<div class="school-card">')
    print(f"index.html regenerado: {len(ordenados)} fichas, {len(con_coords)} con coordenadas, {n_cards} cards HTML")

if __name__ == "__main__":
    main()
