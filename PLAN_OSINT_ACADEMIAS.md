# Plan OSINT — Censo exhaustivo de academias de inglés en Sevilla y área metropolitana

**Versión:** 1.0 — 15 agosto 2026
**Destinatario de ejecución:** operador humano o agente con web, navegador y ejecución de código
**Repositorio objetivo:** `V3RNE42/centros_compatibles` — https://centros-compatibles.vercel.app

---

## Índice

- [0. Supuestos adoptados](#0-supuestos-adoptados)
- [1. Diagnóstico del estado actual del repositorio](#1-diagnóstico-del-estado-actual-del-repositorio)
- [2. Definición del objetivo y del ámbito](#2-definición-del-objetivo-y-del-ámbito)
- [3. Modelo del universo y estimación de tamaño](#3-modelo-del-universo-y-estimación-de-tamaño)
- [4. Estrategia de fuentes priorizada](#4-estrategia-de-fuentes-priorizada)
- [5. Queries y dorks literales](#5-queries-y-dorks-literales)
- [6. Pipeline técnico](#6-pipeline-técnico)
- [7. Verificación y control de calidad](#7-verificación-y-control-de-calidad)
- [8. Plan de ejecución por fases](#8-plan-de-ejecución-por-fases)
- [9. Riesgos y modos de fallo](#9-riesgos-y-modos-de-fallo)
- [Anexo A — Lista cerrada de municipios](#anexo-a--lista-cerrada-de-municipios-potaus-46)
- [Anexo B — Índice de marcas [VERIFICAR]](#anexo-b--índice-de-marcas-y-franquicias-a-verificar)

---

## 0. Supuestos adoptados

Ambigüedades del encargo resueltas por decisión propia. Cada una es reversible; si alguna es errónea, el impacto se indica.

| # | Ambigüedad | Supuesto adoptado | Impacto si es erróneo |
|---|---|---|---|
| S1 | "Área metropolitana" no definida | POTAUS (Decreto 267/2009), 46 municipios | Alto: cambia el barrido geográfico entero. Ver §2.2 para el subconjunto reducido alternativo |
| S2 | ¿El censo debe seguir mezclando colegios y academias? | Sí, pero con campo `tipologia` obligatorio que permita filtrar. No se tocan las fichas de colegios salvo para corregir errores | Bajo |
| S3 | ¿"Todas las academias" o "todas las que podrían contratarme"? | Todas las del ámbito, con campo `prioridad_candidatura` derivado. Un censo sesgado por empleabilidad percibida no es censable ni verificable | Medio: si solo interesan las contratables, las fases 3–4 pierden ~40% de su valor |
| S4 | Escuelas de ELE (CLIC, Giralda Center) | **Se incluyen** si cumplen el criterio de evidencia de §2.4. No por intuición: por regla escrita | Bajo |
| S5 | Formato de salida de los datos | Se propone migrar a `data/centros.json` + generador que emita el HTML actual. Escribir altas a mano sobre `index.html` no escala a +200 fichas | Medio: si se rechaza, el pipeline debe emitir fragmentos HTML directamente (§6.2 contempla ambos) |
| S6 | Presupuesto | Se asume tolerancia de 0–50 € en APIs de pago. Todo el plan tiene ruta 100% gratuita, más lenta | Bajo |
| S7 | Idioma de los datos | El repo mezcla "Seville"/"Sevilla" y etiquetas en inglés. Se mantiene el esquema en inglés existente para no romper el front, y se normaliza el **contenido** a español (topónimos oficiales) | Bajo |
| S8 | Franquicias con sede fuera del ámbito pero centro dentro | Cada **sede física** es una ficha; la marca es un campo, no una ficha | Bajo |

---

## 1. Diagnóstico del estado actual del repositorio

Inspección realizada el 15/08/2026 sobre `main` (56 commits).

### 1.1 Dónde están realmente los datos

**La afirmación del encargo de que los datos están en `clusters/` es incorrecta.** Estructura real:

```
/
├── index.html          ← 79.901 bytes. CONTIENE TODOS LOS DATOS
├── leaflet.js, leaflet.css, favicon*
└── clusters/
    ├── clusters_centros.yaml            (5.575 B)  — agrupaciones, no fichas
    ├── carmelitas-sevilla.md            (13.162 B) — informe narrativo
    ├── colegios-fomento.md              (14.459 B)
    ├── colegios-san-jose-sevilla.md     ( 9.249 B)
    ├── english-connection-sevilla.md    (12.159 B)
    ├── hermanos-sagrada-familia-belley.md (18.078 B)
    └── salesianos-sevilla.md            (18.699 B)
```

`clusters/` es **documentación de investigación**, no un almacén de datos. Los datos viven en dos estructuras paralelas dentro de `index.html`:

**(a) Fichas — `div.school-card`, 70 instancias:**

```html
<div class="school-card">
  <div class="card-body">
    <div class="card-name"><span class="card-number">47</span> Col. Ntra. Sra. de los Reyes (Mercedarias)</div>
    <div class="card-phone"><strong>📞</strong> 954370550</div>
    <div class="card-addr">C/ Calatrava, 38, 41003 Sevilla</div>
    <div class="card-links">
      <a class="link-chip" href="https://..." rel="noopener" target="_blank">https://...</a>
      <span class="email-chip" data-email="..." role="button" tabindex="0">...</span>
    </div>
  </div>
</div>
```

Placeholders: `<span class="link-chip" style="...">no website found</span>` y equivalente para email.

**(b) Mapa — array JS `mapLocations`, 66 instancias (línea ~1755):**

```js
const mapLocations = [
  { number: 1, name: "AMT Spain / AM Transnational", area: "Los Bermejales", lat: 37.3465852, lng: -5.9796283 },
  ...
];
```

### 1.2 Defectos detectados y cuantificados

| ID | Defecto | Evidencia medida | Gravedad |
|---|---|---|---|
| D1 | **Desincronización ficha↔mapa** | 70 fichas, 66 entradas en `mapLocations`. Sin coordenadas: **#67, #68, #69, #70** | Alta |
| D2 | **Propagación de email** | `sevilla.losremedios@englishconnection.es` → **18 fichas**; `secretaria@carmelitassevilla.es` → **5**; `secretaria@colegiosanjosesevilla.com` → **2** | Alta |
| D3 | **Propagación de dirección** | `C/ Bailén, 32, 41001 Seville` → **3 fichas**; `C/ San José, 5, 41003 Seville` → **2** | Crítica (municipios distintos) |
| D4 | **Contradicción lógica** | Nota de exclusión de San Francisco de Paula en línea 705; ficha **#68** lo lista | Media |
| D5 | **Sesgo de marca** | English Connection = 18/70 = **25,7%** del censo. Recolección guiada por el localizador de una sola cadena | Crítica (es la causa raíz del encargo) |
| D6 | **Duplicado no resuelto** | #52 y #53 comparten dirección `C/ San José, 5` y teléfono `954218353`. El propio YAML lo reconoce sin resolverlo | Media |
| D7 | **Sin procedencia** | Ninguna ficha tiene `source`, `source_url`, `fecha_captura` ni `confianza`. Imposible auditar | Alta |
| D8 | **Datos no reutilizables** | Sin CSV/JSON. Cualquier alta requiere editar HTML a mano | Alta (bloquea la escala) |
| D9 | **Inconsistencia de topónimo** | "Seville" y "Sevilla" conviven en el campo dirección | Baja |

### 1.3 Notas sobre D2 (crítico para el diseño del deduplicador)

El caso English Connection **no es un error de propagación**: los 18 centros comparten un email corporativo real de la franquicia. El caso Carmelitas y el de C/ Bailén **sí** son propagación errónea. La regla que los distinga aparece en §7.3 — la clave es que la propagación errónea acompaña a **direcciones incompatibles**, no a emails compartidos por sí solos.

### 1.4 Script de extracción del baseline (paso 0 obligatorio)

```python
# baseline_extract.py — convierte index.html en el dataset canónico de partida
import re, json, requests
from bs4 import BeautifulSoup

URL = "https://raw.githubusercontent.com/V3RNE42/centros_compatibles/main/index.html"
html = requests.get(URL, timeout=30).text
soup = BeautifulSoup(html, "html.parser")

# (a) fichas
fichas = {}
for card in soup.select("div.school-card"):
    num_el = card.select_one(".card-number")
    num = int(num_el.get_text(strip=True))
    name = card.select_one(".card-name").get_text(" ", strip=True)
    name = re.sub(r"^\s*%d\s*" % num, "", name).strip()
    phone_el = card.select_one(".card-phone")
    addr_el  = card.select_one(".card-addr")
    web_el   = card.select_one("a.link-chip")
    mail_el  = card.select_one(".email-chip")
    fichas[num] = {
        "numero": num,
        "nombre_raw": name,
        "telefono_raw": phone_el.get_text(" ", strip=True).replace("📞", "").strip() if phone_el else None,
        "direccion_raw": addr_el.get_text(" ", strip=True) if addr_el else None,
        "web_raw": web_el["href"] if web_el else None,
        "email_raw": mail_el.get("data-email") if mail_el else None,
    }

# (b) coordenadas
coords = {}
for m in re.finditer(
    r'\{\s*number:\s*(\d+),\s*name:\s*"([^"]*)",\s*area:\s*"([^"]*)",\s*lat:\s*(-?[\d.]+),\s*lng:\s*(-?[\d.]+)\s*\}',
    html):
    n = int(m.group(1))
    coords[n] = {"name_map": m.group(2), "area": m.group(3),
                 "lat": float(m.group(4)), "lng": float(m.group(5))}

for n, f in fichas.items():
    f.update(coords.get(n, {"lat": None, "lng": None, "area": None}))
    f["_sin_coordenadas"] = n not in coords

json.dump(list(fichas.values()), open("baseline_70.json", "w"), ensure_ascii=False, indent=2)
print("fichas:", len(fichas), "| sin coords:", sorted(n for n in fichas if n not in coords))
# salida esperada: fichas: 70 | sin coords: [67, 68, 69, 70]
```

Si la salida difiere de `70 / [67,68,69,70]`, el repo cambió desde el 15/08/2026: reinspeccionar antes de continuar.

---

## 2. Definición del objetivo y del ámbito

### 2.1 Definición operativa de "academia de inglés"

Una entidad entra en el censo si cumple **las tres** condiciones:

1. **Servicio**: imparte inglés como lengua extranjera **a terceros** (no formación interna de su propia plantilla).
2. **Entidad física**: dispone de un local identificable con dirección postal en el ámbito. Un domicilio fiscal sin actividad docente no basta.
3. **Capacidad de contratación**: es una persona jurídica o un autónomo con local que emplea o puede emplear profesorado distinto del titular.

La condición 3 es la que separa "academia" de "profesor particular". Se opera con proxies verificables (§2.4), no con juicio.

### 2.2 Ámbito geográfico

**Criterio elegido: POTAUS — Plan de Ordenación del Territorio de la Aglomeración Urbana de Sevilla, Decreto 267/2009 (BOJA nº 132, 09/07/2009). 46 municipios.**

Justificación frente a las alternativas:

| Criterio | Municipios | Pros | Contras | Decisión |
|---|---|---|---|---|
| Término municipal de Sevilla | 1 | Trivial | Excluye Dos Hermanas, Mairena, Tomares... donde el censo ya tiene fichas | ✗ |
| **POTAUS** | **46** | **Oficial, lista cerrada, citable, estable desde 2009, coincide con la delimitación del IECA** | Incluye municipios de baja densidad (Isla Mayor, Castilleja del Campo) con ~0 academias | **✓** |
| Radio 25 km desde Puerta de Jerez | ~35 | Simple de implementar | Arbitrario, corta términos municipales por la mitad | ✗ (se usa como *filtro secundario* de priorización) |
| Isócrona 45 min en transporte público | variable | El más relevante para empleabilidad real | No reproducible sin API de rutas; varía por hora y día | ✗ como delimitación, ✓ como campo derivado |
| Consorcio de Transportes del Área de Sevilla | ~46 [VERIFICAR] | Alineado con commuting real | Composición ha cambiado en el tiempo; menos citable | ✗ |

**Ventaja decisiva del POTAUS**: da una lista cerrada y auditable, lo que hace posible el criterio de parada por municipio de §7.5. Un radio kilométrico no permite decir "he barrido el 100% del ámbito".

**Estratificación operativa** (para ordenar el esfuerzo, no para excluir):

- **Corona 0** — Sevilla capital (11 distritos). ~690.000 hab. Prioridad máxima.
- **Corona 1** — contigüidad urbana y >20.000 hab: Dos Hermanas, Alcalá de Guadaíra, Mairena del Aljarafe, Utrera, La Rinconada, Camas, Tomares, Bormujos, San Juan de Aznalfarache, Coria del Río, Los Palacios y Villafranca, Castilleja de la Cuesta, Carmona.
- **Corona 2** — resto del Aljarafe y Los Alcores: Gines, Espartinas, Bollullos de la Mitación, Palomares del Río, Gelves, Mairena del Alcor, El Viso del Alcor, Salteras, Santiponce, Valencina, Umbrete, Villanueva del Ariscal, Sanlúcar la Mayor, La Algaba, Alcalá del Río, Brenes, Guillena, La Puebla del Río, Almensilla, Castilleja de Guzmán, Olivares, Pilas, Benacazón.
- **Corona 3** — periferia de baja densidad: Albaida del Aljarafe, Aznalcázar, Aznalcóllar, Carrión de los Céspedes, Castilleja del Campo, Gerena, Huévar del Aljarafe, Isla Mayor, Villamanrique de la Condesa.

Lista completa y códigos INE en el [Anexo A](#anexo-a--lista-cerrada-de-municipios-potaus-46).

### 2.3 Tipologías — cada una es una población distinta

| # | Tipología | Código | Fuentes primarias (§4) | Volumen esperado en el ámbito |
|---|---|---|---|---|
| 1 | Academia de idiomas independiente, sede única | `ACAD_IND` | Places, ACEIA, prep. Cambridge, Overpass | 90–160 |
| 2 | Cadena/franquicia con sedes locales | `ACAD_CADENA` | Localizadores de marca, portales de franquicia | 40–90 |
| 3 | Escuela de ELE que además da inglés / emplea nativos | `ELE_MIXTA` | Instituto Cervantes acreditados, IALC/FEDELE [VERIFICAR], Places | 8–20 |
| 4 | Centro preparador/examinador oficial | `EXAM_PREP` | Buscadores de Cambridge, Trinity, IELTS, LanguageCert, Aptis, OTE | 60–140 (con alto solape con 1 y 2) |
| 5 | Formación bonificada / in-company (FUNDAE) | `INCOMPANY` | Registro estatal de entidades de formación, FUNDAE, licitaciones | 15–40 |
| 6 | Academia generalista de refuerzo con inglés | `REFUERZO` | Places, directorios verticales, Overpass | 60–130 |
| 7 | EOI y centros públicos | `PUBLICO` | Registro de centros de la Junta, catálogo de EOI | 3–6 EOI + extensiones |
| 8 | Guardería/ludoteca/campamento con inmersión | `INFANTIL` | Places, marcas específicas, redes sociales | 15–40 |
| 9 | Centro online con sede física registrada | `ONLINE_LOCAL` | BORME/CNAE, portales de empleo | 3–10 |
| 10 | Casos frontera | `FRONTERA` | — | ver §2.4 |

**Nota sobre la tipología 4**: los "centros preparadores" son la fuente más productiva del plan y a la vez la de mayor solape. No es una población independiente: es un *atributo* de las poblaciones 1, 2, 3 y 6. Se modela como campo booleano `es_centro_preparador` + `certificadoras[]`, **no** como tipología excluyente. Se mantiene en la tabla porque su fuente de descubrimiento es distinta.

### 2.4 Criterio explícito para casos frontera

El encargo señala CLIC International House y Giralda Center. Regla, aplicable sin juicio:

**REGLA-ELE**: una escuela de español para extranjeros se **incluye** con `tipologia=ELE_MIXTA` si se documenta **al menos una** de estas evidencias, con URL y captura:

- **E1.** La web ofrece cursos de inglés a terceros (página, tarifa o formulario de matrícula de inglés).
- **E2.** Ha publicado en los últimos 24 meses una oferta de empleo para profesor de inglés / *English teacher*.
- **E3.** Aparece como centro preparador o examinador de una certificación de inglés (Cambridge, Trinity, IELTS, LanguageCert, Aptis, OTE).
- **E4.** Imparte formación de profesorado de inglés (CELTA, Trinity CertTESOL) — implica plantilla angloparlante y contratación recurrente.

Si no cumple ninguna: `estado=EXCLUIDO`, `motivo_exclusion=ELE_SIN_INGLES`. **Se conserva la ficha en el fichero de exclusiones**, nunca se borra: es la única forma de que una reejecución futura no vuelva a evaluarla desde cero.

> Nota: CLIC International House es, específicamente, un caso donde E4 es muy probable (la red International House imparte CELTA en varias sedes españolas) — **[VERIFICAR]** para la sede de Sevilla concretamente.

Otras fronteras y su regla:

| Caso | Regla | Código |
|---|---|---|
| Colegio bilingüe/concertado que además vende clases extraescolares de inglés al público | Incluir como `COLEGIO` + `oferta_extraescolar_ingles=true`. No duplicar ficha | — |
| Academia de oposiciones que prepara el B2 exigido | Incluir con `REFUERZO` solo si tiene página de inglés propia | `REFUERZO` |
| Guardería "bilingüe" sin docencia de inglés a terceros ajenos al alumnado | Incluir: el alumnado *es* el tercero. `INFANTIL` | `INFANTIL` |
| Gimnasio/centro cultural que alquila aula a un profesor autónomo | Excluir. El empleador es el autónomo, no el local | `EXC_LOCAL_CEDIDO` |
| Academia con local en municipio del ámbito y sede social fuera | Incluir la sede local | — |
| Franquiciado en trámite de apertura (local anunciado, sin actividad) | `estado=PROXIMA_APERTURA`, no cuenta para captura-recaptura | — |

### 2.5 Criterios de exclusión

| Código | Criterio | Justificación | Detección automática |
|---|---|---|---|
| `EXC_AUTONOMO` | Profesor particular sin local | No puede contratar (S1 del objetivo). Además su volumen es indeterminable: no hay universo censable | Anuncio en plataformas de clases particulares como única presencia + sin CIF/NIF de empresa + dirección = domicilio residencial |
| `EXC_ONLINE` | Plataforma 100% online sin presencia local | No contrata profesorado localizado en Sevilla de forma verificable, y su universo es global | Sin dirección postal en el ámbito, o dirección = coworking/domiciliación |
| `EXC_CERRADO` | Cerrado definitivamente | — | Places `businessStatus=CLOSED_PERMANENTLY` + web caída + sin actividad en RRSS >12 meses. **Requiere 2 de 3** |
| `EXC_NO_INGLES` | Academia sin oferta de inglés (informática, música, baile, oposiciones sin inglés) | Fuera del objetivo | Ausencia de términos de inglés en web + Places types |
| `EXC_ELE_SIN_INGLES` | ELE sin ninguna evidencia E1–E4 | §2.4 | Regla |
| `EXC_FUERA_AMBITO` | Fuera de los 46 municipios | §2.2 | Point-in-polygon contra los límites municipales |
| `EXC_INTERNA` | Departamento de idiomas interno de una empresa | No presta servicio a terceros | Manual |
| `EXC_DOMICILIACION` | Dirección = centro de negocios / domiciliación con >5 empresas registradas | Centro fantasma | Recuento de entidades por dirección normalizada |

**Importante**: exclusión ≠ borrado. Todo excluido va a `data/excluidos.json` con `motivo_exclusion`, `evidencia_url` y `fecha`. Sin esto, el captura-recaptura de §7.5 se corrompe (se recontarían como "nuevos" en cada pasada).

---

## 3. Modelo del universo y estimación de tamaño

Objetivo: saber **cuándo parar**. Tres vías independientes, cada una con supuestos explícitos.

### 3.1 Vía A — Penetración asociativa (ACEIA)

**Dato verificado (15/08/2026)**: ACEIA (Asociación de Centros de Enseñanza de Idiomas de Andalucía, fundada 1980) declara **164 centros** asociados en Andalucía que se dedican *exclusivamente* a la enseñanza de idiomas. Fuente: aceia.es, home. Cifras históricas: 154 centros (~2020), 170 (2022) — el sector está estabilizado, no en expansión.

```
Población Andalucía ≈ 8,60 M
Población provincia de Sevilla ≈ 1,97 M  → 22,9%
Centros ACEIA en provincia de Sevilla ≈ 164 × 0,229 ≈ 38     [VERIFICAR: contar en el buscador de ACEIA]
Ámbito POTAUS ≈ 80% de la población provincial              → ≈ 30 centros ACEIA en el ámbito

Tasa de afiliación (fracción del sector que se asocia): r
N_A = 30 / r
```

`r` es el parámetro crítico y no es observable directamente. Anclajes:

- ACEIA solo admite centros **exclusivamente** de idiomas → excluye por definición tipologías 6, 7, 8, y buena parte de 2 y 5.
- Las asociaciones patronales sectoriales en España rara vez superan el 30% de afiliación entre microempresas.
- Rango razonable: **r ∈ [0,12 ; 0,30]** para el subconjunto "academias de idiomas puras", que a su vez es ~60% del universo total definido en §2.1.

```
N_idiomas_puras = 30 / [0,12 ; 0,30]   → [100 ; 250]
N_total        = N_idiomas_puras / 0,60 → [167 ; 417]
```

**Estimación vía A: 165–420.** Intervalo ancho — la incertidumbre está toda en `r`. Se puede estrechar mucho: ver §3.5.

### 3.2 Vía B — Red de centros preparadores Cambridge

**Datos verificados (15/08/2026)**:

- Exams Andalucía (Platinum Centre, Granada) declara **>500–600 centros preparadores** en Andalucía Oriental **y provincia de Sevilla**.
- Instituto Británico de Sevilla (`exams-sevilla.com`) es Platinum Centre con su propia red de preparadores en Sevilla.
- `emacarena.com` (centro de idiomas Macarena, también sede examinadora) declara **>70 centros preparadores de toda la provincia** presentando candidatos con ellos.
- SevillaCert opera como centro examinador de LanguageCert en Sevilla y publica su lista de preparadores.

```
Preparadores Cambridge en la provincia de Sevilla ≈ P
P ∈ [150 ; 300]                                        [VERIFICAR contando las listas reales]
Fracción que son academias (no colegios) ≈ f1 ∈ [0,45 ; 0,65]
Fracción de academias que SON preparadoras  ≈ f2 ∈ [0,35 ; 0,60]

N_B = (P × f1) / f2 × 0,80 (ajuste provincia→ámbito)
    = [150×0,45/0,60×0,8 ; 300×0,65/0,35×0,8]
    = [90 ; 445]
```

Punto central (P=220, f1=0,55, f2=0,47): **N_B ≈ 206**.

**Sesgo conocido**: infraestima si hay muchas academias que no preparan exámenes oficiales (típico en refuerzo escolar e infantil); sobreestima si las listas de los tres examinadores solapan (un centro puede presentar con dos). **Deduplicar entre las tres listas antes de calcular P.**

### 3.3 Vía C — Densidad por habitante calibrada

```
Población del ámbito POTAUS ≈ 1.567.491 hab (INE 2024)
Densidad de academias de idiomas en área urbana española: d academias / 10.000 hab
N_C = 1.567.491 / 10.000 × d
```

`d` no está publicado de forma fiable **[VERIFICAR]**. Se estima por calibración: elegir una ciudad de tamaño comparable con censo local publicado y exhaustivo, contar y dividir. Con `d ∈ [1,0 ; 2,0]`:

```
N_C ∈ [157 ; 313]
```

**Cómo calibrar `d` sin ciudad de referencia** (recomendado, 20 min): aplicar el barrido de Places de la Fase 1 a un **único distrito completo** de Sevilla capital (p. ej. Nervión), con teselado exhaustivo hasta saturación local, y extrapolar por población:

```
d_observado = academias_en_distrito / (población_distrito / 10.000)
N_C_calibrado = d_observado × 156,7 × k
```
donde `k ∈ [0,55 ; 0,75]` corrige la menor densidad de la periferia respecto a un distrito urbano central. Esto convierte la vía C de "conjetura" en "medición", y debe hacerse en la Fase 1.

### 3.4 Vía D — Registro mercantil por CNAE (control cruzado)

CNAE 2009 relevante: **8559 — "Otra educación n.c.o.p."**. Problemas: agrupa autoescuelas, academias de música, formación deportiva y enseñanza de idiomas sin distinción. **No sirve como estimador directo**, sí como cota superior y como fuente de descubrimiento (§4, Nivel 3).

```
N_D_superior = empresas CNAE 8559 activas en el ámbito × fracción_idiomas
fracción_idiomas ≈ 0,10–0,20                              [VERIFICAR]
```

Consultar vía datos abiertos del BORME (`boe.es`, sección BORME, dumps diarios en XML/JSON) filtrando objeto social, o vía el DIRCE del INE por provincia y CNAE a 4 dígitos. Marcado **[VERIFICAR]** el acceso programático a ambos.

### 3.5 Síntesis y uso operativo

| Vía | Rango | Centro | Independencia |
|---|---|---|---|
| A — Penetración ACEIA | 165–420 | ~250 | Alta |
| B — Red preparadores Cambridge | 90–445 | ~206 | Alta |
| C — Densidad calibrada | 157–313 | ~235 | Media (comparte medición con Places) |
| D — CNAE (cota superior) | — | — | Alta |

**Estimación de consenso: 180–320 academias en el ámbito; punto central ≈ 230.**

Contra las ~15–20 academias que el censo contiene hoy (de 70 fichas, ~52 son colegios y 18 son English Connection), **faltan del orden de 200 centros**. Este número es el que da sentido al plan: no es una tarea de completar huecos, es una recolección casi desde cero para la vertiente de academias.

**Uso operativo del intervalo**: no se usa como objetivo, sino como *alarma*. Si al final de la Fase 3 el recuento es <150 o >400, alguna vía de estimación o el barrido tienen un error sistemático que hay que diagnosticar antes de seguir.

---

## 4. Estrategia de fuentes priorizada

### 4.1 Criterio de niveles

- **Nivel 1** — alta cobertura, coste bajo, fiabilidad alta. Se ejecuta primero, en paralelo.
- **Nivel 2** — cobertura media o coste medio; aporta cola larga y verificación cruzada.
- **Nivel 3** — cobertura baja o coste alto; solo tras saturación de niveles 1–2, o para casos concretos.
- **Nivel 4** — fuentes de verificación y rescate, no de descubrimiento primario.

Las estimaciones de "aporta único" son **priors** para el reparto de esfuerzo; se recalculan con datos reales tras la Fase 1 (§7.5).

### 4.2 Tabla maestra de fuentes

| Nv | Fuente | Qué aporta que otras no | Sesgo que introduce | Solape esperado | Coste |
|---|---|---|---|---|---|
| 1 | **Google Places API (New)** — Text + Nearby, teselado | Cobertura casi censal de negocios con local, coordenadas, teléfono, web, `businessStatus` | Sesgo hacia negocios que gestionan su ficha; infrarrepresenta centros sin Google Business Profile | Base de todo | 0–35 € |
| 1 | **Buscador de centros de ACEIA** | Centros de idiomas puros, verificados por la patronal. Alta precisión | Solo asociados (r≈0,12–0,30). Sesgo hacia centros establecidos y medianos | ~70% con Places | 0 € |
| 1 | **Listas de centros preparadores Cambridge** (Instituto Británico de Sevilla, Exams Andalucía, Exams-Sevilla) | La mayor lista sectorial existente. Además certifica actividad real | Excluye academias que no presentan a exámenes | ~65% con Places | 0 € |
| 1 | **Localizadores de franquicias** (uno por marca) | **El eje donde el censo está más incompleto.** Sedes exactas, marca, a veces email por sede | Solo marcas conocidas de antemano → requiere descubrimiento previo de marcas | ~50% con Places | 0 € |
| 1 | **OSM / Overpass API** | Gratis, sin límite práctico, sin restricción de almacenamiento. `amenity=language_school` | Cobertura irregular; depende de mapeadores locales | ~55% con Places | 0 € |
| 2 | Trinity College London — buscador de centros | Red distinta a Cambridge; capta academias con perfil comunicativo/infantil | Menor implantación que Cambridge | ~40% | 0 € |
| 2 | LanguageCert / SevillaCert; Aptis (British Council); Oxford Test of English; IELTS (BC/IDP) | Redes recientes, captan academias jóvenes | Muy parciales | ~30–50% | 0 € |
| 2 | **Portales de empleo** (InfoJobs, LinkedIn Jobs, Indeed, Tusclasesparticulares, TEFL.com, tefl.org boards) | **Prueba de actividad y de contratación.** Alto valor para el objetivo real del usuario | Solo academias que contratan formalmente y publican | ~45% | 0 € |
| 2 | Directorios verticales de formación (Emagister, Educaweb, Lectiva, Cursosidiomas) **[VERIFICAR cada uno]** | Cola larga de centros pequeños | **Sesgo de pago**: prioriza quien paga por listarse; incluye fantasmas no depurados | ~60% | 0 € (scraping) |
| 2 | Bing Maps / HERE / Apple Maps / Foursquare | Índices de POI distintos, capturan lo que Google pierde | Bases más pobres en España | ~75% | 0–20 € |
| 2 | Registro de centros de la Junta de Andalucía | Único censal para EOI, colegios y FP | **NO contiene academias no regladas** (ver §4.3) | ~10% | 0 € |
| 2 | Redes sociales (Instagram por geolocalización, Facebook Pages locales, LinkedIn por sector+ubicación) | Centros muy pequeños e infantiles sin web | Requiere navegador; antibot fuerte | ~35% | 0 € |
| 3 | BORME / CNAE 8559 | Entidades sin presencia digital; razones sociales para cotejo | Ruido enorme (autoescuelas, música); no dice si el local existe | ~15% | 0 € |
| 3 | Licencias de apertura / actividad municipal, datos abiertos municipales | Único que documenta el **local**, no la marca | Muy desigual entre 46 ayuntamientos; muchos no publican | ~20% | 0 € |
| 3 | Catastro (uso de local) | Verificación de que la dirección es un local comercial | No identifica la actividad concreta | — | 0 € |
| 3 | Registro estatal de entidades de formación / FUNDAE | Tipología 5 (in-company) | Incluye entidades sin local propio | ~25% | 0 € |
| 3 | Listados de subvenciones, becas de idiomas, convenios AMPA/ayuntamientos, licitaciones públicas | Centros que trabajan con administraciones y no se anuncian | Muy disperso | ~20% | 0 € |
| 3 | Prensa local, blogs y foros de expatriados/profesores en Sevilla | Contexto, aperturas y cierres, reputación como empleador | Anecdótico | ~30% | 0 € |
| 4 | **Wayback Machine (CDX API)** | Recupera directorios muertos, detecta renombrados y cambios de web | Datos caducados → falsos positivos | — | 0 € |
| 4 | Common Crawl (índice URL) | Barrido masivo de dominios `.es` con términos objetivo | Muy costoso en cómputo para el retorno | — | 0 € |

### 4.3 Advertencia crítica sobre registros oficiales

**La enseñanza de idiomas no reglada NO está en el registro de centros docentes de la Consejería de Educación.** Se trata de una actividad mercantil de servicios, no de un centro docente autorizado.

Dato confirmado durante la validación de fuentes: ACEIA declara que el colectivo de centros privados de enseñanza **no reglada** de idiomas está regulado por la **Dirección General de Consumo de la Junta de Andalucía**, no por Educación.

**Implicación operativa de primer orden**: el registro de Educación solo servirá para tipología 7 (EOI, centros públicos) y para los colegios que el censo ya tiene. Buscar academias ahí es tiempo perdido. En cambio, **merece una línea de investigación específica** el registro o censo que Consumo pueda mantener sobre estos centros (obligaciones de hojas de reclamaciones, contratos-tipo, publicidad de precios). **[VERIFICAR: si existe un listado público de Consumo de centros de enseñanza no reglada, sería una fuente de Nivel 1 y cambiaría la prioridad de todo el plan. Comprobarlo en la Fase 1 antes que ninguna otra cosa: es la apuesta de mayor valor esperado del plan entero.]**

### 4.4 Fuentes descartadas y por qué

| Fuente | Motivo del descarte |
|---|---|
| Páginas Amarillas / QDQ | **[VERIFICAR estado en 2026]**. Históricamente alta cobertura, hoy con datos muy caducados. Usar solo como fuente Nivel 4 de rescate |
| Yelp | Implantación marginal en España; no compensa el coste de integración |
| Scraping directo de Google Maps sin API | Viola los ToS y expone a bloqueo. La API tiene capa gratuita suficiente |
| Compra de bases de datos comerciales de empresas | Coste alto, datos de segunda mano, sin trazabilidad de procedencia |

---

## 5. Queries y dorks literales

Bloques copiables. Sustituir `{MUNICIPIO}`, `{DISTRITO}`, `{CP}` iterando sobre las listas de §5.4.

### 5.1 Google / Bing / DuckDuckGo — descubrimiento general

```text
# Núcleo léxico ES
"academia de inglés" Sevilla
"academia de idiomas" Sevilla
"escuela de idiomas" Sevilla -oficial -EOI
"centro de idiomas" Sevilla
"clases de inglés" Sevilla academia
"cursos de inglés" Sevilla presencial
"inglés para niños" Sevilla academia
"inglés para empresas" Sevilla
"preparación First Certificate" Sevilla
"preparación Advanced" OR "preparación C1" Sevilla academia
"preparación Proficiency" Sevilla
"preparación IELTS" Sevilla
"academia bilingüe" Sevilla
"refuerzo escolar" "inglés" Sevilla academia

# Núcleo léxico EN
"English academy" Seville
"English school" Seville
"language school" Seville
"learn English" Seville academy
"English classes" Seville
"TEFL jobs" Seville
"English teacher" Seville academy vacancy

# Restricción de dominio nacional
site:.es "academia de inglés" Sevilla
site:.es "escuela de idiomas" ("Dos Hermanas" OR "Mairena" OR "Tomares" OR "Alcalá de Guadaíra")

# Estructuras de URL típicas del sector
inurl:academia inurl:ingles Sevilla
inurl:idiomas inurl:sevilla
inurl:english inurl:sevilla -site:booking.com -site:tripadvisor.com
intitle:"academia de inglés" intitle:Sevilla
intitle:"escuela de idiomas" Sevilla

# Páginas de contacto y de sedes (para enriquecimiento)
"academia de inglés" Sevilla (inurl:contacto OR inurl:contact OR inurl:donde-estamos)
"academia de inglés" Sevilla (inurl:trabaja-con-nosotros OR inurl:empleo OR inurl:jobs OR inurl:careers)
```

### 5.2 Descubrimiento de **cadenas y franquicias** (eje prioritario)

```text
# Localizadores de sedes
"nuestras sedes" "inglés" Sevilla
"encuentra tu centro" inglés academia
"nuestros centros" "academia de inglés" Sevilla
"centros en España" "academia de inglés" Sevilla
"localiza tu academia" inglés

# Portales de franquicia — descubrir marcas antes de recorrer localizadores
"franquicia" "academia de inglés" España
"abre tu franquicia" "academia de inglés"
"franquíciate" inglés academia
"franquicia de idiomas" España inversión
site:tormo.com idiomas franquicia            # [VERIFICAR dominio]
site:franquicias.net idiomas                  # [VERIFICAR dominio]
"franquicias de enseñanza de idiomas" listado

# Una vez identificada la marca {MARCA}
"{MARCA}" Sevilla
"{MARCA}" ("Dos Hermanas" OR "Mairena del Aljarafe" OR "Tomares" OR "Alcalá de Guadaíra")
site:{dominio_marca} Sevilla
inurl:{dominio_marca} inurl:sevilla
```

**Método de descubrimiento de marcas** (hacerlo *antes* de recorrer localizadores):

1. Barrer los 3–4 portales de franquicia españoles por la categoría "idiomas/enseñanza". **[VERIFICAR sus URLs reales]**
2. Extraer las marcas que declaran presencia en Andalucía.
3. Cruzar con los nombres repetidos que devuelva Google Places: si un mismo nombre aparece en ≥2 puntos del ámbito, es una cadena → añadir a la lista de marcas.
4. Para cada marca, localizar su localizador de sedes y extraerlo íntegro. Filtrar por los 46 municipios.

Este paso 3 es el que habría evitado el sesgo D5: **la detección de cadenas debe derivarse de los datos, no de conocimiento previo**.

### 5.3 Listados agregados de terceros

```text
# Artículos y rankings
"mejores academias de inglés en Sevilla"
"las mejores academias de inglés" Sevilla 2026
"academias de inglés en Sevilla" opiniones comparativa
"dónde estudiar inglés en Sevilla"
"guía de academias" idiomas Sevilla

# PDFs de asociaciones, ayuntamientos, AMPAs
filetype:pdf "academias de inglés" Sevilla
filetype:pdf "centros de idiomas" Sevilla listado
filetype:pdf "centros colaboradores" inglés Sevilla
filetype:pdf ACEIA centros asociados
filetype:pdf "centros preparadores" Cambridge Sevilla
filetype:pdf "oferta formativa" idiomas ayuntamiento {MUNICIPIO}
filetype:xlsx OR filetype:csv "academias" idiomas Sevilla

# Convenios y subvenciones
"convenio" "clases de inglés" ayuntamiento {MUNICIPIO}
"subvención" "cursos de inglés" AMPA Sevilla
site:*.gob.es OR site:*.juntadeandalucia.es "enseñanza de idiomas" Sevilla subvención
```

### 5.4 Barrido por granularidad geográfica

**Distritos de Sevilla capital (11):**

```text
Casco Antiguo | Macarena | Nervión | Cerro-Amate | Sur | Triana |
Norte | San Pablo-Santa Justa | Este-Alcosa-Torreblanca |
Bellavista-La Palmera | Los Remedios
```

**Barrios de alta densidad comercial** (lista de trabajo; obtener la lista canónica del dataset municipal de barrios, §6.3):

```text
Alameda, Alfalfa, Santa Cruz, Arenal, San Vicente, San Lorenzo, Feria,
Triana, Los Remedios, Tablada, El Porvenir, Heliópolis, Bami,
Reina Mercedes, Los Bermejales, Tiro de Línea, Bellavista,
Nervión, Gran Plaza, La Calzada, Ciudad Jardín, Santa Justa, Viapol,
San Pablo, Rochelambert, Cerro del Águila, Amate, Palmete, Su Eminencia,
Polígono Sur, Las Letanías, Padre Pío, Torreblanca, Parque Alcosa,
Sevilla Este, Palacio de Congresos, Polígono Norte, La Macarena,
Pino Montano, San Jerónimo, La Bachillera, Los Príncipes, Miraflores,
Santa Aurelia, Parque Amate, Tharsis, Parsi, La Salle
```

**Plantilla por municipio** (iterar sobre los 46 del Anexo A):

```text
"academia de inglés" "{MUNICIPIO}"
"academia de idiomas" "{MUNICIPIO}"
"clases de inglés" "{MUNICIPIO}" academia
"English academy" "{MUNICIPIO}"
site:.es "{MUNICIPIO}" "inglés" academia -site:facebook.com
```

**Códigos postales:**

- Sevilla capital: **41001–41020** (rango verificado y contiguo). Iterar los 20.
- Cinturón metropolitano: los CP de los otros 45 municipios **no forman un rango contiguo** y no deben inventarse. Derivarlos programáticamente:

```python
# Obtener el mapeo CP <-> municipio de una fuente autoritativa, NO de memoria
# Opciones (elegir la que esté viva en el momento de ejecutar):
#  a) CartoCiudad (IGN) - servicio de geocodificación oficial       [VERIFICAR endpoint]
#  b) Dataset de códigos postales de España en datos.gob.es         [VERIFICAR]
#  c) Nominatim/OSM: consultar boundary=postal_code por municipio
# Iterar luego:
for cp in cps_del_ambito:
    query(f'"academia de inglés" "{cp}"')
    query(f'"{cp}" idiomas academia Sevilla')
```

### 5.5 Overpass QL — consultas completas

Bbox aproximado del ámbito POTAUS: `37.05, -6.45, 37.68, -5.62` (S,W,N,E). Verificar contra los polígonos reales antes de usar como filtro definitivo.

```overpassql
/* Q1 — Escuelas de idiomas explícitas en el bbox metropolitano */
[out:json][timeout:180];
(
  nwr["amenity"="language_school"](37.05,-6.45,37.68,-5.62);
);
out center tags;
```

```overpassql
/* Q2 — Barrido léxico: cualquier POI cuyo nombre sugiera idiomas/inglés */
[out:json][timeout:300];
(
  nwr["name"~"[Aa]cademia.*[Ii]ngl[eé]s|[Ii]ngl[eé]s.*[Aa]cademia",i](37.05,-6.45,37.68,-5.62);
  nwr["name"~"[Ii]diomas",i](37.05,-6.45,37.68,-5.62);
  nwr["name"~"[Ee]nglish",i](37.05,-6.45,37.68,-5.62);
  nwr["name"~"[Ll]anguage",i](37.05,-6.45,37.68,-5.62);
  nwr["name"~"[Ss]chool of [Ee]nglish",i](37.05,-6.45,37.68,-5.62);
);
out center tags;
```

```overpassql
/* Q3 — Centros educativos no reglados y tutorías, para tipologías 6 y 8 */
[out:json][timeout:300];
(
  nwr["amenity"="prep_school"](37.05,-6.45,37.68,-5.62);
  nwr["office"="educational_institution"](37.05,-6.45,37.68,-5.62);
  nwr["amenity"="training"](37.05,-6.45,37.68,-5.62);
  nwr["shop"="educational"](37.05,-6.45,37.68,-5.62);
  nwr["amenity"="school"]["school:subject"~"language|english",i](37.05,-6.45,37.68,-5.62);
);
out center tags;
```

```overpassql
/* Q4 — Restringido al área administrativa exacta de un municipio (más limpio que bbox) */
[out:json][timeout:180];
area["name"="Dos Hermanas"]["admin_level"="8"]["boundary"="administrative"]->.mun;
(
  nwr["amenity"="language_school"](area.mun);
  nwr["name"~"[Ii]diomas|[Ii]ngl[eé]s|[Ee]nglish",i](area.mun);
);
out center tags;
```

```bash
# Ejecución
curl -s -X POST https://overpass-api.de/api/interpreter \
  --data-urlencode "data@q1.overpassql" \
  -H "User-Agent: censo-academias-sevilla/1.0 (contacto@ejemplo.es)" \
  -o osm_q1.json
```

Rate limit de la instancia pública de Overpass: aproximadamente 2 slots concurrentes y ~10.000 s de tiempo de cómputo diario por IP **[VERIFICAR: los límites cambian]**. Espaciar consultas ≥5 s y respetar `Retry-After`. Alternativa si se satura: instancia de Kumi Systems o descarga del extracto regional de Geofabrik (`andalucia-latest.osm.pbf`) y consulta local con `osmium`/`pyrosm` — **preferible si se van a hacer más de ~20 consultas**.

### 5.6 Google Places API (New) — llamadas y teselado

**Estado del pricing verificado (agosto 2026)**: el crédito recurrente de 200 $/mes desapareció el 1 de marzo de 2025. Ahora cada SKU tiene su propia franquicia gratuita mensual: **10.000 llamadas Essentials, 5.000 Pro, 1.000 Enterprise**. `Text Search (Pro)` ≈ 32 $/1.000; `Text Search (Enterprise)` ≈ 35 $/1.000; añadir `rating`/`reviews` empuja la llamada a Enterprise. La Places API antigua es *Legacy* y **no puede habilitarse en proyectos nuevos**.

**Consecuencia de diseño**: mantener el `X-Goog-FieldMask` estrictamente en campos Pro. Pedir `rating` cuesta dinero y no aporta nada al censo.

```bash
# Text Search — plantilla por municipio/barrio
curl -s -X POST 'https://places.googleapis.com/v1/places:searchText' \
  -H 'Content-Type: application/json' \
  -H "X-Goog-Api-Key: ${GOOGLE_MAPS_KEY}" \
  -H 'X-Goog-FieldMask: places.id,places.displayName,places.formattedAddress,places.location,places.nationalPhoneNumber,places.websiteUri,places.businessStatus,places.types,places.primaryType,nextPageToken' \
  -d '{
        "textQuery": "academia de inglés en Nervión, Sevilla",
        "languageCode": "es",
        "regionCode": "ES",
        "pageSize": 20
      }'
```

```bash
# Nearby Search — teselado por círculos
curl -s -X POST 'https://places.googleapis.com/v1/places:searchNearby' \
  -H 'Content-Type: application/json' \
  -H "X-Goog-Api-Key: ${GOOGLE_MAPS_KEY}" \
  -H 'X-Goog-FieldMask: places.id,places.displayName,places.formattedAddress,places.location,places.nationalPhoneNumber,places.websiteUri,places.businessStatus,places.types' \
  -d '{
        "includedTypes": ["language_school"],
        "maxResultCount": 20,
        "languageCode": "es",
        "regionCode": "ES",
        "locationRestriction": {
          "circle": { "center": {"latitude": 37.3826, "longitude": -5.9963}, "radius": 800.0 }
        }
      }'
```

> **[VERIFICAR]** que `language_school` sigue siendo un tipo válido en `includedTypes` de Places API (New). Si no lo fuera, sustituir por `school` + `primary_type_display_name` y filtrar por léxico. También **[VERIFICAR]** si `searchNearby` sigue sin soportar paginación (históricamente no la tenía, a diferencia de `searchText`).

**Teselado — cómo sortear el techo de 20/60 resultados:**

El techo real es 20 resultados por respuesta y hasta 3 páginas en `searchText` (60 máx). Si una celda devuelve 60, está **truncada silenciosamente** y hay que subdividirla. Algoritmo:

```python
def barrer_celda(centro, radio, tipo, profundidad=0, MAX_PROF=5):
    """Teselado adaptativo con quadtree. Subdivide solo donde satura."""
    res = nearby_search(centro, radio, tipo)
    if len(res) >= 20 and profundidad < MAX_PROF:
        # SATURACIÓN: la celda esconde más de lo que devuelve
        for sub_centro, sub_radio in subdividir_en_4(centro, radio):
            yield from barrer_celda(sub_centro, sub_radio, tipo, profundidad + 1)
    else:
        yield from res

# Malla inicial: hexagonal o cuadrada de 800 m de radio
#   Sevilla capital (141 km²)      -> ~90 celdas
#   Corona 1 (13 municipios)       -> ~170 celdas
#   Coronas 2-3 (32 municipios)    -> ~250 celdas, radio 1.500 m (densidad menor)
# Total inicial ~510 celdas; con subdivisión adaptativa, ~700-900 llamadas.
```

**Coste estimado del barrido completo con Places:**

| Escenario | Llamadas | Franquicia gratuita | Coste |
|---|---|---|---|
| Solo Nearby, field mask Pro, malla adaptativa | ~800 | 5.000 Pro/mes | **0 €** |
| + Text Search por municipio y por barrio (46 + 48 + variantes léxicas ×6) | ~1.400 | 5.000 Pro/mes | **0 €** |
| + Place Details enriquecido para 300 candidatos | ~300 | dentro de franquicia | **0 €** |
| Reejecución mensual completa | ~2.500 | 5.000 Pro/mes | **0 €** |

**El barrido completo cabe en la capa gratuita.** El riesgo no es el coste sino habilitar accidentalmente campos Enterprise (`rating`, `reviews`, `photos`), que solo tienen 1.000 llamadas gratis y cuestan 35–40 $/1.000. **Poner una cuota dura por API en la consola de Google**: las alertas de presupuesto notifican pero **no detienen** el consumo.

**Restricción de almacenamiento (ToS de Google Maps Platform)**: no se puede almacenar de forma permanente contenido de Places salvo `place_id`. Nombres, direcciones y teléfonos obtenidos de Places deben tratarse como caché temporal (≤30 días) y **reverificarse contra la web oficial del centro** antes de publicarse en el repositorio. Ver §6.7 — esto no es un formalismo: define la arquitectura del pipeline.

### 5.7 Alternativas gratuitas a Places

| Necesidad | Alternativa gratuita | Limitación |
|---|---|---|
| POIs | Overpass/OSM (§5.5) | Cobertura menor, pero **ODbL: sin restricción de almacenamiento** |
| Geocodificación | Nominatim (1 req/s, atribución obligatoria) o CartoCiudad (IGN) | Lento; Nominatim prohíbe uso masivo |
| Geocodificación masiva | Descarga del extracto de Geofabrik + `pelias`/`photon` local | Requiere montaje |
| Validación de direcciones | CartoCiudad / callejero del INE | **[VERIFICAR endpoints]** |

### 5.8 Portales de empleo — queries

```text
# InfoJobs / Indeed / LinkedIn
"profesor de inglés" Sevilla academia
"profesora de inglés" Sevilla contrato
"English teacher" Seville academy
"profesor nativo de inglés" Sevilla
"monitor de inglés" Sevilla
"teacher" "Sevilla" TEFL OR CELTA OR "Trinity CertTESOL"

# Dorks sobre los propios portales
site:infojobs.net "profesor de inglés" Sevilla         # [VERIFICAR dominio actual]
site:linkedin.com/jobs "English teacher" Seville
site:indeed.es "profesor de inglés" Sevilla academia

# Bolsas específicas del sector
"English teaching jobs" Seville
"TEFL jobs Seville" 2026
```

**Valor específico**: cada oferta identifica un centro **activo, con local y contratando** — exactamente el objetivo del usuario. El campo `fuente=EMPLEO` debe marcarse con `confianza=ALTA` en el eje "capacidad de contratación", incluso si el resto de datos son pobres.

### 5.9 Wayback Machine — recuperación de directorios muertos

```bash
# Listar todas las capturas de un directorio desaparecido
curl -s "http://web.archive.org/cdx/search/cdx?url=DOMINIO/*&output=json&fl=timestamp,original,statuscode&collapse=urlkey&limit=5000" \
  -o cdx_dominio.json

# Recuperar una captura concreta
curl -s "https://web.archive.org/web/20200601000000/http://DOMINIO/listado-academias-sevilla"
```

Usos: (a) recuperar listados de asociaciones o guías municipales ya retiradas; (b) detectar centros que **cambiaron de nombre** — misma URL, distinto `<title>` a lo largo del tiempo; (c) fechar el cierre de un centro (última captura con contenido vivo).

---

## 6. Pipeline técnico

### 6.1 Arquitectura

```
                    ┌──────────────────────────────────┐
   FASE 0           │ baseline_extract.py              │
                    │ index.html -> baseline_70.json   │
                    └───────────────┬──────────────────┘
                                    │
    ┌───────────────┬───────────────┼───────────────┬───────────────┐
    │ collectors/   │ collectors/   │ collectors/   │ collectors/   │  ← PARALELO
    │ places.py     │ overpass.py   │ franquicias/  │ preparadores/ │
    │ (API)         │ (API)         │ (playwright)  │ (html+pdf)    │
    └───────┬───────┴───────┬───────┴───────┬───────┴───────┬───────┘
            └───────────────┴───────┬───────┴───────────────┘
                                    ▼
                    ┌──────────────────────────────────┐
                    │ raw/  — un JSONL por fuente      │  ← NUNCA se sobrescribe
                    │ {fuente}_{YYYYMMDD}.jsonl        │     (append-only)
                    └───────────────┬──────────────────┘
                                    ▼
                    ┌──────────────────────────────────┐
                    │ normalize.py                     │
                    │ nombre / dirección / tel / dominio│
                    └───────────────┬──────────────────┘
                                    ▼
                    ┌──────────────────────────────────┐
                    │ dedupe.py  (blocking + fuzzy)    │
                    │ + cotejo contra baseline_70      │
                    └───────────────┬──────────────────┘
                                    ▼
                    ┌──────────────────────────────────┐
                    │ enrich.py (playwright)           │
                    │ email, tel, /trabaja-con-nosotros│
                    └───────────────┬──────────────────┘
                                    ▼
                    ┌──────────────────────────────────┐
                    │ verify.py — reglas §7            │
                    │ + capture_recapture.py — §7.5    │
                    └───────────────┬──────────────────┘
                                    ▼
              ┌─────────────────────┴─────────────────────┐
              ▼                                           ▼
   data/centros.json (canónico)              data/excluidos.json
              │
              ▼
   build_html.py  →  index.html (fichas + mapLocations sincronizados)
```

**Reglas de arquitectura:**

1. **`raw/` es inmutable.** Todo colector escribe JSONL con append. Ninguna etapa posterior lo modifica. Permite recalcular todo el pipeline con reglas nuevas sin volver a pedir datos, y es lo que hace posible el captura-recaptura.
2. **Persistencia**: SQLite (`censo.db`) para el estado intermedio y la caché HTTP; JSON para los artefactos publicables. No hace falta más.
3. **Paralelismo**: los colectores son independientes → 4 procesos. Normalización y deduplicación son secuenciales y globales. El enriquecimiento vuelve a ser paralelo (pool de 4 navegadores, ≥2 s entre peticiones al mismo dominio).
4. **Idempotencia**: cada colector guarda un hash del contenido descargado. Reejecutar no duplica.
5. **`build_html.py` es la única cosa que escribe `index.html`.** Resuelve D1 por construcción: la ficha y la entrada de mapa se generan del mismo registro.

### 6.2 Esquema canónico

```json
{
  "id": "sev-0071",
  "numero": 71,
  "nombre": "Academia Ejemplo Idiomas",
  "nombre_normalizado": "academia ejemplo idiomas",
  "marca_id": null,
  "tipologia": "ACAD_IND",
  "es_centro_preparador": true,
  "certificadoras": ["Cambridge", "Trinity"],
  "imparte_ingles": "CONFIRMADO",
  "municipio": "Sevilla",
  "municipio_ine": "41091",
  "distrito": "Nervión",
  "barrio": "Gran Plaza",
  "direccion": "C/ Ejemplo, 12, 1º",
  "cp": "41005",
  "direccion_completa": "C/ Ejemplo, 12, 1º, 41005 Sevilla",
  "lat": 37.3829853,
  "lng": -5.9739859,
  "geocod_metodo": "CARTOCIUDAD",
  "geocod_precision": "PORTAL",
  "telefono": "+34954123456",
  "telefono_display": "954123456",
  "web": "https://academiaejemplo.es",
  "dominio": "academiaejemplo.es",
  "email": "info@academiaejemplo.es",
  "email_tipo": "GENERICO",
  "url_empleo": "https://academiaejemplo.es/trabaja-con-nosotros",
  "estado": "ACTIVO",
  "motivo_exclusion": null,
  "fuentes": [
    {"source": "GOOGLE_PLACES", "source_url": "places/ChIJ...", "fecha_captura": "2026-08-15", "campos": ["nombre","lat","lng","telefono","web"]},
    {"source": "ACEIA",        "source_url": "https://aceia.es/...", "fecha_captura": "2026-08-15", "campos": ["nombre","direccion"]},
    {"source": "WEB_OFICIAL",  "source_url": "https://academiaejemplo.es/contacto", "fecha_captura": "2026-08-16", "campos": ["email","telefono","direccion"]}
  ],
  "n_fuentes_independientes": 3,
  "confianza": "ALTA",
  "verificado_manualmente": false,
  "flags": [],
  "notas": "",
  "primera_deteccion": "2026-08-15",
  "ultima_verificacion": "2026-08-16"
}
```

**Compatibilidad con el repo actual**: `numero`, `nombre`, `telefono_display`, `direccion_completa`, `web`, `email` mapean 1:1 a los campos de `div.school-card`; `numero`, `nombre`, `barrio`→`area`, `lat`, `lng` mapean a `mapLocations`. `build_html.py` no requiere refactorizar el front-end. Los placeholders actuales se preservan:

```python
web_html   = f'<a class="link-chip" href="{web}" rel="noopener" target="_blank">{web}</a>' if web \
             else '<span class="link-chip" style="background:#f7f8fb;color:#999;border-color:#ddd;cursor:default;">no website found</span>'
email_html = f'<span class="email-chip" data-email="{email}" role="button" tabindex="0">{email}</span>' if email \
             else '<span class="email-chip" style="...">contact via website</span>'
```

**Regla de numeración**: `numero` se **reasigna** en cada build por orden alfabético del nombre normalizado. `id` es el identificador estable. Mantener `numero` fijo con >200 fichas es una fuente garantizada de errores.

**Campo `flags`** — valores posibles, generados por §7.3:
`EMAIL_COMPARTIDO_MUNICIPIOS_DISTINTOS`, `DIRECCION_COMPARTIDA_MUNICIPIOS_DISTINTOS`, `DOMINIO_EMAIL_NO_COINCIDE_WEB`, `SIN_COORDENADAS`, `TELEFONO_COMPARTIDO_DISTANTE`, `FUENTE_UNICA`, `DIRECCION_SIN_NUMERO`, `COORDENADAS_FUERA_MUNICIPIO`, `POSIBLE_DUPLICADO`, `SIN_VERIFICAR_180D`.

### 6.3 Estrategia de scraping por tipo de fuente

| Tipo | Herramienta | Notas operativas |
|---|---|---|
| API con clave (Places) | `requests` + backoff | Cuota dura en consola. `X-Goog-FieldMask` mínimo |
| API abierta (Overpass, Wayback CDX) | `requests` | `User-Agent` identificativo con contacto. ≥5 s entre consultas Overpass |
| HTML estático (listas de preparadores, directorios) | `requests` + `selectolax` | Comprobar `robots.txt` **antes**. Cachear el HTML crudo en `raw/` |
| SPA / contenido dinámico (localizadores de franquicia, mapas embebidos) | `playwright` (chromium headless) | Muchos localizadores llaman a un endpoint JSON interno: **abrir DevTools, encontrar el XHR y llamarlo directamente**. Diez veces más rápido y robusto |
| PDF (listados de asociaciones, boletines) | `pdfplumber`; si es escaneado, `ocrmypdf` + `tesseract -l spa` | Las tablas de PDF requieren `extract_tables()` con ajuste de `table_settings` |
| Sitios con `robots.txt` restrictivo (**aceia.es lo tiene** — comprobado) | Navegación manual asistida, no automatizada | Ver §6.7 |
| Redes sociales | `playwright` con sesión, volumen bajo | Alto riesgo de bloqueo. Última prioridad |
| Geocodificación | CartoCiudad (IGN) → Nominatim → Places (fallback) | Registrar `geocod_metodo` y `geocod_precision` siempre |

**Patrón para localizadores de franquicia** (el eje prioritario):

```python
# 1. Abrir el localizador con playwright y capturar el tráfico de red
page.on("response", lambda r: capturar_si(r, patrones=["/api/", "centros", "stores", "sedes", "locations", ".json"]))
page.goto(url_localizador, wait_until="networkidle")
page.fill("input[type=text], input[name*=cp], input[placeholder*=ciudad]", "Sevilla")
page.keyboard.press("Enter")
page.wait_for_timeout(3000)

# 2. Si aparece un XHR con JSON de sedes -> llamarlo directamente en adelante,
#    normalmente sin filtro para obtener TODAS las sedes de España de una vez,
#    y filtrar por municipio en local.
# 3. Si no hay XHR (SSR), extraer del DOM con selectores estables (data-*, itemprop),
#    nunca con clases de framework tipo `css-1x2y3z`.
```

### 6.4 Normalización

```python
import re, unicodedata
import phonenumbers
import tldextract

FORMAS_JURIDICAS = r"\b(s\.?l\.?u?\.?|s\.?a\.?|s\.?c\.?|c\.?b\.?|sociedad limitada|coop\.?)\b"
ABREV = {
    r"\bcol\.?\b": "colegio", r"\bctro\.?\b": "centro", r"\bacad\.?\b": "academia",
    r"\bntra\.?\b": "nuestra", r"\bntro\.?\b": "nuestro", r"\bsra\.?\b": "señora",
    r"\bsan\b": "san", r"\bsta\.?\b": "santa", r"\bsto\.?\b": "santo",
    r"\bhh\.?\b": "hermanos", r"\bctra\.?\b": "carretera",
}
RUIDO = r"\b(sevilla|centro de idiomas|academia de idiomas|idiomas|english|school|academy|"\
        r"escuela|academia|oficial|s\.?l\.?)\b"

def norm_nombre(s: str) -> str:
    """Nombre canónico para comparación (NO para mostrar)."""
    s = s.lower().strip()
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")          # quita tildes
    for pat, rep in ABREV.items():
        s = re.sub(pat, rep, s)
    s = re.sub(FORMAS_JURIDICAS, " ", s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def norm_nombre_nucleo(s: str) -> str:
    """Versión sin palabras genéricas del sector: para blocking, no para scoring.
    'Academia de Inglés Los Remedios' -> 'los remedios'"""
    return re.sub(r"\s+", " ", re.sub(RUIDO, " ", norm_nombre(s))).strip()

def norm_telefono(t, region="ES"):
    if not t: return None
    try:
        p = phonenumbers.parse(str(t), region)
        if not phonenumbers.is_valid_number(p): return None
        return phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164)  # +34954123456
    except Exception:
        return None

def norm_dominio(url):
    if not url: return None
    e = tldextract.extract(url)
    return f"{e.domain}.{e.suffix}" if e.suffix else None   # eTLD+1
```

**Direcciones**: no normalizar con regex propias. Enviar la dirección cruda a **CartoCiudad (IGN)** o al callejero oficial y quedarse con la respuesta estructurada (tipo de vía, nombre, número, CP, municipio, coordenadas, precisión). Cuando el geocodificador devuelva precisión inferior a `PORTAL`, marcar `flags += ["DIRECCION_SIN_NUMERO"]` y **no** aceptar la ficha con confianza ALTA. **[VERIFICAR endpoints y límites de CartoCiudad en el momento de ejecutar.]**

**Topónimos**: aplicar el nombre oficial del INE ("Sevilla", nunca "Seville"; "Alcalá de Guadaíra" con tilde; "La Rinconada" con artículo). Esto resuelve D9 y es prerrequisito del blocking por municipio.

### 6.5 Deduplicación

**Paso 1 — Blocking** (reduce N² a un conjunto manejable). Un par entra en comparación si comparte **al menos una** clave:

| Clave | Definición | Comentario |
|---|---|---|
| `B1` | `telefono` E.164 idéntico | Muy fuerte |
| `B2` | `dominio` eTLD+1 idéntico | Fuerte, pero une todas las sedes de una cadena |
| `B3` | geohash de 6 caracteres (~1,2 km × 0,6 km) | Captura variantes de dirección |
| `B4` | `cp` + primeros 4 caracteres de `norm_nombre_nucleo` | Captura errores tipográficos |
| `B5` | `email` idéntico | **Cuidado**: dispara con el caso English Connection |

**Paso 2 — Scoring del par**

```python
from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler

def score_par(a, b):
    s_nombre = fuzz.token_set_ratio(a["nombre_normalizado"], b["nombre_normalizado"]) / 100
    s_dir    = JaroWinkler.similarity(a.get("direccion","") or "", b.get("direccion","") or "")
    d_m      = haversine(a["lat"], a["lng"], b["lat"], b["lng"]) if todos_coords(a,b) else None
    s_geo    = 1.0 if d_m is not None and d_m <= 50 else \
               0.7 if d_m is not None and d_m <= 150 else \
               0.0 if d_m is not None else 0.5          # 0.5 = desconocido, neutro
    s_tel    = 1.0 if a.get("telefono") and a["telefono"] == b.get("telefono") else 0.0
    s_dom    = 1.0 if a.get("dominio")  and a["dominio"]  == b.get("dominio")  else 0.0

    return (0.30*s_nombre + 0.20*s_dir + 0.25*s_geo + 0.15*s_tel + 0.10*s_dom)
```

**Umbrales:**

| Score | Acción |
|---|---|
| ≥ 0,88 | Fusión automática |
| 0,68 – 0,88 | Cola de revisión manual (`flags += ["POSIBLE_DUPLICADO"]`) |
| < 0,68 | Entidades distintas |

**Paso 3 — Regla de marca (el caso English Connection)**

El problema: 18 sedes de English Connection tienen `s_nombre ≈ 0,95`, `s_dom = 1,0` y `s_tel` frecuentemente 1,0 (centralita). Con los pesos de arriba, dos sedes distintas puntúan ~0,80 y caerían en revisión manual — 153 pares para 18 sedes. Inaceptable.

```python
def es_colision_de_marca(a, b) -> bool:
    """True si comparten marca pero son sedes físicamente distintas."""
    misma_marca = (a.get("marca_id") and a["marca_id"] == b.get("marca_id")) or \
                  (a.get("dominio") and a["dominio"] == b.get("dominio"))
    if not misma_marca:
        return False
    d = haversine(a["lat"], a["lng"], b["lat"], b["lng"]) if todos_coords(a, b) else None
    if d is not None and d > 200:
        return True                      # dos puntos separados = dos sedes
    if a.get("cp") and b.get("cp") and a["cp"] != b["cp"]:
        return True
    return False

def score_final(a, b):
    if es_colision_de_marca(a, b):
        # La marca deja de ser evidencia. Solo cuenta la geografía.
        return 0.75 * s_geo(a, b) + 0.25 * s_dir(a, b)
    return score_par(a, b)
```

Efecto: dos sedes de English Connection a 3 km puntúan ~0,0–0,2 → distintas, sin revisión. Dos registros de la *misma* sede recogidos por Places y por el localizador puntúan ~0,95 → fusión automática. **Esta es la regla que el censo actual no tenía y que produjo el sesgo D5 y la propagación D2.**

**Paso 4 — Cotejo contra las 70 fichas existentes**

```python
# baseline_70.json entra al deduplicador como una fuente más, con prioridad de supervivencia:
#  - si un candidato nuevo casa con una ficha existente -> es ACTUALIZACIÓN (se conserva el `id`)
#  - si no casa con ninguna                             -> es ALTA
#  - si una ficha existente no casa con nada en 3 fuentes independientes -> flag REVISAR_EXISTENTE
#
# Salida obligatoria de esta etapa, tres ficheros:
#   altas.json          -> centros nuevos
#   actualizaciones.json-> campos que cambian en fichas existentes (con diff)
#   conflictos.json     -> pares 0,68-0,88 para revisión humana
```

**Paso 5 — Precedencia de campos en la fusión**

| Campo | Fuente preferente (de mayor a menor) |
|---|---|
| `nombre` | Web oficial → localizador de marca → ACEIA → Places → directorio |
| `direccion` | CartoCiudad geocodificada → web oficial → Places → directorio |
| `lat`/`lng` | CartoCiudad → Places → OSM → geocodificación de la dirección |
| `telefono` | Web oficial → Places → directorio |
| `email` | **Web oficial únicamente** (ver §7.3) |
| `web` | Places → resultado de búsqueda → directorio |
| `estado` | Places `businessStatus` → verificación manual |

### 6.6 Enriquecimiento

Para cada centro con `web` conocida, una pasada con `playwright`:

```python
RUTAS_CONTACTO = ["/contacto", "/contact", "/contactanos", "/donde-estamos", "/localizacion",
                  "/sedes", "/centros", "/quienes-somos", "/aviso-legal", "/politica-privacidad"]
RUTAS_EMPLEO   = ["/trabaja-con-nosotros", "/empleo", "/jobs", "/careers", "/unete",
                  "/trabaja-en", "/rrhh", "/work-with-us", "/vacantes"]

RE_EMAIL = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
RE_TEL   = r"(?:\+34[\s.\-]?)?(?:9[1-8]\d|6\d{2}|7[1-9]\d)[\s.\-]?\d{2}[\s.\-]?\d{2}[\s.\-]?\d{2}"
```

Puntos finos:

1. **La página de aviso legal es la mejor fuente de datos identificativos**: el art. 10 de la LSSI obliga a publicar denominación social, NIF, domicilio y email. Rinde más que `/contacto` y da el **NIF**, que es la clave de deduplicación más fuerte que existe. Priorizarla.
2. **Emails ofuscados**: buscar también `mailto:`, `data-email`, texto con " arroba ", " (at) ", `&#64;`, e imágenes (descartar sin OCR).
3. **Coordenadas embebidas**: extraer de `<iframe src="google.com/maps/embed?...!3dLAT!4dLNG">`, de JSON-LD `@type: LocalBusiness → geo`, y de microdatos `itemprop="latitude"`. JSON-LD es la mina: suele traer nombre, dirección, teléfono, horario y coordenadas de una vez.

```python
import json
def extraer_jsonld(html):
    """LocalBusiness/EducationalOrganization en JSON-LD: la fuente estructurada más limpia."""
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.S):
        try:
            data = json.loads(m.group(1))
        except Exception:
            continue
        for node in (data if isinstance(data, list) else [data]):
            t = node.get("@type", "")
            if any(k in str(t) for k in ("LocalBusiness", "EducationalOrganization", "School", "Organization")):
                yield node
```

4. **Detección de página de empleo**: probar `RUTAS_EMPLEO` + buscar en el HTML de la home enlaces cuyo texto contenga `trabaja|empleo|únete|careers|jobs|vacante`. Si existe → `url_empleo` y `confianza_contratacion=ALTA`.
5. **Tipo de email**: clasificar en `GENERICO` (`info@`, `contacto@`, `secretaria@`, `admin@`) vs `PERSONAL` (`nombre.apellido@`). Determina el tratamiento RGPD (§6.7).

### 6.7 Rate limits, reintentos, caché

```python
import httpx, hashlib, sqlite3, time, random
from pathlib import Path

class Fetcher:
    """Caché en disco + backoff exponencial + límite por dominio."""
    def __init__(self, cache_dir="cache", ttl_dias=7, delay_por_dominio=2.0):
        self.dir = Path(cache_dir); self.dir.mkdir(exist_ok=True)
        self.ttl = ttl_dias * 86400
        self.delay = delay_por_dominio
        self.ultimo = {}

    def get(self, url, **kw):
        key = hashlib.sha256(url.encode()).hexdigest()
        f = self.dir / f"{key}.html"
        if f.exists() and (time.time() - f.stat().st_mtime) < self.ttl:
            return f.read_text(encoding="utf-8", errors="replace")

        dom = httpx.URL(url).host
        espera = self.delay - (time.time() - self.ultimo.get(dom, 0))
        if espera > 0:
            time.sleep(espera + random.uniform(0, 0.5))

        for intento in range(5):
            try:
                r = httpx.get(url, timeout=30, follow_redirects=True,
                              headers={"User-Agent": "censo-academias-sevilla/1.0 (+contacto@ejemplo.es)"},
                              **kw)
                self.ultimo[dom] = time.time()
                if r.status_code == 429:
                    time.sleep(int(r.headers.get("Retry-After", 2 ** intento * 5)))
                    continue
                if r.status_code >= 500:
                    time.sleep(2 ** intento); continue
                r.raise_for_status()
                f.write_text(r.text, encoding="utf-8")
                return r.text
            except httpx.HTTPError:
                if intento == 4: raise
                time.sleep(2 ** intento + random.uniform(0, 1))
```

Límites por fuente:

| Fuente | Límite a respetar |
|---|---|
| Google Places | Cuota dura en consola. Sin límite de tasa práctico dentro de la franquicia |
| Overpass público | ≥5 s entre consultas; 2 slots; respetar `Retry-After`. >20 consultas → extracto local |
| Nominatim | **1 req/s máximo, obligatorio**, con `User-Agent` identificativo |
| Wayback CDX | ~1 req/s; sin autenticación |
| Webs de centros | 2 s por dominio; horario diurno |
| Redes sociales | Volumen mínimo; sesión real; asumir bloqueo |

### 6.8 Consideraciones legales y éticas

**`robots.txt` y ToS**

- Comprobar `robots.txt` **antes** de cada fuente nueva. **Comprobado el 15/08/2026: `aceia.es` bloquea el acceso automatizado.** Su directorio se consulta manualmente en navegador, y la extracción se hace del contenido visualizado. Es legítimo y es lento: presupuestar tiempo humano para ello.
- **Google Maps Platform**: prohibido almacenar de forma permanente contenido de Places salvo `place_id`. **Implicación de arquitectura**: los datos de Places viven en `cache/` y en `raw/` como material de trabajo con TTL; lo que se publica en el repositorio debe estar **reverificado contra la web oficial del centro** o contra una fuente sin esa restricción (OSM, ACEIA, web propia). Esto no es opcional y afecta a la mayoría de las fichas: presupuestar la pasada de reverificación en la Fase 5.
- **OpenStreetMap (ODbL)**: permite almacenar y publicar, pero exige atribución y tiene cláusula de *share-alike* para bases de datos derivadas. **Si el censo publicado incorpora datos de OSM, puede quedar sujeto a ODbL en su conjunto.** Mitigación limpia: usar OSM como fuente de **descubrimiento** (saber que un centro existe) y tomar los valores de campo de la web oficial del centro. Añadir en cualquier caso el crédito de OSM en el pie de `index.html` — los tiles de Carto que ya usa el mapa lo requieren igualmente.
- Scraping de páginas web públicas de empresas para datos de contacto profesional: admisible con moderación de volumen y sin eludir medidas técnicas de protección. No usar rotación de proxies ni resolución de CAPTCHAs.

**RGPD**

| Dato | Naturaleza | Tratamiento |
|---|---|---|
| `info@academia.es`, `secretaria@centro.es` | Dato de **persona jurídica** → fuera del ámbito del RGPD (art. 19 LOPDGDD para datos de empresarios individuales en su condición de tales) | Almacenamiento y publicación admisibles |
| `maria.lopez@academia.es` | **Dato personal** | Base jurídica: interés legítimo (art. 6.1.f). Publicar en un repositorio público **no** es proporcionado. **Recomendación: no publicar emails nominativos; guardarlos en un fichero local no versionado y usar el genérico en el repo** |
| Nombre del director/a extraído de la web | Dato personal | No incorporar al censo. No aporta al objetivo |
| Teléfono fijo del centro | Persona jurídica | Admisible |
| Teléfono móvil publicado como contacto del centro | Frontera | Tratar como dato de empresa si figura como contacto oficial |

Añadir un `AVISO.md` en el repositorio: finalidad (candidaturas espontáneas de un particular), fuentes, y procedimiento de retirada a petición (una dirección de contacto y compromiso de eliminación). Cuesta diez minutos y cubre la única exposición real del proyecto.

**Envío de candidaturas**: la LSSI (art. 21) restringe las comunicaciones **comerciales** no solicitadas. Una candidatura espontánea de empleo no es comunicación comercial, luego no aplica. Sí aplica el sentido común: un envío por centro, sin automatización masiva, sin listas de distribución.

---

## 7. Verificación y control de calidad

### 7.1 Protocolo de verificación por ficha

Un centro se acepta como **real, activo y que imparte inglés** si acumula evidencia en los **tres ejes**:

| Eje | Evidencia aceptable | Peso |
|---|---|---|
| **Existencia** | Web propia activa · ficha en Places con `businessStatus=OPERATIONAL` · presencia en registro oficial · listado en ACEIA o red de preparadores | obligatorio |
| **Local físico** | Dirección con número de portal geocodificada a nivel `PORTAL` · foto de fachada · dirección en aviso legal | obligatorio |
| **Imparte inglés** | Página de cursos de inglés · centro preparador de una certificación de inglés · oferta de empleo de profesor de inglés · reseña reciente que mencione clases de inglés | obligatorio |
| **Actividad reciente** | Actualización de web · post en RRSS <6 meses · oferta de empleo <12 meses · reseña <12 meses | recomendado |

**Niveles de confianza:**

| Nivel | Condición | Publicable |
|---|---|---|
| `ALTA` | ≥2 fuentes independientes **y** web oficial verificada **y** los tres ejes cubiertos | Sí |
| `MEDIA` | ≥2 fuentes independientes, o 1 fuente + web oficial. Falta un eje | Sí, con `flags` visible |
| `BAJA` | 1 sola fuente, sin web oficial | No. Va a cola de verificación manual |
| `SOSPECHOSA` | Cualquier `flag` de §7.3 activo | No, hasta resolución |

**Definición de "fuente independiente"** (crítica para §7.5): dos fuentes son independientes si no derivan la una de la otra. **No son independientes**: Google Places y cualquier directorio que importe fichas de Google; dos directorios de un mismo grupo editorial; el localizador de una marca y su propia web. **Sí lo son**: Places, OSM, ACEIA, la red de preparadores Cambridge, un portal de empleo y el BORME. El pipeline debe registrar `familia_fuente` para poder aplicar esta distinción.

### 7.2 Detección de centros cerrados, fusionados o renombrados

```python
SENALES_CIERRE = {
    "places_closed":     3,   # businessStatus == CLOSED_PERMANENTLY
    "web_caida":         2,   # DNS no resuelve, o HTTP 4xx/5xx persistente en 3 intentos separados
    "dominio_expirado":  3,   # WHOIS: sin registrar o en redemption
    "sin_rrss_12m":      1,
    "sin_resenas_18m":   1,
    "wayback_ultimo_ok": 2,   # última captura con contenido vivo hace >24 meses
}
# >= 4 puntos -> estado = CERRADO_PROBABLE, requiere confirmación manual (llamada telefónica)
# >= 6 puntos -> estado = CERRADO, se mueve a excluidos.json
```

**Renombrados y fusiones**: si un centro nuevo comparte teléfono E.164 **o** NIF **o** coordenadas (≤50 m) con uno marcado como cerrado, es un **renombramiento**, no un alta. Conservar el `id` original, añadir `nombre_anterior[]`. Este patrón es frecuente en el sector (traspasos, cambio de franquicia). El Wayback sobre el dominio antiguo lo confirma.

### 7.3 Reglas automáticas para errores de propagación de campos

Las reglas están calibradas contra los defectos reales medidos en §1.2 y **deben detectarlos todos** al ejecutarse sobre `baseline_70.json`. Ese es su test de aceptación.

```python
from collections import defaultdict

def detectar_propagacion(centros):
    flags = defaultdict(list)

    # R1 — DIRECCIÓN idéntica en municipios distintos. ERROR DURO, sin excepciones.
    #      Un local no puede estar en dos municipios.
    por_dir = defaultdict(list)
    for c in centros:
        if c.get("direccion_completa"):
            por_dir[norm_direccion(c["direccion_completa"])].append(c)
    for dir_, grupo in por_dir.items():
        if len({c["municipio"] for c in grupo}) > 1:
            for c in grupo:
                flags[c["id"]].append("DIRECCION_COMPARTIDA_MUNICIPIOS_DISTINTOS")
    # -> debe disparar en C/ Bailén 32 (3 fichas: Sevilla, Carmona, Mairena del Alcor)

    # R2 — EMAIL compartido. NO es error por sí solo (cadenas reales lo hacen).
    #      Es error si además hay incompatibilidad geográfica sin marca común.
    por_email = defaultdict(list)
    for c in centros:
        if c.get("email"):
            por_email[c["email"].lower()].append(c)
    for em, grupo in por_email.items():
        if len(grupo) < 2:
            continue
        municipios = {c["municipio"] for c in grupo}
        marcas     = {c.get("marca_id") for c in grupo}
        misma_marca = len(marcas) == 1 and None not in marcas
        if len(municipios) > 1 and not misma_marca:
            for c in grupo:
                flags[c["id"]].append("EMAIL_COMPARTIDO_MUNICIPIOS_DISTINTOS")
    # -> dispara en secretaria@carmelitassevilla.es (Sevilla/Carmona/Mairena del Alcor,
    #    sin marca_id declarada) y NO dispara en English Connection una vez asignada la marca

    # R3 — Dominio del email incoherente con el dominio de la web
    for c in centros:
        if c.get("email") and c.get("dominio"):
            dom_email = c["email"].split("@")[-1].lower()
            if norm_dominio("http://" + dom_email) != c["dominio"]:
                flags[c["id"]].append("DOMINIO_EMAIL_NO_COINCIDE_WEB")
    # -> dispara en la ficha #47 (web colegiomercedariasevilla.com, email @carmelitassevilla.es)

    # R4 — Teléfono compartido entre centros distantes sin marca común
    por_tel = defaultdict(list)
    for c in centros:
        if c.get("telefono"):
            por_tel[c["telefono"]].append(c)
    for tel, grupo in por_tel.items():
        if len(grupo) < 2: continue
        if len({c.get("marca_id") for c in grupo}) == 1 and grupo[0].get("marca_id"): continue
        for a, b in combinaciones(grupo, 2):
            if todos_coords(a, b) and haversine(a["lat"],a["lng"],b["lat"],b["lng"]) > 2000:
                flags[a["id"]].append("TELEFONO_COMPARTIDO_DISTANTE")
                flags[b["id"]].append("TELEFONO_COMPARTIDO_DISTANTE")

    # R5 — Coordenadas fuera del polígono del municipio declarado
    for c in centros:
        if c.get("lat") and not punto_en_municipio(c["lat"], c["lng"], c["municipio"]):
            flags[c["id"]].append("COORDENADAS_FUERA_MUNICIPIO")
    # -> detecta #9 y #11 (Col. Internacional Almenar en Dos Hermanas y Col. San Hermenegildo
    #    en Montequinto comparten lat/lng 37.283689/-5.9226718: uno de los dos está mal)

    # R6 — Sin coordenadas
    for c in centros:
        if c.get("lat") is None:
            flags[c["id"]].append("SIN_COORDENADAS")
    # -> #67, #68, #69, #70

    # R7 — CP incoherente con el municipio
    for c in centros:
        if c.get("cp") and c["cp"] not in cps_de(c["municipio"]):
            flags[c["id"]].append("CP_INCOHERENTE")

    return flags
```

**Regla de reparación (no solo detección):** cualquier ficha con `DIRECCION_COMPARTIDA_MUNICIPIOS_DISTINTOS` o `EMAIL_COMPARTIDO_MUNICIPIOS_DISTINTOS` pierde el campo afectado (`= null`) y pasa a cola de reenriquecimiento desde su web oficial. **Un campo vacío es correcto; un campo con el dato de otro centro es una mentira que además contamina la deduplicación.** Este es el arreglo directo de D2 y D3.

### 7.4 Auditoría por muestreo

Muestreo aleatorio estratificado por tipología y corona, con verificación manual (visita a la web, comprobación en Places, y llamada telefónica en la submuestra dudosa).

```
Tamaño de muestra para estimar la tasa de error con precisión ±5% y confianza 95%:
    n = Z²·p·(1-p) / e²  con Z=1,96, p=0,5 (peor caso), e=0,05  ->  n = 384
Corrección para población finita (N ≈ 250):
    n_ajustado = n / (1 + (n-1)/N) = 384 / (1 + 383/250) ≈ 152
```

152 verificaciones manuales sobre ~250 fichas es el 60% del censo — desproporcionado. Con una tolerancia realista de ±10%:

```
n = 1,96²·0,25/0,10² = 96  ->  n_ajustado = 96/(1+95/250) ≈ 70
```

**Recomendación: muestra de 40 fichas** (±13% de precisión), estratificada:

| Estrato | Fichas a auditar |
|---|---|
| Confianza ALTA | 10 |
| Confianza MEDIA | 15 |
| Detectadas por una sola fuente | 10 |
| Fichas preexistentes (las 70 originales) | 5 |

**Procedimiento por ficha auditada** (≈4 min): (1) abrir la web y confirmar que ofrece inglés; (2) confirmar dirección en el aviso legal o la página de contacto; (3) confirmar en Places que sigue operativo; (4) registrar `verificado_manualmente=true`, `ultima_verificacion`. Total: ~2,5 h.

**Criterio de aceptación**: si la tasa de error del estrato ALTA supera el 5%, las reglas de confianza están mal calibradas → revisar §7.1 antes de publicar.

### 7.5 Criterio de parada cuantitativo

**Modelo base — Lincoln-Petersen con corrección de Chapman (dos fuentes)**

Con dos fuentes independientes A y B:

```
n1 = centros hallados por A
n2 = centros hallados por B
m2 = centros hallados por AMBAS

Lincoln-Petersen:   N̂ = (n1 · n2) / m2

Chapman (sesgo menor con muestras pequeñas, siempre preferible):
    N̂ = ((n1 + 1)(n2 + 1) / (m2 + 1)) − 1

Varianza de Chapman:
    Var(N̂) = ((n1+1)(n2+1)(n1−m2)(n2−m2)) / ((m2+1)²(m2+2))

IC 95%:  N̂ ± 1,96 · √Var(N̂)
```

**Supuestos y cuándo se violan:**

| Supuesto | Se viola cuando | Efecto | Mitigación |
|---|---|---|---|
| **Población cerrada** | Abren o cierran academias durante el barrido | Sesgo pequeño si el barrido dura <4 semanas | Fijar fecha de corte; `PROXIMA_APERTURA` no cuenta |
| **Independencia de fuentes** | Un directorio importa fichas de Google → `m2` inflado artificialmente → **N̂ infraestimado** | **Este es el fallo dominante en la práctica** | Usar solo pares genuinamente independientes (§7.1). Nunca emparejar Places con un directorio que use datos de Google |
| **Equiprobabilidad de captura** | Las academias grandes y con SEO aparecen en todas las fuentes; las pequeñas en ninguna | **N̂ infraestimado, a veces mucho** | Usar Chao1 (abajo), que es robusto a heterogeneidad |
| **Identificación perfecta** | Falla la deduplicación → un mismo centro cuenta como dos → `m2` deflactado → **N̂ sobreestimado** | Auditar `conflictos.json` antes de calcular | |

**Pares recomendados para Lincoln-Petersen en este proyecto:**

| A | B | Independencia |
|---|---|---|
| Google Places | Red de preparadores Cambridge | Alta ✓ |
| Google Places | ACEIA | Alta ✓ |
| OSM/Overpass | ACEIA | Alta ✓ |
| Portales de empleo | Google Places | Media–alta ✓ |
| Google Places | Directorio vertical de formación | **Baja ✗ — no usar** |

**Modelo preferido — Chao1 con k fuentes (robusto a heterogeneidad)**

Con k>2 fuentes, construir la distribución de frecuencia de captura: para cada centro, en cuántas fuentes independientes aparece.

```
S_obs = centros distintos observados
f1    = centros observados en EXACTAMENTE 1 fuente
f2    = centros observados en EXACTAMENTE 2 fuentes

Chao1:              N̂ = S_obs + f1² / (2·f2)                 (si f2 > 0)
Chao1 corregido:    N̂ = S_obs + f1(f1−1) / (2(f2+1))         (si f2 = 0, o f1 pequeño)

Cobertura estimada de la muestra (Good-Turing):
    Ĉ = 1 − f1 / n_total_capturas
```

```python
from collections import Counter

def chao1(frecuencias_captura):
    """frecuencias_captura: lista con el nº de fuentes independientes en que aparece cada centro."""
    S_obs = len(frecuencias_captura)
    c = Counter(frecuencias_captura)
    f1, f2 = c.get(1, 0), c.get(2, 0)
    if f2 > 0:
        N = S_obs + (f1 ** 2) / (2 * f2)
    else:
        N = S_obs + (f1 * (f1 - 1)) / 2
    n_capturas = sum(frecuencias_captura)
    cobertura_muestral = 1 - f1 / n_capturas if n_capturas else 0
    return {"S_obs": S_obs, "f1": f1, "f2": f2,
            "N_estimado": round(N, 1),
            "cobertura_censo": round(S_obs / N, 3) if N else 0,
            "cobertura_muestral_good_turing": round(cobertura_muestral, 3),
            "faltan_estimados": round(N - S_obs, 1)}
```

**Interpretación de `f1`**: si muchos centros aparecen en una sola fuente, el universo tiene una cola larga que aún no se ha tocado → seguir buscando. Si `f1` cae hacia 0, cada fuente nueva confirma lo ya conocido → saturación.

**Criterio de parada — se cumplen las tres condiciones:**

```
C1.  Cobertura estimada:      S_obs / N̂_Chao1  ≥  0,92
C2.  Rendimiento marginal:    la última fuente completa aportó < 3% de centros nuevos
C3.  Cobertura geográfica:    ≥ 1 barrido completo ejecutado en los 46 municipios,
                              y ningún municipio de la Corona 1 con 0 centros hallados
```

**Umbral de 0,92, no de 0,99**: el coste marginal crece de forma explosiva. Pasar del 92% al 98% cuesta aproximadamente tanto como todo el trabajo previo, y las últimas academias son las más pequeñas y menos susceptibles de contratar — precisamente las de menor valor para el objetivo del usuario. Un censo del 92% documentado y honesto es superior a uno del 98% sin trazabilidad.

**Publicar siempre la estimación** en el repositorio: `"cobertura_estimada": 0.93, "N_estimado": 247, "faltan_aprox": 17, "metodo": "Chao1", "fecha": "2026-08-25"`. Convierte el censo en un documento con márgenes de error declarados en lugar de una lista sin contexto.

### 7.6 Plan de mantenimiento

| Periodicidad | Subconjunto | Coste | Objetivo |
|---|---|---|---|
| **Semanal** | Portales de empleo (§5.8) | 15 min automatizado | Detectar contratación activa. Es lo que de verdad importa para candidaturas |
| **Mensual** | Places `businessStatus` + HTTP HEAD a todas las webs | 30 min | Detectar cierres y webs caídas |
| **Trimestral** | Localizadores de franquicia + ACEIA + listas de preparadores | 2 h | Nuevas aperturas: el canal por el que llegan casi todas |
| **Semestral** | Barrido completo de Places con teselado + recálculo de Chao1 | 4 h | Recalibrar cobertura |
| **Anual** | Todas las fuentes, incluidos niveles 3–4 + auditoría de 40 fichas | 12 h | Censo completo |
| **Continuo** | Reglas de §7.3 en cada build | 0 (CI) | Impedir reintroducción de D2/D3 |

Automatizable con un workflow de GitHub Actions que ejecute `verify.py` en cada push y falle el build si alguna regla de §7.3 dispara sobre `data/centros.json`. Es la garantía estructural de que los defectos actuales no vuelven.

---

## 8. Plan de ejecución por fases

Ordenadas por ratio hallazgos/esfuerzo. Los rendimientos son estimaciones sobre el modelo de §3 y deben recalibrarse tras la Fase 1.

### Fase 0 — Baseline y andamiaje (45 min)

- **Objetivo**: dataset de partida limpio y detección de los defectos conocidos.
- **Acciones**: ejecutar `baseline_extract.py` (§1.4); aplicar `detectar_propagacion` (§7.3) y confirmar que dispara en los 5 casos medidos; crear `data/centros.json` y `data/excluidos.json`; resolver D4 (decidir si San Francisco de Paula entra o sale, y hacer coherentes nota y ficha); asignar `marca_id=english_connection` a las 18 fichas.
- **Rendimiento**: 0 centros nuevos.
- **Criterio de paso**: las 70 fichas están en JSON con `flags` poblados y las reglas de §7.3 tienen sus 5 aciertos.

### Fase 1 — Las primeras dos horas (el grueso de lo que falta)

| Bloque | Minutos | Fuente | Nuevos esperados |
|---|---|---|---|
| 1A | 15 | **Comprobar si Consumo (Junta) publica un listado de centros de enseñanza no reglada** (§4.3). Apuesta de mayor valor esperado | 0–120 (todo o nada) |
| 1B | 30 | **Google Places, teselado adaptativo de Sevilla capital** (~90 celdas, `language_school` + Text Search por los 11 distritos) | 60–100 |
| 1C | 20 | **ACEIA**: recorrer el buscador de centros asociados (manual, robots.txt lo exige) | 15–35 (solape alto con 1B) |
| 1D | 25 | **Listas de centros preparadores Cambridge**: Instituto Británico de Sevilla, Exams Andalucía, Exams-Sevilla, SevillaCert (LanguageCert), emacarena | 25–50 |
| 1E | 30 | **Franquicias**: descubrir marcas (§5.2 pasos 1–3) y recorrer localizadores de las que tengan sede en el ámbito | 20–45 |

- **Objetivo**: pasar de ~18 academias a ~140–200 en dos horas.
- **Rendimiento acumulado esperado: +120 a +180 centros nuevos.**
- **Criterio de paso**: `S_obs ≥ 130` y primer cálculo de Chao1 disponible. Si el resultado es <90, el barrido tiene un fallo sistemático (revisar cobertura de teselado y filtros de tipo antes de continuar).

> **Por qué este orden**: 1B da la base geográfica sobre la que todo lo demás se deduplica; 1C y 1D son listas curadas de alta precisión que aportan lo que Places pierde (centros sin ficha de Google); 1E ataca directamente el sesgo D5. 1A va primero porque es barato y, si acierta, cambia la prioridad del resto.

### Fase 2 — Extensión geográfica y segundas fuentes de mapas (3 h)

- **Objetivo**: cubrir los 45 municipios restantes y las fuentes cartográficas alternativas.
- **Fuentes**: Places teselado de las Coronas 1–3 (~420 celdas); Overpass Q1–Q4; Bing/HERE; dorks por municipio (§5.4).
- **Rendimiento esperado**: +40 a +80.
- **Criterio de paso**: los 46 municipios barridos; cobertura Chao1 ≥ 0,80.

### Fase 3 — Fuentes de actividad y cola larga (4 h)

- **Objetivo**: centros sin presencia cartográfica + prueba de contratación.
- **Fuentes**: portales de empleo (§5.8); Trinity, LanguageCert, Aptis, OTE, IELTS; directorios verticales; redes sociales por geolocalización; listados agregados de terceros (§5.3); registro de la Junta para la tipología 7.
- **Rendimiento esperado**: +20 a +45, con **alto valor cualitativo**: aquí es donde se identifica quién contrata de verdad.
- **Criterio de paso**: cobertura Chao1 ≥ 0,88.

### Fase 4 — Rescate y fuentes indirectas (3 h)

- **Objetivo**: cerrar la cola.
- **Fuentes**: BORME/CNAE 8559; licencias de apertura y datos abiertos municipales; Wayback sobre directorios muertos; FUNDAE; subvenciones y convenios; prensa local y foros de expatriados.
- **Rendimiento esperado**: +8 a +25. Rendimiento decreciente evidente.
- **Criterio de paso**: cobertura Chao1 ≥ 0,92 → **PARADA** (§7.5).

### Fase 5 — Enriquecimiento, verificación y publicación (4 h)

- **Objetivo**: convertir candidatos en fichas publicables.
- **Acciones**: `enrich.py` sobre todas las webs (email, teléfono, `/trabaja-con-nosotros`, JSON-LD, coordenadas); geocodificación con CartoCiudad; **reverificación de los datos procedentes de Places contra la web oficial** (§6.8 — obligatorio, no opcional); ejecución completa de §7.3; auditoría por muestreo de 40 fichas; `build_html.py`; commit.
- **Rendimiento**: 0 centros nuevos, pero es la fase que determina si el censo sirve para algo.

**Presupuesto total: ~17 horas de ejecución.** Las 2 primeras aportan aproximadamente el 65% del resultado.

---

## 9. Riesgos y modos de fallo

| Riesgo | Probabilidad | Detección | Mitigación |
|---|---|---|---|
| **Truncamiento silencioso de la API** — una celda satura en 20 resultados y no avisa | **Alta** | Registrar `len(resultados)` de cada celda; cualquier celda con exactamente 20 (o 60 con paginación) es sospechosa | Teselado adaptativo obligatorio (§5.6). **Nunca aceptar el recuento de una celda saturada** |
| **Bloqueo antibot** en localizadores y RRSS | Alta | HTTP 403/429, CAPTCHA, contenido vacío con HTTP 200 | Bajar tasa, `User-Agent` real, sesión con navegador. **No usar rotación de proxies ni resolver CAPTCHAs**: cruza la línea de los ToS |
| **Sesgo de directorios de pago** — solo listan a quien paga, e incluyen centros muertos | Alta | Comparar la tasa de coincidencia del directorio con Places; si <40%, el directorio está caduco | Marcar `familia_fuente=DIRECTORIO_PAGO`, `confianza≤MEDIA`, y **excluirlos del cálculo de captura-recaptura** |
| **Falsos positivos: academias de otras materias** | Alta | "Academia" en el nombre sin evidencia de inglés | Regla del eje 3 de §7.1: sin evidencia de inglés, no entra. Nunca inferir por el nombre |
| **Centros fantasma** (existen solo en directorios desactualizados) | Media | Web caída + sin Places + sin RRSS | Regla de §7.2. Requerir ≥2 fuentes independientes **de familias distintas** |
| **Violación de independencia en captura-recaptura** → cobertura sobreestimada → parada prematura | **Alta** | `m2` anómalamente alto entre dos fuentes | Solo usar los pares de §7.5. Preferir Chao1 sobre Lincoln-Petersen |
| **Deduplicación agresiva** — fusiona sedes distintas de la misma marca (repetiría D5 en espejo) | **Alta** | Recuento de sedes por marca menor que el del localizador oficial | Regla de colisión de marca (§6.5 paso 3). **Test de regresión: las 18 sedes de English Connection deben seguir siendo 18** |
| **Deduplicación laxa** — el mismo centro entra dos veces con nombres distintos | Media | Pares con teléfono o NIF idéntico y `id` distinto | Blocking por teléfono y NIF; revisar `conflictos.json` |
| **Restricción de almacenamiento de Google** ignorada | Media | — | Reverificación de Fase 5. Es una obligación contractual, no un consejo |
| **ODbL de OSM contamina la licencia del repo** | Media | — | OSM solo como descubrimiento; valores desde la web oficial (§6.8) |
| **Coste inesperado en Places** por field mask Enterprise | Media | Panel de facturación | Cuota dura por API en consola. Las alertas de presupuesto **no cortan el gasto** |
| **Deriva del alcance** — el censo acaba incluyendo colegios de toda la provincia | Media | Recuento por tipología y municipio | `EXC_FUERA_AMBITO` automático por point-in-polygon |
| **Sobreestimación del universo** por contar sedes de franquicia como centros independientes en la estimación de §3 | Media | Comparar N̂ con y sin agrupación por marca | Publicar ambas cifras: "centros" y "entidades" |
| **El repo cambia bajo los pies** (el usuario edita `index.html` a mano en paralelo) | Media | Hash de `index.html` al inicio y al final | Trabajar sobre rama; `build_html.py` como única vía de escritura |
| **ACEIA u otra fuente clave endurece su `robots.txt` o cierra el buscador** | Baja | 403 / 404 | Ya bloquea el acceso automatizado (comprobado). Extracción manual presupuestada; guardar copia en `raw/` para no repetirla |

---

## Anexo A — Lista cerrada de municipios (POTAUS, 46)

Fuente: Decreto 267/2009, de 9 de junio (BOJA nº 132, 09/07/2009). Códigos INE **[VERIFICAR uno a uno contra el nomenclátor del INE antes de usarlos como clave]**.

| # | Municipio | Corona | # | Municipio | Corona |
|---|---|---|---|---|---|
| 1 | Sevilla | 0 | 24 | Guillena | 2 |
| 2 | Dos Hermanas | 1 | 25 | Huévar del Aljarafe | 3 |
| 3 | Alcalá de Guadaíra | 1 | 26 | Isla Mayor | 3 |
| 4 | Utrera | 1 | 27 | Mairena del Alcor | 2 |
| 5 | Mairena del Aljarafe | 1 | 28 | Olivares | 2 |
| 6 | La Rinconada | 1 | 29 | Palomares del Río | 2 |
| 7 | Los Palacios y Villafranca | 1 | 30 | Pilas | 2 |
| 8 | Camas | 1 | 31 | La Puebla del Río | 2 |
| 9 | Tomares | 1 | 32 | Salteras | 2 |
| 10 | Bormujos | 1 | 33 | Sanlúcar la Mayor | 2 |
| 11 | Carmona | 1 | 34 | Santiponce | 2 |
| 12 | Coria del Río | 1 | 35 | Umbrete | 2 |
| 13 | San Juan de Aznalfarache | 1 | 36 | Valencina de la Concepción | 2 |
| 14 | Castilleja de la Cuesta | 1 | 37 | Villamanrique de la Condesa | 3 |
| 15 | Albaida del Aljarafe | 3 | 38 | Villanueva del Ariscal | 2 |
| 16 | Alcalá del Río | 2 | 39 | El Viso del Alcor | 2 |
| 17 | La Algaba | 2 | 40 | Almensilla | 2 |
| 18 | Aznalcázar | 3 | 41 | Benacazón | 2 |
| 19 | Aznalcóllar | 3 | 42 | Bollullos de la Mitación | 2 |
| 20 | Brenes | 2 | 43 | Castilleja de Guzmán | 2 |
| 21 | Carrión de los Céspedes | 3 | 44 | Castilleja del Campo | 3 |
| 22 | Espartinas | 2 | 45 | Gelves | 2 |
| 23 | Gerena | 3 | 46 | Gines | 2 |

Población total del ámbito: **1.567.491 hab** (INE 2024). Superficie: 4.962 km².

**Subconjunto reducido alternativo** (si S1 resulta demasiado amplio): Corona 0 + Corona 1 = 14 municipios, ~1,15 M hab, ~73% de la población del ámbito y previsiblemente >85% de las academias. Reduce el esfuerzo de las Fases 2 y 4 a la mitad.

---

## Anexo B — Índice de marcas y franquicias a verificar

**Ninguna de estas marcas está confirmada como presente en el ámbito.** Es una lista de arranque para el paso 1 de §5.2, no un hallazgo. Todas van marcadas **[VERIFICAR]** — tanto su existencia actual en España como su presencia en los 46 municipios.

| Marca | Perfil | Estado |
|---|---|---|
| English Connection | Franquicia nacional | **Confirmada**: 18 sedes ya en el censo. Verificar si sigue habiendo 18 |
| Kids&Us | Inmersión infantil, franquicia | [VERIFICAR] |
| Helen Doron English | Inmersión infantil, franquicia internacional | [VERIFICAR] |
| Berlitz | Cadena internacional, adultos y empresas | [VERIFICAR] |
| Wall Street English | Cadena internacional, adultos | [VERIFICAR] |
| Number 16 School | Franquicia nacional | [VERIFICAR] |
| inlingua | Red internacional | [VERIFICAR] |
| Vaughan Systems | In-company, España | [VERIFICAR] |
| International House | Red internacional (CLIC en Sevilla es miembro) | Parcialmente confirmada vía CLIC |
| Centro Norteamericano | Independiente histórico de Sevilla (desde 1958) | Confirmado en el censo (#3) |

**El método importa más que la lista.** El paso 3 de §5.2 —detectar cadenas a partir de nombres repetidos en los datos de Places— es lo que evita repetir el error original: una lista de marcas escrita de memoria reproduce el sesgo de quien la escribe. La detección desde los datos, no.

---

## Marcas [VERIFICAR] pendientes — resumen

Elementos que este plan afirma sin verificación completa y que deben comprobarse antes de invertir tiempo:

1. Existencia de un listado público de centros de enseñanza no reglada en la Dirección General de Consumo (Junta de Andalucía) — **§4.3, máxima prioridad**.
2. Número exacto de centros ACEIA en la provincia de Sevilla (contar en su buscador).
3. Tamaño real de las listas de preparadores Cambridge de Sevilla (§3.2, parámetro P).
4. Validez del tipo `language_school` en `includedTypes` de Places API (New).
5. Paginación en `searchNearby` de Places API (New).
6. Endpoints y límites actuales de CartoCiudad (IGN).
7. Límites de tasa vigentes de la instancia pública de Overpass.
8. URLs de los portales de franquicia españoles (§5.2).
9. Estado y cobertura actuales de los directorios verticales de formación (§4.2).
10. Estado de Páginas Amarillas / QDQ en 2026.
11. Acceso programático a los dumps del BORME y al DIRCE por CNAE a 4 dígitos.
12. Códigos INE de los 46 municipios (Anexo A).
13. Presencia real en el ámbito de cada marca del Anexo B.
14. Datasets de licencias de apertura publicados por cada uno de los 46 ayuntamientos.
15. Que CLIC International House Sevilla imparta CELTA o inglés a terceros (evidencia E1/E4 de §2.4).

**Ninguna URL, endpoint ni nombre de directorio de este documento ha sido inventado.** Los verificados el 15/08/2026 son: la estructura del repositorio, ACEIA (existencia, cifra de 164 centros, `robots.txt` restrictivo), la red de preparadores Cambridge en Sevilla (Instituto Británico / Exams Andalucía / SevillaCert / emacarena), la delimitación POTAUS de 46 municipios, el modelo de precios vigente de Google Maps Platform, y el portal de datos abiertos del Ayuntamiento de Sevilla. Todo lo demás va marcado.
