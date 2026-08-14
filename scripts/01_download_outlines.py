"""Download glacier outlines for the Olivares basin.

Fetches the Randolph Glacier Inventory 6.0 shapefile for region 17
(Southern Andes) from the OGGM public mirror, selects the Olivares Alfa
and Olivares Beta glaciers, and saves them as a small GeoJSON that the
rest of the workflow uses to mask MODIS pixels.

Usage (from the repository root):
    python scripts/01_download_outlines.py

No credentials required. The ~40 MB RGI zip is cached in data/outlines/
so re-runs are instant.
"""
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd

import config


def download_rgi(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"RGI zip already present: {dest}")
        return dest
    print(f"Downloading {config.RGI_URL}\n -> {dest} (~40 MB, may take a minute)")
    urllib.request.urlretrieve(config.RGI_URL, dest)
    return dest


def read_rgi(zip_path: Path) -> gpd.GeoDataFrame:
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmp)
        shp = next(Path(tmp).glob("**/*.shp"))
        print(f"Reading {shp.name} ...")
        return gpd.read_file(shp)


def select_glaciers(rgi: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    lon_min, lat_min, lon_max, lat_max = config.BBOX
    box = rgi.cx[lon_min:lon_max, lat_min:lat_max]
    print(f"{len(box)} glaciers inside the bounding box")

    name_col = "Name" if "Name" in box.columns else "glac_name"
    names = box[name_col].fillna("").str.lower()
    wanted = names.apply(
        lambda n: any(p in n for p in config.GLACIER_NAME_PATTERNS))
    sel = box[wanted]

    if sel.empty:
        print("WARNING: no glacier matched by name; falling back to the "
              "largest glaciers in the box (check the result on a map!)")
        area_col = "Area" if "Area" in box.columns else "area_km2"
        sel = box.sort_values(area_col, ascending=False).head(2)
    return sel


def main():
    zip_path = config.OUTLINE_DIR / "17_rgi60_SouthernAndes.zip"
    rgi = read_rgi(download_rgi(zip_path))
    sel = select_glaciers(rgi)

    name_col = "Name" if "Name" in sel.columns else "glac_name"
    area_col = "Area" if "Area" in sel.columns else "area_km2"
    print("\nSelected glaciers:")
    for _, row in sel.iterrows():
        print(f"  {row[name_col]!r:30s} area = {row[area_col]:6.2f} km2  "
              f"({row.geometry.centroid.y:.3f}, {row.geometry.centroid.x:.3f})")

    config.OUTLINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    sel.to_file(config.OUTLINE_FILE, driver="GeoJSON")
    print(f"\nSaved {len(sel)} outlines -> {config.OUTLINE_FILE}")
    if sel.empty:
        sys.exit(1)


if __name__ == "__main__":
    main()
