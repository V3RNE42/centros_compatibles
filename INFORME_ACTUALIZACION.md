# Informe de actualización — 15/08/2026

## Resumen ejecutivo
El censo pasa de **70 fichas** (de las cuales solo ~18 eran academias, casi todas de una única cadena) a **183 fichas** con cobertura en **21 municipios** del ámbito POTAUS. La vertiente de academias pasa de ~18 a ~113 centros de idiomas.

## Qué se ha hecho (fases del plan)

### Fase 0 — Baseline (completada)
- `scripts/baseline_extract.py`: extrajo las 70 fichas y las 66 entradas de mapa del `index.html`.
- Reglas §7.3 ejecutadas: **detectadas y confirmadas** las propagaciones D2/D3:
  - `sevilla.losremedios@englishconnection.es` → 18 fichas (caso legítimo de cadena)
  - `secretaria@carmelitassevilla.es` → 5 fichas (propagación errónea → limpiada)
  - `secretaria@colegiosanjosesevilla.com` → 2 fichas (limpiada)
  - Dirección `C/ Bailén 32` en 3 municipios distintos (limpiada en 2)
  - `C/ San José, 5` + teléfono `954218353` en #52 y #53 (duplicado documentado)
- D1 (70 fichas vs 66 coordenadas): resuelto por construcción con `build_html.py`.

### Fase 1 — Recolección (completada en gran parte)
| Fuente | Centros | Estado |
|---|---|---|
| Overpass/OSM (Q1-Q3) | 61 | ✅ barrido bbox metropolitano + geocodificación |
| ACEIA (buscador oficial) | 46 | ✅ extracción manual navegador (robots.txt permite /portfolio/) |
| Helen Doron (localizador JSON) | 8 | ✅ 1241 registros globales, 8 en POTAUS |
| Kids&Us (localizador) | 5 | ✅ confirmadas 5 sedes |
| Total nuevos | 120 | 11 duplicados fusionados, 24 falsos positivos descartados |

**Verificaciones del plan resueltas:**
- **1A (Consumo Junta): NO existe listado público** de centros de enseñanza no reglada. Búsqueda en juntadeandalucia.es y Google News sin resultado. La fuente de mayor valor esperado del plan no existe → se descarta.
- **CLIC International House Sevilla** imparte **CELTA/DELTA** (`clic.es/tefl`) → evidencia E4 → `ELE_MIXTA` (respuesta al [VERIFICAR] #15).
- **Berlitz: NO tiene centro en Sevilla** (solo Madrid, San Sebastián de los Reyes, Barcelona, Valencia) → descartado.
- **English Connection: 17 sedes activas** listadas en su web (el censo tenía 18; **Santa Justa no aparece** en el localizador — posible cierre, marcado para verificación).
- **Helen Doron: 8 sedes** (el plan la marcaba [VERIFICAR]).
- **ACEIA: 57 centros en la provincia de Sevilla** (11 fuera del ámbito POTAUS descartados).

### Fase 5 — Pipeline y publicación (completada)
- `data/centros.json`: esquema canónico (167 fichas con `id`, `fuentes[]`, `confianza`, `flags`).
- `scripts/build_html.py`: única vía de escritura de `index.html`. Fichas y `mapLocations` se generan del mismo registro → D1 resuelto por construcción.
- `AVISO.md`: finalidad, fuentes, RGPD y procedimiento de retirada (§6.8).
- Corrección de emails propagados: 36 emails de plantilla/incoherentes limpiados.

## Pendiente (para próximas rondas)
- Geocodificar los ~38 centros sin coordenadas (faltan direcciones estructuradas ACEIA).
- Verificar si English Connection Santa Justa sigue abierta.
- Fase 3: portales de empleo (InfoJobs/LinkedIn) para confirmar contratación.
- Los municipios de la Corona 2-3 sin cobertura (25) no tienen academias en OSM ni prensa — plausible (baja densidad), pero merecen verificación puntual vía Places en una ronda con API key.
- Recálculo de Chao1 con 3+ fuentes.

## Métricas
- **Fichas totales:** 183 (antes 70)
- **Academias de idiomas (no colegios):** ~113 (antes ~18)
- **Colegios conservados:** 70 (ninguno tocado, S2)
- **Municipios con cobertura:** 21/46
- **Con web:** 120 | **Con teléfono:** 125 | **Con email:** 88 | **Con coordenadas:** 145
- **Estimación del plan:** 180-320 academias → la recolección está en ~113; faltan ~67-207 (Fases 2-3).

## Fase 2 — Extensión geográfica (añadido)
- **OSM local vía Geofabrik PBF** (192 MB, `andalucia-latest.osm.pbf`): barrido del bbox POTAUS completo sin rate limit — 41 candidatos, con coordenadas precisas. Este es el método recomendado por el plan §5.5 para >20 consultas.
- **Overpass API por municipio** (Q4, 46 consultas): 15 nuevos + 12 falsos positivos léxicos descartados (El Corte Inglés, Cementerio de los Ingleses, Ingles Steel...).
- **SevillaCert / LanguageCert**: red de 13 Academic Partners extraída de los iframes de Google Maps de su página — 9 nuevos (Coucke's Academy, Learning Centre, M&J AND You, Moving On School, Native Learn, TEC Sevilla, Wish English, ATENTOS AIAE, Academia Méndez Núñez).
- **Dorks por municipio** (Google News, 26 municipios): solo 13 pistas, 0 confirmaciones — los municipios pequeños no aparecen en prensa.
- **Marcas verificadas y descartadas** (ninguna con sede en el ámbito): Berlitz, Number 16, inlingua, Vaughan (todas solo Madrid/Barcelona/Valencia/Bilbao/Zaragoza/Granada). Patrón: el tejido local es 100% andaluz.
- **Exams Andalucía**: cubre Almería/Granada/Jaén/Málaga, no Sevilla (el Platinum de Sevilla es el Instituto Británico) — no aporta.
- **Trinity College**: no publica buscador público de centros preparadores accesible.
