"""Submit AppEEARS area-extraction tasks for the Olivares albedo archive.

AppEEARS (https://appeears.earthdatacloud.nasa.gov) clips MODIS products to
our study area on NASA's servers, so instead of downloading >100 GB of full
tiles each student transfers a few hundred MB of ready-to-use netCDF.

One task is submitted per product (MOD10A1 daily snow albedo, MCD43A3
black/white-sky albedo), each requesting every extended summer
(Nov 1 - Mar 31) from 2000 to the present. Task IDs are stored in
data/appeears_tasks.json for script 03.

You need a (free) NASA Earthdata Login account: https://urs.earthdata.nasa.gov
Credentials are read from ~/.netrc if present, otherwise you are prompted.

Usage (from the repository root):
    python scripts/02_submit_appeears_task.py            # submit missing tasks
    python scripts/02_submit_appeears_task.py --force    # resubmit everything
"""
import getpass
import json
import netrc
import sys
import time

import requests

import config

URS_HOST = "urs.earthdata.nasa.gov"


def earthdata_credentials():
    try:
        auth = netrc.netrc().authenticators(URS_HOST)
        if auth:
            print(f"Using Earthdata credentials for '{auth[0]}' from ~/.netrc")
            return auth[0], auth[2]
    except (FileNotFoundError, netrc.NetrcParseError):
        pass
    user = input("Earthdata username: ")
    password = getpass.getpass("Earthdata password: ")
    return user, password


def login(attempts=4):
    user, password = earthdata_credentials()
    for i in range(attempts):
        r = requests.post(f"{config.API_URL}/login", auth=(user, password),
                          timeout=120)
        if r.status_code < 500:
            r.raise_for_status()
            return r.json()["token"]
        # the AppEEARS gateway sometimes times out (504); just retry
        print(f"  login attempt {i + 1} failed ({r.status_code}), retrying...")
        time.sleep(10)
    r.raise_for_status()


def bbox_geojson():
    lon_min, lat_min, lon_max, lat_max = config.BBOX
    ring = [[lon_min, lat_min], [lon_max, lat_min], [lon_max, lat_max],
            [lon_min, lat_max], [lon_min, lat_min]]
    return {"type": "FeatureCollection",
            "features": [{"type": "Feature", "properties": {},
                          "geometry": {"type": "Polygon",
                                       "coordinates": [ring]}}]}


def build_task(product, layers):
    y0, y1 = config.YEAR_RANGE
    # Two recurring windows because a recurring range cannot cross Dec 31:
    # Nov-Dec of years y0..y1-1 plus Jan-Mar of years y0..y1 covers every
    # extended summer from y0 to y1.
    dates = [
        {"startDate": "11-01", "endDate": "12-31",
         "recurring": True, "yearRange": [y0, y1 - 1]},
        {"startDate": "01-01", "endDate": "03-31",
         "recurring": True, "yearRange": [y0, y1]},
    ]
    return {
        "task_type": "area",
        "task_name": f"{config.TASK_PREFIX}-{product.split('.')[0].lower()}",
        "params": {
            "dates": dates,
            "layers": [{"product": product, "layer": lay} for lay in layers],
            "geo": bbox_geojson(),
            "output": {"format": {"type": "netcdf4"},
                       "projection": "geographic"},
        },
    }


def main():
    force = "--force" in sys.argv

    tasks = {}
    if config.TASK_FILE.exists():
        tasks = json.loads(config.TASK_FILE.read_text())

    todo = {p: l for p, l in config.PRODUCTS.items()
            if force or p not in tasks}
    if not todo:
        print("All tasks already submitted (use --force to resubmit):")
        for p, t in tasks.items():
            print(f"  {p}: {t['task_id']}")
        return

    token = login()
    headers = {"Authorization": f"Bearer {token}"}

    for product, layers in todo.items():
        task = build_task(product, layers)
        print(f"Submitting task '{task['task_name']}' "
              f"({len(layers)} layers, {config.YEAR_RANGE[0]}-"
              f"{config.YEAR_RANGE[1]}) ...")
        r = requests.post(f"{config.API_URL}/task", json=task, headers=headers)
        if not r.ok:
            print(f"  ERROR {r.status_code}: {r.text}")
            sys.exit(1)
        task_id = r.json()["task_id"]
        tasks[product] = {"task_id": task_id, "task_name": task["task_name"]}
        print(f"  -> task_id {task_id}")

    config.TASK_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.TASK_FILE.write_text(json.dumps(tasks, indent=2))
    print(f"\nTask IDs saved to {config.TASK_FILE}")
    print("Processing takes from minutes to a few hours; run "
          "scripts/03_download_appeears_results.py to check and download.")


if __name__ == "__main__":
    main()
