"""Shared configuration for the Olivares albedo project.

Every script imports this module, so the study area, time windows and
directory layout are defined in exactly one place.
"""
from pathlib import Path

# ---------------------------------------------------------------- directories
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTLINE_DIR = DATA_DIR / "outlines"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FIGURE_DIR = ROOT / "figures"

# ------------------------------------------------------------------ study area
# Bounding box around the upper Olivares basin (Region Metropolitana, Chile),
# generous enough to include Olivares Alfa and Beta plus some context for maps.
# Order: (lon_min, lat_min, lon_max, lat_max), degrees, WGS84.
BBOX = (-70.35, -33.30, -70.05, -33.05)

# Glaciers used for the time series (matched case-insensitively against the
# RGI "Name"/"glac_name" attribute inside BBOX).
GLACIER_NAME_PATTERNS = ["olivares alfa", "olivares beta"]

# Randolph Glacier Inventory 6.0, region 17 (Southern Andes), served without
# authentication from the OGGM mirror of glims.org.
RGI_URL = ("https://cluster.klima.uni-bremen.de/~oggm/rgi/www.glims.org/"
           "RGI/rgi60_files/17_rgi60_SouthernAndes.zip")
OUTLINE_FILE = OUTLINE_DIR / "olivares_glaciers.geojson"

# ----------------------------------------------------------------- time window
# Extended austral summer, split in two calendar-year windows because AppEEARS
# recurring ranges cannot cross Dec 31: Nov-Dec of year Y belongs to the same
# summer as Jan-Mar of year Y+1 (summers are labelled by the ending year).
YEAR_RANGE = [2000, 2026]          # first and last calendar year requested
SUMMER_MONTHS = (11, 12, 1, 2, 3)  # months kept in the analysis
CORE_SUMMER_MONTHS = (12, 1, 2)    # DJF, used for the summer-mean statistic

# ------------------------------------------------------------------- products
# AppEEARS product IDs and the layers requested from each.
PRODUCTS = {
    "MOD10A1.061": [
        "Snow_Albedo_Daily_Tile",
        "NDSI_Snow_Cover",
        "NDSI_Snow_Cover_Basic_QA",
    ],
    "MCD43A3.061": [
        "Albedo_BSA_shortwave",
        "Albedo_WSA_shortwave",
        "BRDF_Albedo_Band_Mandatory_Quality_shortwave",
    ],
}

# ------------------------------------------------------------------- AppEEARS
API_URL = "https://appeears.earthdatacloud.nasa.gov/api"
TASK_FILE = DATA_DIR / "appeears_tasks.json"
TASK_PREFIX = "olivares-albedo"

# ------------------------------------------------------------------- outputs
TIMESERIES_FILE = PROCESSED_DIR / "albedo_timeseries.csv"

# Fire seasons highlighted in the figures (summer label -> text for legend).
FIRE_SUMMERS = {
    2017: "verano 2016-17 (mega-incendios de enero)",
    2023: "verano 2022-23 (incendios de febrero)",
}


def summer_label(date):
    """Summer a date belongs to, labelled by the ending year.

    November/December count toward the summer that ends the following
    calendar year; dates outside SUMMER_MONTHS return None.
    """
    if date.month >= 11:
        return date.year + 1
    if date.month <= 3:
        return date.year
    return None
