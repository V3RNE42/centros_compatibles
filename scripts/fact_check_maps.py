#!/usr/bin/env python3
"""Fact-checking de centros contra Google Maps via playwright-cli. Sin API key.

Emite veredicto por centro: OK / CERRADO / REVISAR / SIN_DATOS.
NO actualiza el dataset final (data/centros.json); escribe un overlay de verdades
de campo en data/verificacion.json que un merge aparte aplica.

Uso:
    python3 scripts/fact_check_maps.py --limit 5
    python3 scripts/fact_check_maps.py --only sev-9000 --verbose
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENTROS = os.path.join(RAIZ, "data", "centros.json")
SALIDA = os.path.join(RAIZ, "data", "verificacion.json")
SCRIPTS_SKILL = os.path.expanduser(
    "~/.hermes/skills/research/google-maps-scraper/scripts/maps-extract.mjs"
)

# --- parseo de fechas relativas de Google Maps ---------------------------------

_UNIDAD_DIAS = [
    (("dia", "dias"), 1),
    (("semana", "semanas"), 7),
    (("mes", "meses"), 30),
    (("ano", "anos", "año", "años"), 365),
]
_NUMERO = {
    "un": 1, "una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12,
}


def dias_desde(when):
    """'Hace 6 años' / 'hace 2 semanas' -> días aproximados. None si no parsea."""
    if not when:
        return None
    s = unicodedata.normalize("NFKD", when.lower())
    s = "".join(c for c in s if not unicodedata.combining(c)).replace("ñ", "n")
    m = re.search(r"hace\s+(\d+|[a-zñ]+)\s+([a-zñ]+)", s)
    if not m:
        return None
    n_txt, unidad = m.group(1), m.group(2)
    n = int(n_txt) if n_txt.isdigit() else _NUMERO.get(n_txt)
    if not n:
        return None
    for variantes, dias in _UNIDAD_DIAS:
        if any(unidad.startswith(v) for v in variantes):
            return n * dias
    return None


def normaliza(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def nombre_coincide(nombre, extraido):
    """Comparación por tokens: 'Academia Afoban' ⊂ 'Academia Afoban Sevilla'."""
    a, b = normaliza(nombre), normaliza(extraido)
    if not a or not b:
        return False
    if a == b or a in b or b in a:
        return True
    ta, tb = set(a.split()), set(b.split())
    return len(ta & tb) / max(len(ta), 1) >= 0.75


# --- playwright ----------------------------------------------------------------

def cli(*args, timeout=90):
    """playwright-cli sobre la sesion por defecto. Nunca -s=: la sesion nombrada
    se queda en mal estado entre invocaciones y devuelve snapshots vacios."""
    r = subprocess.run(["playwright-cli", *args], capture_output=True, text=True,
                       timeout=timeout)
    return r.stdout


def cli_raw(expr, timeout=60):
    """--raw eval devuelve JSON serializado; a veces con comillas envolventes."""
    out = cli("--raw", "eval", expr, timeout=timeout).strip()
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return out


def acepta_consentimiento():
    """Rechaza el muro de cookies. Un click basta; reintentar no ayuda porque el
    navegador se relanza en cada intento y vuelve al mismo muro."""
    for _ in range(2):
        if "consent.google.com" not in str(cli_raw("document.location.href") or ""):
            return True
        snap = cli("--raw", "snapshot")
        m = re.search(r'button "Rechazar todo".*?\[ref=(\w+)\]', snap, re.S)
        if not m:
            time.sleep(3)          # el muro tarda en renderizar el botón
            continue
        cli("click", m.group(1))
        time.sleep(4)              # el redirect a Maps no es instantáneo
    return "consent.google.com" not in str(cli_raw("document.location.href") or "")


def _abre(nombre, timeout=90):
    """(Re)abre el navegador en la búsqueda. El proceso muere entre centros:
    sin esto el segundo centro devuelve 'browser is not open'."""
    cli("kill-all", timeout=30)
    time.sleep(0.5)
    cli("open", "--browser=chromium",
        "https://www.google.com/maps/search/" + nombre.replace(" ", "+"),
        timeout=timeout)
    time.sleep(2)


def extrae(nombre, timeout=90, reintentos=2):
    """Campos del negocio, o {'error': ...}. Sesión por defecto, reabierta siempre."""
    datos = {"error": "sin intentos"}
    for intento in range(reintentos + 1):
        datos = _extrae_una_vez(nombre, timeout)
        if not datos.get("error"):
            return datos
        if intento < reintentos:
            time.sleep(2)
    return datos


def _extrae_una_vez(nombre, timeout=90):
    _abre(nombre, timeout)

    snap = cli("--raw", "snapshot")
    if not snap:
        return {"error": "sin respuesta del navegador"}
    if "is not open" in snap or "please run open first" in snap:
        return {"error": "navegador no abierto"}

    if "consent.google.com" in str(cli_raw("document.location.href") or ""):
        if not acepta_consentimiento():
            return {"error": "muro de consentimiento no superado"}

    url = str(cli_raw("document.location.href") or "")
    if "/maps/place/" in url:
        # recargar con la URL completa (feature id) hace renderizar el panel
        # de reseñas, rating y categoría; sin él solo sale el raíl izquierdo
        cli("goto", url, timeout=timeout)
        time.sleep(3)

    texto_pagina = str(cli_raw("document.body.innerText || ''") or "")

    # "Google Maps no encuentra X" — negocio ausente de Maps. La vista de búsqueda
    # sin resultado único NO tiene h1, así que hay que comprobar esto ANTES.
    if "no encuentra" in texto_pagina:
        return {"error": None, "no_encontrado": True, "nombre_en_maps": None,
                "reviews": [], "pid": None,
                "mensaje_maps": texto_pagina.split("|")[0][:120]}

    nombre_maps = str(cli_raw("document.querySelector('h1')?.textContent || ''") or "")
    # el muro de cookies también renderiza un h1; no es un negocio
    if not nombre_maps or "Antes de ir a Google" in nombre_maps:
        return {"error": "consentimiento no resuelto", "nombre_en_maps": nombre_maps}

    raw = cli("--raw", "run-code", f"--filename={SCRIPTS_SKILL}")
    try:
        datos = json.loads(json.loads(raw.strip()))
    except (json.JSONDecodeError, TypeError):
        return {"error": "extracción ilegible", "nombre_en_maps": nombre_maps}

    datos["nombre_en_maps"] = nombre_maps
    texto = str(cli_raw("document.body.innerText || ''") or "")
    datos["cerrado_permanente"] = bool(
        re.search(r"cerrado permanentemente|permanentemente cerrado", texto, re.I)
    )
    datos["cerrado_temporalmente"] = bool(
        re.search(r"cerrado temporalmente|temporalmente cerrado", texto, re.I)
    )
    return datos


# --- veredicto ------------------------------------------------------------------

MESES_RECIENTE = 18      # reseña <= 18 meses = señal fuerte de vida
MESES_INTERMEDIO = 48    # 18-48 meses = señal débil; > 48 = inconcluso


def veredicto(centro, datos, umbral_meses=MESES_RECIENTE):
    """OK | CERRADO | REVISAR | SIN_DATOS, con lista de razones."""
    if datos.get("error"):
        return "SIN_DATOS", [datos["error"], "no equivale a cerrado: reintentar"]

    if datos.get("no_encontrado"):
        return "NO_ENCONTRADO", [
            "Google Maps no devuelve ninguna ficha para este nombre",
            "revisar nombre en el dataset o dar de baja: NO es prueba de cierre",
        ]

    if datos.get("cerrado_permanente"):
        return "CERRADO", ["Google Maps marca cerrado permanentemente"]

    señales = []
    if datos.get("tel"):
        señales.append("telefono")
    if datos.get("web"):
        señales.append("web")
    if datos.get("hist") or datos.get("total"):
        señales.append("resenas")
    if datos.get("cat"):
        señales.append("categoria")

    dias_nuevos = [d for d in (dias_desde(r.get("when")) for r in datos.get("reviews", []))
                   if d is not None]
    dias = min(dias_nuevos) if dias_nuevos else None

    razones = []
    if datos.get("cerrado_temporalmente"):
        razones.append("cerrado temporalmente")

    if not datos.get("nombre_en_maps"):
        return "SIN_DATOS", ["ficha vacía en Maps", "el negocio puede no existir o estar sin listar"]

    if not nombre_coincide(centro.get("nombre", ""), datos["nombre_en_maps"]):
        razones.append(
            f"nombre en Maps '{datos['nombre_en_maps']}' != dataset '{centro.get('nombre')}'"
        )
        return "REVISAR", razones

    if dias is None:
        if not señales:
            return "SIN_DATOS", ["sin teléfono, web, categoría ni reseñas"]
        razones.append("sin reseñas con fecha (¿negocio sin volumen de reseñas?)")
        return "REVISAR", razones + [f"señales: {', '.join(señales)}"]

    meses = dias / 30.0
    if meses <= umbral_meses:
        return "OK", [f"reseña hace ~{meses:.0f} meses"] + [f"señales: {', '.join(señales)}"]
    if meses <= MESES_INTERMEDIO:
        razones.append(f"reseña más reciente hace ~{meses:.0f} meses (débil)")
        return "REVISAR", razones + [f"señales: {', '.join(señales)}"]
    razones.append(f"reseña más reciente hace ~{meses:.0f} meses (> {MESES_INTERMEDIO//12} años)")
    return "REVISAR", razones + ["antigüedad de reseñas NO prueba cierre: falso negativo probable"]


# --- main -----------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", help="id de un centro concreto")
    ap.add_argument("--umbral-meses", type=int, default=MESES_RECIENTE)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    centros = json.load(open(CENTROS, encoding="utf-8"))
    if args.only:
        centros = [c for c in centros if c["id"] == args.only]
        if not centros:
            sys.exit(f"id no encontrado: {args.only}")
    if args.limit:
        centros = centros[:args.limit]

    previo = {}
    if os.path.exists(SALIDA):
        previo = {v["id"]: v for v in json.load(open(SALIDA, encoding="utf-8"))}

    for i, c in enumerate(centros, 1):
        if c["id"] in previo:
            continue
        t0 = time.time()
        try:
            datos = extrae(c["nombre"])
        except subprocess.TimeoutExpired:
            datos = {"error": "timeout de playwright"}
        ver, razones = veredicto(c, datos, args.umbral_meses)
        previo[c["id"]] = {
            "id": c["id"],
            "nombre": c["nombre"],
            "estado_dataset": c.get("estado"),
            "veredicto": ver,
            "razones": razones,
            "nombre_en_maps": datos.get("nombre_en_maps"),
            "place_id": datos.get("pid"),
            "maps_total": datos.get("total"),
            "rating": datos.get("rating"),
            "categoria_maps": datos.get("cat"),
            "telefono_maps": datos.get("tel"),
            "web_maps": datos.get("web"),
            "mensaje_maps": datos.get("mensaje_maps"),
            "telefono_coincide": (normaliza(datos.get("tel") or "").replace(" ", "")
                                  == normaliza(c.get("telefono") or "").replace(" ", "")
                                  if datos.get("tel") and c.get("telefono") else None),
            "web_coincide": (normaliza(datos.get("web") or "").replace(" ", "").endswith(
                normaliza(c.get("web") or "").split("//")[-1].replace("www.", "").replace(" ", ""))
                if datos.get("web") and c.get("web") else None),
            "dias_ultima_resena": (lambda d: d[0] if d else None)(
                sorted([x for x in (dias_desde(r.get("when")) for r in datos.get("reviews", []))
                        if x is not None]) or [None]),
            "reviews": datos.get("reviews", [])[:3],
            "error": datos.get("error"),
            "segundos": round(time.time() - t0, 1),
            "fecha_verificacion": time.strftime("%Y-%m-%d"),
        }
        v = previo[c["id"]]
        if args.verbose:
            print(json.dumps(v, ensure_ascii=False, indent=1))
        else:
            print(f"[{i}/{len(centros)}] {c['id']:>10}  {ver:<8}  {c['nombre'][:38]:<38} "
                  f"{v['dias_ultima_resena'] if v['dias_ultima_resena'] is not None else '-':>6}d  "
                  f"{v['segundos']}s")
        # persistencia incremental: un fallo no tira el trabajo pagado en tiempo
        json.dump(list(previo.values()), open(SALIDA, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        time.sleep(1.5)

    cli("kill-all")

    conteo = {}
    for v in previo.values():
        conteo[v["veredicto"]] = conteo.get(v["veredicto"], 0) + 1
    print("\n" + json.dumps(conteo, indent=1, ensure_ascii=False))
    print(f"-> {os.path.relpath(SALIDA, RAIZ)}  ({len(previo)} centros)")


def demo():
    """Autochequeo del parser de fechas y del veredicto."""
    assert dias_desde("Hace 6 años") == 6 * 365
    assert dias_desde("Hace 2 meses") == 60
    assert dias_desde("hace 3 semanas") == 21
    assert dias_desde("Hace un año") == 365
    assert dias_desde("Hace 12 años") == 4380
    assert dias_desde("") is None and dias_desde("el mes pasado") is None

    assert nombre_coincide("Academia Afoban", "Academia Afoban")
    assert nombre_coincide("Kids&Us Sevilla Este", "Kids&Us Sevilla Este")
    assert not nombre_coincide("Kids&Us Sevilla", "Kids&Us Mairena")

    c = {"nombre": "Emergya"}
    d = {"nombre_en_maps": "Emergya", "pid": "ChIJ", "total": 63, "tel": "954",
         "web": "x.es", "cat": "Software", "reviews": [{"when": "Hace 19 años"}]}
    assert veredicto(c, d)[0] == "REVISAR"          # 19 meses -> ni OK ni CERRADO
    d["reviews"] = [{"when": "Hace 6 meses"}]
    assert veredicto(c, d)[0] == "OK"
    d["cerrado_permanente"] = True
    assert veredicto(c, d)[0] == "CERRADO"
    assert veredicto(c, {"error": "timeout"})[0] == "SIN_DATOS"
    assert veredicto(c, {"nombre_en_maps": "Otro Negocio SL", "pid": "x"})[0] == "REVISAR"
    assert veredicto(c, {"nombre_en_maps": "Emergya"})[0] == "SIN_DATOS"  # sin señales
    # regresión: el muro de cookies renderiza un h1 y NO es un negocio
    assert veredicto(c, {"error": "consentimiento no resuelto",
                         "nombre_en_maps": "Antes de ir a Google"})[0] == "SIN_DATOS"
    # regresión: el navegador muerto no debe confundirse con un cierre
    assert veredicto(c, {"error": "navegador no abierto"})[0] == "SIN_DATOS"
    # regresión: 'no encuentra' es concluyente, no un fallo técnico
    assert veredicto(c, {"no_encontrado": True})[0] == "NO_ENCONTRADO"
    print("demo OK")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--demo":
        demo()
    else:
        main()
