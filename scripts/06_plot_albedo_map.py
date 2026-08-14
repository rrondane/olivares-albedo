"""Map of the MODIS albedo field for one day.

Draws the MOD10A1 snow albedo (or MCD43A3 shortwave albedo) around the
Olivares glaciers for the requested date, with the glacier outlines on
top. Useful to inspect individual smoke/ash deposition events.

Usage (from the repository root):
    python scripts/06_plot_albedo_map.py 2017-01-30
    python scripts/06_plot_albedo_map.py 2017-01-30 MCD43A3
"""
import sys

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

import config
import figstyle

figstyle.use()


def load_field(product, when):
    files = sorted((config.RAW_DIR / product).glob("*.nc"))
    if not files:
        sys.exit(f"No netCDF for {product} in data/raw/ - run scripts 02-03.")
    ds = xr.open_dataset(files[0])

    if product == "MOD10A1":
        var = next(v for v in ds.data_vars if "Snow_Albedo" in v)
        da = ds[var]
        da = da.where((da >= 1) & (da <= 100)) / 100.0
        name = "Albedo de nieve MOD10A1"
    else:
        var = next(v for v in ds.data_vars if "Albedo_BSA_shortwave" in v)
        da = ds[var]
        da = da.where((da >= 0) & (da <= 1))
        name = "Albedo de cielo negro MCD43A3"

    da = da.sel(time=when, method="nearest")
    return da, name


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    when = pd.Timestamp(sys.argv[1])
    product = sys.argv[2] if len(sys.argv) > 2 else "MOD10A1"

    da, name = load_field(product, when)
    actual = pd.Timestamp(da["time"].values)
    if abs(actual - when) > pd.Timedelta(days=3):
        print(f"WARNING: nearest available date is {actual.date()}")

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    lat = da["lat"].values if "lat" in da.coords else da["latitude"].values
    lon = da["lon"].values if "lon" in da.coords else da["longitude"].values
    mesh = ax.pcolormesh(lon, lat, da.values, cmap="viridis",
                         vmin=0, vmax=1, shading="nearest")

    if config.OUTLINE_FILE.exists():
        outlines = gpd.read_file(config.OUTLINE_FILE)
        # double stroke (white under black) stays visible on any albedo
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
    stem = f"mapa_albedo_{product}_{actual.date()}"
    for ext in ("png", "pdf"):
        path = config.FIGURE_DIR / f"{stem}.{ext}"
        fig.savefig(path, dpi=300, bbox_inches="tight")
        print(f"saved {path.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
