# raw/ — datos crudos inmutables (append-only)

Cada colector escribe un JSONL con fecha. **Nunca se sobrescribe.** Permite
recalcular todo el pipeline con reglas nuevas sin volver a pedir datos.

- `overpass_*.jsonl` — consultas Q1-Q3 de Overpass/OSM (2026-08-15)
- `aceia_sevilla.jsonl` — centros ACEIA provincia Sevilla + enriquecimiento (2026-08-15)
- `kidsus_sevilla.jsonl` — sedes Kids&Us en el ámbito POTAUS (2026-08-15)
- `helendoron_sevilla.jsonl` — sedes Helen Doron en el ámbito POTAUS (2026-08-15)

**Nota sobre Google Places**: no se usó en esta ronda (sin API key en el entorno).
El plan §5.6 contempla Places con field mask Pro como fuente Nivel 1 para rondas futuras.

**Nota OSM/ODbL**: los datos de OSM se usan solo como fuente de *descubrimiento*
(saber que un centro existe); los valores publicados se toman de la web oficial
de cada centro cuando existe. Atribución en `index.html` y `AVISO.md`.
