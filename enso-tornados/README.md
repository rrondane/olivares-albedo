# ¿El Niño cambia la estacionalidad de los tornados en Chile?

Análisis independiente del proyecto de albedo que comparte este
repositorio. Usa la base de datos de tornados y trombas de Chile de
Bastías-Curivil et al. para preguntar si la fase cálida de ENSO
(El Niño) desplaza o modifica la estacionalidad de los tornados
chilenos, que se concentra entre mediados de mayo y mediados de junio
(Bastías-Curivil et al. 2025, GRL).

## Datos

| Archivo | Contenido | Fuente |
|---|---|---|
| `data/tornados_trombas_chile_master_2026-08-06.csv` | `Final_Table` de la planilla maestra de los autores: 116 eventos 1554-2026 (hasta el 27-jul-2026), con fecha, coordenadas, tipo e intensidad EF | Planilla maestra de la base publicada en figshare, [doi:10.6084/m9.figshare.25119566](https://doi.org/10.6084/m9.figshare.25119566) (instantánea del 6-ago-2026; la v5 de figshare es del 14-jul-2025) |
| `data/oni.csv` | Oceanic Niño Index por trimestre móvil 1950-2026 (último trimestre final: AMJ 2026), con la clasificación oficial de episodios (±0,5 °C por ≥5 trimestres consecutivos) | [CPC/NOAA `oni.ascii.txt`](https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt), procesado vía [ahuang11/ninodata](https://github.com/ahuang11/ninodata) |
| `data/eventos_2026_provisional.csv` | Eventos reportados en prensa posteriores a la instantánea maestra (Larque Oriente 8-ago; Constitución, Tomé y Yungay-Cholguán 27-29 ago 2026). **Borrador para curatoría: editar y volver a correr.** | prensa (URLs en el CSV) |

Notas sobre la instantánea maestra: se exportan solo las columnas usadas
aquí; los saltos de línea en `Location` se aplanan y se limpia una coma
perdida en la longitud de CL0100. Ojo: en la planilla maestra hay
**5 UniqueID duplicados** (CL0100-CL0102 y CL0109-CL0110 se reusan entre
eventos históricos nuevos y los de 2025-2026) — no afecta este análisis,
pero conviene corregirlo antes de la próxima versión de figshare.

## Método (`analisis_enso_estacionalidad.py`)

- A cada evento con fecha desde 1950 se le asigna el trimestre ONI
  centrado en su mes (mayo → AMJ, etc.): la anomalía concurrente y la
  fase de episodio (El Niño / neutral / La Niña).
- Los eventos cuyo trimestre ONI aún no se publica (los de jun-jul 2026
  de la base, y los provisionales de prensa) reciben la última anomalía
  final disponible (AMJ 2026: +0.98 °C) con fase por umbral ±0.5 °C
  solamente, quedan marcados **provisionales** y entran solo en las
  variantes "+ 2026 provisional", nunca en el resultado principal.
- La fecha dentro del año se trata como variable **circular**
  (día del año → ángulo). Para "El Niño" vs "resto" se calculan:
  diferencia de fecha media circular, diferencia de concentración R,
  U² de Watson (todas con test de permutación, 20 000 permutaciones),
  correlación de rangos entre la anomalía ONI y la desviación circular
  respecto de la fecha media climatológica, y la fracción de eventos en
  la temporada núcleo (15 may - 15 jun y may-ago; Fisher exacto).
- Sensibilidad: todo se repite con **días de tornado** (fechas únicas,
  para que el brote del 30-31 de mayo de 2019 no pese 7 veces) y con el
  subconjunto centro-sur (lat ≤ -33°).

## Resultados (maestra al 6-ago-2026; `output/resultados.txt`)

Muestra principal: 94 eventos 1952-2025 con ONI definitivo
(26 El Niño, 55 neutral, 13 La Niña).

- **La estacionalidad es fuerte en todas las fases** (Rayleigh
  p < 0.001): ENSO no crea ni destruye la temporada.
- **El corrimiento de la fecha media bajo El Niño desaparece con el
  registro más largo**: +4 días (p = 0.74) en eventos, +12 días
  (p = 0.46) en días de tornado. Con la instantánea corta (hasta 2023)
  habíamos visto +17 a +35 días rozando o cruzando el 5 %; los eventos
  nuevos del registro largo lo desarman — en particular el grupo de
  septiembre de 2025 (Pilolcura, Linares, San Pedro de la Paz, Chaihuín)
  ocurrió en fase **neutral**, y Chinquihue (nov-2000) bajo La Niña, así
  que la cola tardía ya no es exclusiva de El Niño.
- **Lo que sí queda es una señal de concentración**: bajo El Niño la
  temporada es más compacta alrededor de su centro. La correlación de
  rangos entre la anomalía ONI concurrente y la distancia circular del
  evento al centro de la temporada es negativa y significativa en las
  variantes curadas: ρ = -0.24 (p = 0.019) en eventos, -0.28 (p = 0.019)
  en días de tornado, -0.22 (p = 0.041) en centro-sur (-0.24, p = 0.050
  en días centro-sur). Consistente con ΔR = +0.12 a +0.18 (p = 0.14-0.37)
  y Watson U² p = 0.071 en la muestra principal: los eventos fuera de
  temporada (tornados estivales precordilleranos, marzo, primavera)
  ocurren casi siempre en fase neutral o La Niña.
- **Frecuencia**: 26 de 94 eventos en episodios El Niño contra 24.2
  esperados (binomial p = 0.72) — sin señal.
- Con los eventos provisionales de 2026 (evento cálido en desarrollo,
  eventos de jun-ago): las conclusiones no cambian; la correlación de
  rangos se mantiene (días: ρ = -0.24, p = 0.035) y ΔR marginal
  (p = 0.083).

**Conclusión:** con el registro largo, la evidencia de que El Niño
*corra* la temporada de tornados es débil o nula; lo que aparece —
moderado y aún por confirmar con más datos — es que **el ENSO cálido
concentra los eventos en el corazón de la temporada de invierno,
mientras que los eventos fuera de temporada ocurren de preferencia en
neutral/La Niña**. Dado el número de tests correlacionados, ese ρ
significativo (p ≈ 0.02-0.05 en tres de cuatro variantes curadas) debe
leerse como sugerente, no concluyente. Nota metodológica saludable: el
resultado "significativo" que daba la instantánea corta (+29 días,
p = 0.013) no sobrevivió al registro completo.

## Uso

```bash
pip install numpy pandas matplotlib
python enso-tornados/analisis_enso_estacionalidad.py
```

Escribe `output/resultados.txt` y la figura
`output/enso_estacionalidad_tornados.{png,pdf}` (histograma mensual por
fase ENSO + fecha del evento contra ONI concurrente; rombos abiertos =
eventos con ONI provisional). Para refrescar datos: bajar la última
versión de figshare (o exportar la `Final_Table` de la planilla
maestra), regenerar `oni.csv` con el `process_oni.py` de ninodata, y
editar/vaciar `eventos_2026_provisional.csv` según corresponda.

## Referencias

- Bastías-Curivil, C., et al. (2024-2025). *Tornadoes and Waterspouts in
  Chile / Tornados y Trombas en Chile* (dataset, v5 2025-07-14). figshare.
  https://doi.org/10.6084/m9.figshare.25119566
- Bastías-Curivil, C., et al. (2025). Tornado Seasonality in
  Central-Southern Chile. *Geophysical Research Letters*.
  https://doi.org/10.1029/2024GL110900
- Vicencio, J., et al. (2021). The Chilean Tornado Outbreak of May
  2019. *BAMS*.
- NOAA/CPC. Oceanic Niño Index.
  https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
