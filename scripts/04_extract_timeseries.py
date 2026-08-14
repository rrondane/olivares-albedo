"""Build the glacier-averaged albedo time series.

Opens every AppEEARS netCDF in data/raw/, keeps only the pixels whose
centers fall inside the Olivares Alfa + Beta outlines, applies the
product-specific quality screening, and writes one tidy CSV
(data/processed/albedo_timeseries.csv) with one row per date and variable:

    date, summer, product, variable, mean, median, std, n_valid, n_pixels

Quality screening
-----------------
MOD10A1 Snow_Albedo_Daily_Tile : valid range is 1-100 (%); every other
    value is a flag (cloud 150, night 111, missing 250, ...) and is
    discarded. Albedo is converted to a 0-1 fraction.
MCD43A3 Albedo_*_shortwave     : the scale factor and fill value are
    applied automatically by xarray; additionally only pixels whose
    mandatory QA equals 0 (full BRDF inversion) are kept.

Usage (from the repository root):
    python scripts/04_extract_timeseries.py
"""
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
import xarray as xr

import config


def glacier_mask(lon, lat):
    """Boolean (lat, lon) array: pixel centers inside the glacier outlines."""
    outlines = gpd.read_file(config.OUTLINE_FILE)
    union = outlines.geometry.union_all() if hasattr(outlines.geometry, "union_all") \
        else outlines.geometry.unary_union
    lon2d, lat2d = np.meshgrid(lon, lat)
    return shapely.contains_xy(union, lon2d, lat2d)


def stats_rows(da, mask, product, variable):
    """Per-date statistics of `da` over the glacier pixels."""
    rows = []
    n_pixels = int(mask.sum())
    values = da.values  # (time, lat, lon)
    for i, t in enumerate(pd.to_datetime(da["time"].values)):
        v = values[i][mask]
        v = v[np.isfinite(v)]
        rows.append({
            "date": t.date(),
            "summer": config.summer_label(t),
            "product": product,
            "variable": variable,
            "mean": np.mean(v) if v.size else np.nan,
            "median": np.median(v) if v.size else np.nan,
            "std": np.std(v) if v.size else np.nan,
            "n_valid": int(v.size),
            "n_pixels": n_pixels,
        })
    return rows


def find_var(ds, name):
    """AppEEARS keeps the layer name as the variable name; be tolerant."""
    for v in ds.data_vars:
        if name.lower() in v.lower():
            return ds[v]
    return None


def extract_mod10a1(ds, mask):
    alb = find_var(ds, "Snow_Albedo_Daily_Tile")
    if alb is None:
        return []
    # Valid snow albedo is 1-100 %; everything else is a flag value.
    alb = alb.where((alb >= 1) & (alb <= 100)) / 100.0
    return stats_rows(alb, mask, "MOD10A1", "snow_albedo")


def extract_mcd43a3(ds, mask):
    rows = []
    qa = find_var(ds, "BRDF_Albedo_Band_Mandatory_Quality_shortwave")
    for layer, name in [("Albedo_BSA_shortwave", "black_sky_albedo"),
                        ("Albedo_WSA_shortwave", "white_sky_albedo")]:
        alb = find_var(ds, layer)
        if alb is None:
            continue
        if qa is not None:
            alb = alb.where(qa == 0)  # full BRDF inversions only
        alb = alb.where((alb >= 0) & (alb <= 1))
        rows += stats_rows(alb, mask, "MCD43A3", name)
    return rows


def main():
    if not config.OUTLINE_FILE.exists():
        sys.exit("No glacier outlines - run script 01 first.")
    nc_files = sorted(config.RAW_DIR.glob("**/*.nc"))
    if not nc_files:
        sys.exit("No netCDF files in data/raw/ - run scripts 02 and 03 first.")

    all_rows = []
    for path in nc_files:
        print(f"Processing {path.relative_to(config.ROOT)} ...")
        ds = xr.open_dataset(path)
        lat_name = "lat" if "lat" in ds.coords else "latitude"
        lon_name = "lon" if "lon" in ds.coords else "longitude"
        mask = glacier_mask(ds[lon_name].values, ds[lat_name].values)
        print(f"  {int(mask.sum())} MODIS pixels on the glaciers")

        rows = extract_mod10a1(ds, mask) + extract_mcd43a3(ds, mask)
        if not rows:
            print("  WARNING: no known albedo layer found, skipped")
        all_rows += rows
        ds.close()

    df = (pd.DataFrame(all_rows)
          .dropna(subset=["summer"])
          .sort_values(["product", "variable", "date"]))
    config.TIMESERIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.TIMESERIES_FILE, index=False, float_format="%.4f")

    n_dates = df["date"].nunique()
    print(f"\nWrote {len(df)} rows ({n_dates} dates) -> "
          f"{config.TIMESERIES_FILE}")
    with pd.option_context("display.width", 120):
        print(df.groupby(["product", "variable"])
                .agg(dates=("date", "nunique"),
                     first=("date", "min"), last=("date", "max"),
                     mean_albedo=("mean", "mean")))


if __name__ == "__main__":
    main()
