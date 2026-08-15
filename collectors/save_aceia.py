#!/usr/bin/env python3
"""Guarda los centros ACEIA de provincia Sevilla extraídos del navegador."""
import json

# datos extraídos de https://aceia.es/centros-asociados/ (navegador, 2026-08-15)
raw = """PREMIER SCHOOL OF ENGLISH (Utrera)|https://aceia.es/portfolio/premier-school-of-english-utrera/
BLS IDIOMAS (Sevilla)|https://aceia.es/portfolio/bls-idiomas-sevilla/
ACADEMIA WILLOW (EL SAUCEJO)|https://aceia.es/portfolio/academia-willow-el-saucejo/
REAL ENGLISH – Lebrija|https://aceia.es/portfolio/real-english-lebrija/
Giralda in&out|https://aceia.es/portfolio/giralda-inout/
ELI Triana(SEVILLA)|https://aceia.es/portfolio/eli-sevilla-triana/
Centro de Idiomas Macarena (Macarena)|https://aceia.es/portfolio/centro-de-idiomas-macarena-macarena/
ELI Sevilla Este I (Sevilla)|https://aceia.es/portfolio/eli-sevilla-este-i-sevilla/
GO SPEAK ENGLISH LANGUAGE SCHOOL (Sevilla)|https://aceia.es/portfolio/go-speak-english-language-school-sevilla/
The British School Aljarafe (Castilleja de la Cuesta)|https://aceia.es/portfolio/the-british-school-castilleja-de-la-cuesta/
ELI Camas(Camas)|https://aceia.es/portfolio/eli-camas-camas/
ST. JAMES (San Juan Aznalfarache)|https://aceia.es/portfolio/st-james-san-juan-aznalfarache/
THE LANGUAGE PROJECT (Sevilla Centro)|https://aceia.es/portfolio/the-language-project-sevilla-centro/
TAKE ENGLISH LA NEGRILLA(Sevilla)|https://aceia.es/portfolio/take-english-la-negrilla-sevilla/
ST. JAMES (Mairena Centro)|https://aceia.es/portfolio/st-james-mairena-centro/
CBS LANGUAGE ACADEMY (Bormujos)|https://aceia.es/portfolio/cbs-language-academy-bormujos/
SEVILLA HABLA LANGUAGES (Sevilla)|https://aceia.es/portfolio/sevilla-habla-languages-sevilla/
AMERICAN ENGLISH ACADEMY (Tocina)|https://aceia.es/portfolio/american-english-academy-tocina/
ELI (Montequinto)|https://aceia.es/portfolio/eli-monquiello/
ELI (Bormujos)|https://aceia.es/portfolio/eli-bormujos/
ELI SEVILLA ESTE II (Sevilla)|https://aceia.es/portfolio/eli-sevilla-este-ii-sevilla/
ST. JAMES Bulevar (Mairena del Aljarafe)|https://aceia.es/portfolio/st-james-bulevar-mairena-del-aljarafe/
CENTRO NORTEAMERICANO DE ESTUDIOS INTERCULTURALES(Sevilla)|https://aceia.es/portfolio/centro-norteamericano-de-estudios-interculturales/
ELI Nervión(Sevilla)|https://aceia.es/portfolio/eli-nervionsevilla/
THE BRITISH SCHOOL (Sanlúcar la Mayor)|https://aceia.es/portfolio/the-british-school-sanlucar-la-mayor/
Winchester Language School|https://aceia.es/portfolio/winchester-language-school/
ELI [SANTA JUSTA]Sevilla|https://aceia.es/portfolio/eli-santa-justa-sevilla/
ENGLISH DOS HERMANAS(Dos Hemanas)|https://aceia.es/portfolio/english-dos-hermanas/
AMERICAN LAND ACADEMY IN SPAIN Bollullos de la Mitación|https://aceia.es/portfolio/american-land-academy-in-spain-bollullos-de-la-mitacion/
ELI El Porvenir (Sevilla)|https://aceia.es/portfolio/eli-el-porvenir-sevilla/
THE LANGUAGE PROJECT Tomares|https://aceia.es/portfolio/the-language-project-tomares/
CBS LANGUAGE ACADEMY (Mairena del Aljarafe)|https://aceia.es/portfolio/cbs-language-academy-mairena-del-aljarafe/
ST. JAMES Pilas|https://aceia.es/portfolio/st-james-pilas/
ELI (Macarena) SEVILLA|https://aceia.es/portfolio/eli-sevilla-macarena/
St. James Ciudad Expo(Mairena del Aljarafe)|https://aceia.es/portfolio/st-james-ciudad-expo-mairena-del-aljarafe/
The English Center by Elisabeth|https://aceia.es/portfolio/the-english-center-by-elisabeth/
Centro Clic IH(Sevilla)|https://aceia.es/portfolio/centro-clic-sevilla/
GO SPEAK ENGLISH LANGUAGE SCHOOL 2(Sevilla)|https://aceia.es/portfolio/go-speak-english-language-school-2sevilla/
REAL ENGLISH – El Cuervo|https://aceia.es/portfolio/real-english-sevilla/
ESCUELA IDIOMAS CARLOS V(Sevilla)|https://aceia.es/portfolio/escuela-idiomas-carlos-vsevilla/
SAINT GABRIEL REINA MERCEDES (Sevilla)|https://aceia.es/portfolio/saint-gabriel-reina-mercedes-sevilla/
ELI SEVILLA ESTE III(Sevilla)|https://aceia.es/portfolio/eli-sevilla-este-iiisevilla/
BRITANNIA LEARNING CENTRE (Lebrija)|https://aceia.es/portfolio/britannia-learning-centre-lebrija/
ALBA INGLÉS (Osuna)|https://aceia.es/portfolio/alba-ingles-osuna/
CENTRO DE IDIOMAS (Sevilla – NUEVO TORNEO)|https://aceia.es/portfolio/centro-de-idiomas-sevilla-nuevo-torneo/
PENNY LANE ENGLISH SCHOOL San José de la Rinconada|https://aceia.es/portfolio/penny-lane-english-school/
INSTITUTO SAN FERNANDO DE LA LENGUA ESPAÑOLA (Sevilla)|https://aceia.es/portfolio/instituto-san-fernando-de-la-lengua-espanola-sevilla/
Thompson English Academy|https://aceia.es/portfolio/thompson-english-academy/
TAKE ENGLISH AMATE(Sevilla)|https://aceia.es/portfolio/take-english-amate-sevilla/
Notting Hill|https://aceia.es/portfolio/notting-hill/
ACADEMIA OXFORD (Sevilla)|https://aceia.es/portfolio/academia-oxford-sevilla/
SAINT GABRIEL EDUARDO DATO(Sevilla)|https://aceia.es/portfolio/saint-gabriel-eduardo-dato-sevilla/
TOWER ÉCIJA (FUENTE NUEVA)Ejída|https://aceia.es/portfolio/tower-ecija-fuente-nueva/
THE LANGUAGE PROJECT (Triana)|https://aceia.es/portfolio/the-language-project-triana/
CBS LANGUAGE ACADEMY (Bollullos de la  Mitación)|https://aceia.es/portfolio/cbs-language-academy-bullullos/
Abbla Idiomas|https://aceia.es/portfolio/abbla-idiomas/
ENGLISH 1 (Sevilla)|https://aceia.es/portfolio/english-1-sevilla/"""

rows = []
for line in raw.strip().split("\n"):
    nombre, url = line.split("|")
    rows.append({"nombre": nombre.strip(), "url_aceia": url.strip(), "fuente": "ACEIA", "fecha_captura": "2026-08-15"})

with open("/root/centros_compatibles/raw/aceia_sevilla.jsonl", "w") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"ACEIA Sevilla: {len(rows)} centros guardados")
