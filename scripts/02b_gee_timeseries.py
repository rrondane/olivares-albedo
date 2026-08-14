"""Alternative route: build the albedo time series with Google Earth Engine.

Replaces scripts 02 + 03 + 04 in one step. Both products are in the Earth
Engine catalog (MODIS/061/MOD10A1 and MODIS/061/MCD43A3); the glacier-mean
statistics are computed on Google's servers and only the tiny result table
is transferred, so nothing is downloaded and there is no processing queue.
The output CSV is identical to the one from script 04, so scripts 05/06
work unchanged.

One-time setup:
  1. pip install earthengine-api   (already in requirements.txt)
  2. Register for noncommercial Earth Engine use (free) and create/choose
     a Google Cloud project: https://code.earthengine.google.com/register
  3. earthengine authenticate

Usage (from the repository root):
    python scripts/02b_gee_timeseries.py --project YOUR-GCP-PROJECT
"""
import argparse
import json
import sys

import pandas as pd
import shapely.geometry

import config

try:
    import ee
except ImportError:
    sys.exit("earthengine-api is not installed: pip install earthengine-api")


def init_ee(project):
    try:
        ee.Initialize(project=project)
    except Exception:
        print("Stored credentials not found/valid - opening browser to "
              "authenticate ...")
        ee.Authenticate()
        ee.Initialize(project=project)


def glacier_geometry():
    if not config.OUTLINE_FILE.exists():
        sys.exit("No glacier outlines - run script 01 first.")
    gj = json.loads(config.OUTLINE_FILE.read_text())
    union = shapely.union_all(
        [shapely.geometry.shape(f["geometry"]) for f in gj["features"]])
    return ee.Geometry(shapely.geometry.mapping(union))


REDUCER = None  # built after ee.Initialize


def build_reducer():
    return (ee.Reducer.mean()
            .combine(ee.Reducer.median(), sharedInputs=True)
            .combine(ee.Reducer.stdDev(), sharedInputs=True)
            .combine(ee.Reducer.count(), sharedInputs=True))


def mod10a1(start, end):
    col = (ee.ImageCollection("MODIS/061/MOD10A1")
           .filterDate(start, end).select("Snow_Albedo_Daily_Tile"))

    def prep(im):
        # valid snow albedo is 1-100 %; everything else is a flag value
        alb = im.updateMask(im.gte(1).And(im.lte(100))).divide(100)
        return alb.set("system:time_start", im.get("system:time_start"))
    return col.map(prep)


def mcd43a3(start, end, band):
    col = ee.ImageCollection("MODIS/061/MCD43A3").filterDate(start, end)

    def prep(im):
        qa = im.select("BRDF_Albedo_Band_Mandatory_Quality_shortwave")
        alb = im.select(band).updateMask(qa.eq(0)).multiply(0.001)
        return alb.set("system:time_start", im.get("system:time_start"))
    return col.map(prep)


def collection_stats(col, geom, product, variable):
    def per_image(im):
        st = im.rename("alb").reduceRegion(
            reducer=REDUCER, geometry=geom, scale=500, maxPixels=1e9)
        return ee.Feature(None, st).set(
            "date", im.date().format("YYYY-MM-dd"))

    rows = []
    for f in col.map(per_image).getInfo()["features"]:
        p = f["properties"]
        rows.append({
            "date": p["date"], "product": product, "variable": variable,
            "mean": p.get("alb_mean"), "median": p.get("alb_median"),
            "std": p.get("alb_stdDev"), "n_valid": p.get("alb_count", 0),
        })
    return rows


def main():
    global REDUCER
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=None,
                    help="Google Cloud project registered for Earth Engine")
    args = ap.parse_args()

    init_ee(args.project)
    REDUCER = build_reducer()
    geom = glacier_geometry()
    # total-pixel denominator: reduce an all-ones image on the MODIS grid
    # with the SAME combined reducer as the daily statistics, so boundary
    # pixels are counted identically (a standalone count() weights edge
    # pixels fractionally and would come out ~40% lower)
    proj = (ee.ImageCollection("MODIS/061/MOD10A1").first()
            .select("Snow_Albedo_Daily_Tile").projection())
    n_pixels = int(ee.Image.constant(1).setDefaultProjection(proj)
                   .rename("alb").reduceRegion(REDUCER, geom, 500)
                   .getInfo()["alb_count"])
    print(f"{n_pixels} MODIS pixels on the glaciers")

    y0, y1 = config.YEAR_RANGE
    all_rows = []
    for year in range(y0, y1 + 1):
        start, end = f"{year - 1}-11-01", f"{year}-04-01"
        rows = collection_stats(mod10a1(start, end), geom,
                                "MOD10A1", "snow_albedo")
        rows += collection_stats(
            mcd43a3(start, end, "Albedo_BSA_shortwave"), geom,
            "MCD43A3", "black_sky_albedo")
        rows += collection_stats(
            mcd43a3(start, end, "Albedo_WSA_shortwave"), geom,
            "MCD43A3", "white_sky_albedo")
        all_rows += rows
        print(f"  summer {year}: {len(rows)} rows")

    df = pd.DataFrame(all_rows)
    df["date"] = pd.to_datetime(df["date"])
    df["summer"] = [config.summer_label(d) for d in df["date"]]
    df["n_pixels"] = n_pixels
    df = (df.dropna(subset=["summer"])
          [["date", "summer", "product", "variable",
            "mean", "median", "std", "n_valid", "n_pixels"]]
          .sort_values(["product", "variable", "date"]))
    df["date"] = df["date"].dt.date

    config.TIMESERIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.TIMESERIES_FILE, index=False, float_format="%.4f")
    print(f"\nWrote {len(df)} rows -> {config.TIMESERIES_FILE}")


if __name__ == "__main__":
    main()
