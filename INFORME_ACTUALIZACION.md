# Informe de actualización — 15/08/2026

## Resumen ejecutivo
El censo pasa de **70 fichas** (de las cuales solo ~18 eran academias, casi todas de una única cadena) a **167 fichas** con cobertura en **20 municipios** del ámbito POTAUS. La vertiente de academias pasa de ~18 a ~97 centros de idiomas.

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
- Geocodificar los ~33 centros sin coordenadas (faltan direcciones estructuradas ACEIA).
- Verificar si English Connection Santa Justa sigue abierta.
- Fase 2: barrido por dorks de los 26 municipios aún sin cobertura.
- Fase 3: portales de empleo (InfoJobs/LinkedIn) para confirmar contratación.
- Recálculo de Chao1 con 3+ fuentes cuando se complete la Fase 2.

## Métricas
- **Fichas totales:** 167 (antes 70)
- **Academias de idiomas (no colegios):** ~97 (antes ~18)
- **Colegios conservados:** 70 (ninguno tocado, S2)
- **Municipios con cobertura:** 20/46
- **Con web:** 119 | **Con teléfono:** 124 | **Con email:** 88 | **Con coordenadas:** 134
- **Estimación del plan:** 180-320 academias → la recolección inicial ya está en ~97; faltan ~83-223 (Fase 2).
