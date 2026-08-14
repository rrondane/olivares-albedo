# Summer albedo of the Olivares glaciers and Chilean wildfire seasons

Does the albedo of central-Chilean glaciers drop during big wildfire
seasons? Smoke plumes from summer wildfires (e.g. the mega-fires of
January 2017 and February 2023) can deposit black carbon and ash on the
snow and ice of the Andes; darker snow absorbs more sunlight and melts
faster. This repository lets you download, from scratch, a **26-summer
archive of daily MODIS albedo over the Olivares Alfa and Olivares Beta
glaciers** (upper Olivares basin, ~33.2°S) and test that hypothesis
yourself.

## Data

| Product | What it is | Source |
|---|---|---|
| [MOD10A1 v061](https://nsidc.org/data/mod10a1) | Terra/MODIS **daily snow albedo** at 500 m (`Snow_Albedo_Daily_Tile`, plus NDSI snow cover and its QA) | NSIDC DAAC |
| [MCD43A3 v061](https://lpdaac.usgs.gov/products/mcd43a3v061/) | Terra+Aqua **BRDF-corrected black-sky and white-sky shortwave albedo**, daily at 500 m, with mandatory QA | LP DAAC |
| [RGI 6.0](https://www.glims.org/RGI/) | Glacier outlines, region 17 (Southern Andes) | GLIMS/RGI (OGGM mirror) |

Instead of downloading full MODIS tiles (>100 GB), the scripts use
[AppEEARS](https://appeears.earthdatacloud.nasa.gov), a NASA service that
clips the products to our small study area on the server side. Each
student transfers only some hundreds of MB of analysis-ready netCDF.

Every **extended austral summer (Nov 1 - Mar 31) from 2000 to the
present** is requested. Summers are labelled by the year in which they
end: "2017" means November 2016 - March 2017.

## Getting started

1. Create a free NASA Earthdata Login account at
   <https://urs.earthdata.nasa.gov> (needed by AppEEARS).
2. Install the Python environment (any of the two):

   ```bash
   # with conda
   conda env create -f environment.yml
   conda activate olivares-albedo

   # or with pip in a virtual environment
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Run the scripts **in order, from the repository root**:

   ```bash
   python scripts/01_download_outlines.py        # glacier outlines (no login)
   python scripts/02_submit_appeears_task.py     # submit the two AppEEARS tasks
   python scripts/03_download_appeears_results.py --wait   # wait + download
   python scripts/04_extract_timeseries.py       # glacier-mean albedo -> CSV
   python scripts/05_plot_timeseries.py          # summary figures
   python scripts/06_plot_albedo_map.py 2017-01-30   # map of one day
   ```

   AppEEARS queues the extraction; a task typically takes from a few
   minutes to a few hours. You can close everything after script 02 and
   simply run script 03 again later — the task IDs are kept in
   `data/appeears_tasks.json`.

   To avoid typing your Earthdata password each time, put it in
   `~/.netrc` (mode 600):

   ```
   machine urs.earthdata.nasa.gov login YOUR_USER password YOUR_PASSWORD
   ```

### Route B: Google Earth Engine (alternative to scripts 02-04)

Both products are also in the [Earth Engine
catalog](https://developers.google.com/earth-engine/datasets), and the
glacier averages can be computed entirely on Google's servers — no queue,
no bulk download, only the final table is transferred. Use this route if
AppEEARS is slow or down.

1. Register for (free) noncommercial Earth Engine use and create a Google
   Cloud project: <https://code.earthengine.google.com/register>
2. `earthengine authenticate` (one time; opens the browser)
3. ```bash
   python scripts/01_download_outlines.py                      # if not done yet
   python scripts/02b_gee_timeseries.py --project YOUR-PROJECT # ~10-20 min
   python scripts/05_plot_timeseries.py
   python scripts/06b_gee_albedo_map.py 2017-01-30 --project YOUR-PROJECT
   ```

Script 02b writes the **same CSV** as script 04, so everything downstream
is identical. Small differences to be aware of: Earth Engine resamples in
its own pyramid/projection when reducing, so pixel counts and means can
differ by a few percent from the AppEEARS numbers — fine for the
hypothesis test, but do not mix the two sources within one analysis.

## What you get

- `data/processed/albedo_timeseries.csv` — one row per day and variable
  (MOD10A1 snow albedo; MCD43A3 black- and white-sky shortwave albedo),
  averaged over the glacier pixels, with pixel counts so you can judge
  coverage.
- `figures/albedo_diario.*` — daily albedo of every summer on a common
  Nov-Mar axis, wildfire summers highlighted.
- `figures/albedo_veranos.*` — mean December-February albedo of each
  summer, 2000-2026, wildfire summers shaded.
- `figures/mapa_albedo_*.*` — albedo maps of individual days.

## Quality screening (already applied in script 04)

- **MOD10A1**: `Snow_Albedo_Daily_Tile` is kept only in its valid range
  1-100 %. All flag values (cloud = 150, night = 111, missing = 250, …)
  are discarded, so cloudy days simply have fewer (or zero) valid pixels.
- **MCD43A3**: only pixels with mandatory QA = 0 (full BRDF inversion)
  are used; fill values and the 0.001 scale factor are handled
  automatically.

## Things to keep in mind when interpreting the results

- **Clouds and smoke both remove data.** During a heavy-smoke episode the
  retrieval may fail exactly when the deposition happens — look at
  `n_valid` before trusting a gap.
- **Albedo also drops for reasons unrelated to fires**: warm summers melt
  the seasonal snow earlier and expose dark bare ice; a dry winter (e.g.
  the mega-drought years) has the same effect. Compare fire summers
  against summers of similar snow accumulation, not just against the
  mean.
- MOD10A1 is a single-observation daily value in steep terrain
  (illumination/viewing artifacts are possible); MCD43A3 is smoother and
  better calibrated radiometrically but uses a 16-day moving retrieval
  window, which damps short-lived deposition events. That is why we use
  both.
- The two glaciers together span only a few dozen 500 m pixels; the
  outlines are from RGI 6.0 (nominal year ~2000) and the glaciers have
  retreated since, so edge pixels are progressively more mixed.

## Repository layout

```
scripts/   numbered workflow (01 → 06) + config.py + figstyle.py
           02b/06b are the Google Earth Engine alternatives to 02-04/06
data/      everything downloaded/derived (git-ignored, ~hundreds of MB)
figures/   output figures (git-ignored)
```

All figure text is in Spanish (project convention); code and
documentation are in English.

## References

- Hall, D. K. & Riggs, G. A. (2021). *MODIS/Terra Snow Cover Daily L3
  Global 500m SIN Grid, Version 61* (MOD10A1). NSIDC DAAC.
  https://doi.org/10.5067/MODIS/MOD10A1.061
- Schaaf, C. & Wang, Z. (2021). *MCD43A3 MODIS/Terra+Aqua BRDF/Albedo
  Daily L3 Global 500 m V061*. NASA EOSDIS LP DAAC.
  https://doi.org/10.5067/MODIS/MCD43A3.061
- RGI Consortium (2017). *Randolph Glacier Inventory 6.0*.
  https://doi.org/10.7265/N5-RGI-60
- AppEEARS Team (2024). *Application for Extracting and Exploring
  Analysis Ready Samples (AppEEARS)*. NASA EOSDIS LP DAAC.
  https://appeears.earthdatacloud.nasa.gov
