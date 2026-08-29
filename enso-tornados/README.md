# ¿El Niño cambia la estacionalidad de los tornados en Chile?

Análisis independiente del proyecto de albedo que comparte este
repositorio. Usa la base de datos de tornados y trombas de Chile de
Bastías-Curivil et al. (2024) para preguntar si la fase cálida de ENSO
(El Niño) desplaza o modifica la estacionalidad de los tornados
chilenos, que se concentra entre mediados de mayo y mediados de junio
(Bastías-Curivil et al. 2025, GRL).

## Datos

| Archivo | Contenido | Fuente |
|---|---|---|
| `data/tornados_trombas_chile_bastias2024.csv` | 83 eventos (tornados y trombas) 1554-2023, con fecha, lugar, coordenadas e intensidad EF estimada | Bastías-Curivil et al. (2024), figshare [doi:10.6084/m9.figshare.25119566](https://doi.org/10.6084/m9.figshare.25119566) |
| `data/oni.csv` | Oceanic Niño Index por trimestre móvil 1950-2026, con la clasificación oficial de episodios (±0,5 °C por ≥5 trimestres consecutivos) | [CPC/NOAA `oni.ascii.txt`](https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt), procesado vía [ahuang11/ninodata](https://github.com/ahuang11/ninodata) |

Ambos archivos son instantáneas pequeñas y quedan versionadas aquí para
que el análisis sea reproducible sin red. Para refrescarlas: bajar el
CSV de figshare y regenerar `oni.csv` con el `process_oni.py` de
ninodata (o rehacer la clasificación desde `oni.ascii.txt`).

## Método (`analisis_enso_estacionalidad.py`)

- A cada evento con fecha desde 1950 (72 de los 83) se le asigna el
  trimestre ONI centrado en su mes (mayo → AMJ, etc.): la anomalía
  concurrente y la fase de episodio (El Niño / neutral / La Niña).
- La fecha dentro del año se trata como variable **circular**
  (día del año → ángulo). Para "El Niño" vs "resto" se calculan:
  diferencia de fecha media circular, diferencia de concentración R,
  U² de Watson (todas con test de permutación, 20 000 permutaciones),
  correlación de rangos entre la anomalía ONI y la desviación circular
  respecto de la fecha media climatológica, y la fracción de eventos en
  la temporada núcleo (15 may - 15 jun y may-ago; Fisher exacto).
- Sensibilidad: se repite todo con **días de tornado** (fechas únicas,
  para que el brote del 30-31 de mayo de 2019 no pese 7 veces) y con el
  subconjunto centro-sur (lat ≤ -33°).

Correcciones menores aplicadas al leer la base: coordenadas con coma
decimal, y el evento 65 (Lago Villarrica 2021) trae la longitud en la
columna de latitud; se usa la latitud del lago para el filtro espacial.

### Eventos provisionales de 2026

`data/eventos_2026_provisional.csv` recoge los eventos de 2026
reportados en prensa que aún no están curados en la base (temporadas de
julio y agosto: Lago Llanquihue 24-jul; Chillán Viejo y Bulnes 27-jul,
F1 preliminar DMC; Larque Oriente 8-ago; y el episodio del 27-29 de
agosto: trombas de Constitución y Tomé y el tornado de Yungay-Cholguán).
**Esta lista es un borrador para curatoría** — editar ese CSV (agregar,
quitar, corregir fechas/coordenadas) y volver a correr el script. Como
el ONI de JAS 2026 aún no se publica, estos eventos usan la última
anomalía disponible (AMJ 2026: +0.98 °C) y una fase por umbral ±0.5 °C
solamente ("El Niño provisional": la regla de episodio de ≥5 trimestres
no puede aplicarse a un evento en curso). El análisis los trata como
variante aparte y nunca los mezcla con el resultado principal.

## Resultados (instantánea 2024 de la base; `output/resultados.txt`)

- **La estacionalidad es fuerte en todas las fases** (Rayleigh
  p < 0.001 en cada grupo): ENSO no crea ni destruye la temporada.
- **Bajo El Niño la temporada tiende a correrse hacia el final del
  invierno**: fecha media 26 jun (eventos) o 2 jul (días de tornado)
  contra 5-11 jun en el resto, es decir +17 a +27 días. Los únicos
  eventos de fin de temporada (septiembre) ocurren bajo El Niño
  (ASO 2018, +1.6 °C en sep 2023). La tendencia es consistente en las
  cuatro variantes pero **no alcanza significancia al 5 %**: el mejor
  caso es la diferencia de fecha media en días de tornado
  (p ≈ 0.08-0.09); Watson U² da p ≈ 0.14-0.42.
- La concentración de la temporada es algo mayor bajo El Niño
  (ΔR ≈ +0.14 a +0.22, p ≈ 0.15-0.27), y no hay correlación entre la
  anomalía ONI y cuán lejos del centro de la temporada cae un evento.
- **Frecuencia** (secundario): 24 de 72 eventos ocurren en episodios El
  Niño contra 18.8 esperados por la fracción de meses El Niño
  (binomial exacto p ≈ 0.18, y anticonservador porque los brotes no son
  independientes).

**Conclusión (base curada hasta 2023):** con los 72 eventos fechados de
la era ONI, la estacionalidad de los tornados chilenos es robusta a la
fase de ENSO; hay una sugerencia (no significativa) de que El Niño
corre la temporada unas 2-4 semanas hacia el invierno tardío y aporta
los eventos de septiembre. Con ~17-24 eventos cálidos el poder
estadístico es bajo.

### Actualización con los eventos provisionales de 2026

La temporada 2026 (evento cálido en desarrollo: ONI MAM +0.51,
AMJ +0.98 °C) ha producido eventos concentrados en julio y agosto,
es decir exactamente en la cola tardía donde la base 1950-2023 ya
insinuaba el efecto de El Niño. Agregando los 7 eventos provisionales:

- d(fecha media) El Niño - resto = **+29 días (perm p = 0.013)** con
  eventos, **+35 días (p = 0.017)** con días de tornado: la fecha media
  bajo El Niño pasa a ~8-9 de julio contra ~5-9 de junio en el resto.
- La concentración sigue algo mayor bajo El Niño (ΔR +0.17-0.22,
  p ≈ 0.11-0.15); Watson U² p ≈ 0.22-0.29.

Es decir, **con 2026 incluido el corrimiento tardío de la temporada
bajo ENSO cálido se vuelve estadísticamente significativo al 5 %** en
la métrica de fecha media. Cautelas: (1) los eventos 2026 son
provisionales (sin curatoría de la base ni clasificación ONI de
episodio definitiva); (2) 2026 está incompleto — aunque el sesgo de
truncación va en contra del resultado, no a favor, porque solo faltan
meses aún más tardíos; (3) la densidad de reportes moderna infla los
años recientes en ambos grupos por igual, pero un solo año aporta 7 de
los 31 eventos cálidos, así que el resultado descansa fuerte en 2026:
conviene re-testear cuando el ONI de JAS-OND 2026 esté publicado y los
eventos curados. Si más eventos ocurren en septiembre (como en 2018 y
2023, también bajo ENSO cálido), el resultado solo puede reforzarse.

## Uso

```bash
pip install numpy pandas matplotlib
python enso-tornados/analisis_enso_estacionalidad.py
```

Escribe `output/resultados.txt` y la figura
`output/enso_estacionalidad_tornados.{png,pdf}` (histograma mensual por
fase ENSO + fecha del evento contra ONI concurrente).

## Referencias

- Bastías-Curivil, C., et al. (2024). *Tornadoes and Waterspouts in
  Chile / Tornados y Trombas en Chile* (dataset). figshare.
  https://doi.org/10.6084/m9.figshare.25119566
- Bastías-Curivil, C., et al. (2025). Tornado Seasonality in
  Central-Southern Chile. *Geophysical Research Letters*.
  https://doi.org/10.1029/2024GL110900
- Vicencio, J., et al. (2021). The Chilean Tornado Outbreak of May
  2019. *BAMS*.
- NOAA/CPC. Oceanic Niño Index.
  https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
