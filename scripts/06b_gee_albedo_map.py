"""Map of the MODIS albedo field for one day, via Google Earth Engine.

Same figure as script 06 but fetching the clipped field from Earth Engine
instead of the AppEEARS netCDF (useful if you took the GEE route and have
no local netCDF files).

Usage (from the repository root):
    python scripts/06b_gee_albedo_map.py 2017-01-30 --project YOUR-PROJECT
    python scripts/06b_gee_albedo_map.py 2017-01-30 MCD43A3 --project ...
"""
import argparse
import io
import sys
import urllib.request

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config
import figstyle

try:
    import ee
except ImportError:
    sys.exit("earthengine-api is not installed: pip install earthengine-api")

figstyle.use()
FILL = -9999.0


def nearest_image(col, when, days=3):
    """Image of `col` closest in time to `when` (within +-days), or None."""
    w0 = ee.Date(str(when.date()))
    sub = col.filterDate(w0.advance(-days, "day"), w0.advance(days + 1, "day"))
    times = sub.aggregate_array("system:time_start").getInfo()
    if not times:
        return None, None
    stamps = pd.to_datetime(times, unit="ms")
    best = stamps[np.argmin(abs(stamps - when))]
    day = ee.Date(str(best.date()))
    return sub.filterDate(day, day.advance(1, "day")).first(), best


def fetch_field(product, when):
    if product == "MOD10A1":
        col = (ee.ImageCollection("MODIS/061/MOD10A1")
               .select("Snow_Albedo_Daily_Tile"))
        prep = lambda im: im.updateMask(im.gte(1).And(im.lte(100))).divide(100)
        name = "Albedo de nieve MOD10A1"
    else:
        col = ee.ImageCollection("MODIS/061/MCD43A3")
        prep = lambda im: (im.select("Albedo_BSA_shortwave")
                           .updateMask(im.select(
                               "BRDF_Albedo_Band_Mandatory_Quality_shortwave")
                               .eq(0)).multiply(0.001))
        name = "Albedo de cielo negro MCD43A3"

    img, actual = nearest_image(col, when)
    if img is None:
        sys.exit(f"No {product} image within 3 days of {when.date()}")

    lon_min, lat_min, lon_max, lat_max = config.BBOX
    region = ee.Geometry.Rectangle(config.BBOX)
    url = prep(ee.Image(img)).unmask(FILL).rename("alb").getDownloadURL(
        {"region": region, "scale": 500, "format": "NPY"})
    arr = np.load(io.BytesIO(urllib.request.urlopen(url).read()))
    field = arr["alb"].astype(float)
    field[field == FILL] = np.nan

    ny, nx = field.shape
    lon = np.linspace(lon_min, lon_max, nx)
    lat = np.linspace(lat_max, lat_min, ny)  # north-up rows
    return field, lon, lat, name, actual


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("date", help="YYYY-MM-DD")
    ap.add_argument("product", nargs="?", default="MOD10A1",
                    choices=["MOD10A1", "MCD43A3"])
    ap.add_argument("--project", default=None)
    args = ap.parse_args()

    try:
        ee.Initialize(project=args.project)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=args.project)

    when = pd.Timestamp(args.date)
    field, lon, lat, name, actual = fetch_field(args.product, when)
    if actual.date() != when.date():
        print(f"WARNING: nearest available date is {actual.date()}")

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    mesh = ax.pcolormesh(lon, lat, field, cmap="viridis",
                         vmin=0, vmax=1, shading="nearest")
    if config.OUTLINE_FILE.exists():
        outlines = gpd.read_file(config.OUTLINE_FILE)
        outlines.boundary.plot(ax=ax, color="white", lw=2.2)
        outlines.boundary.plot(ax=ax, color="black", lw=0.9)

    fecha = f"{actual.day}-{figstyle.MESES[actual.month - 1]}-{actual.year}"
    ax.set_title(f"{name}, {fecha}")
    ax.set_xlabel("Longitud (°)")
    ax.set_ylabel("Latitud (°)")
    ax.set_aspect(1 / np.cos(np.deg2rad(np.mean(lat))))
    cb = fig.colorbar(mesh, ax=ax, shrink=0.85)
    cb.set_label("Albedo (fracción)")

    missing = figstyle.check(ax.get_title(), ax.get_xlabel(), ax.get_ylabel(),
                             cb.ax.get_ylabel())
    if missing:
        print(f"WARNING: figure font lacks glyphs {missing}", file=sys.stderr)

    config.FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    stem = f"mapa_albedo_{args.product}_{actual.date()}"
    for ext in ("png", "pdf"):
        path = config.FIGURE_DIR / f"{stem}.{ext}"
        fig.savefig(path, dpi=300, bbox_inches="tight")
        print(f"saved {path.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
