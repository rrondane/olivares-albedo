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

**Conclusión:** con los 72 eventos fechados de la era ONI, la
estacionalidad de los tornados chilenos es robusta a la fase de ENSO;
hay una sugerencia (no significativa) de que El Niño corre la temporada
unas 2-4 semanas hacia el invierno tardío y aporta los eventos de
septiembre. Con ~17-24 eventos cálidos el poder estadístico es bajo:
detectar un corrimiento de un mes con estos tamaños requiere más o
menos el doble de eventos, así que vale la pena repetir el test cuando
la base crezca (o extenderlo antes de 1950 con índices ENSO
reconstruidos).

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
