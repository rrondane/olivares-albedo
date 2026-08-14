"""Check AppEEARS task status and download the finished netCDF files.

Reads the task IDs stored by script 02, reports the status of each task,
and downloads the netCDF bundle files of every completed task into
data/raw/<PRODUCT>/. Safe to re-run: existing files are skipped.

Usage (from the repository root):
    python scripts/03_download_appeears_results.py           # check + download
    python scripts/03_download_appeears_results.py --wait    # poll until done
"""
import importlib
import json
import sys
import time
from pathlib import Path

import requests

import config

login = importlib.import_module("02_submit_appeears_task").login

POLL_SECONDS = 120


def task_status(headers, task_id):
    r = requests.get(f"{config.API_URL}/task/{task_id}", headers=headers)
    r.raise_for_status()
    return r.json().get("status", "unknown")


def download_bundle(headers, product, task_id):
    out_dir = config.RAW_DIR / product.split(".")[0]
    out_dir.mkdir(parents=True, exist_ok=True)

    r = requests.get(f"{config.API_URL}/bundle/{task_id}", headers=headers)
    r.raise_for_status()
    files = r.json()["files"]

    # netCDF data + the request/metadata files; skip preview PNGs.
    keep = [f for f in files
            if f["file_name"].endswith((".nc", ".json", ".txt", ".xml"))]
    print(f"  {len(keep)} files to fetch into {out_dir}")
    for f in keep:
        dest = out_dir / Path(f["file_name"]).name
        if dest.exists() and dest.stat().st_size == f.get("file_size", -1):
            print(f"    ok (cached)   {dest.name}")
            continue
        print(f"    downloading   {dest.name} "
              f"({f.get('file_size', 0) / 1e6:.1f} MB)")
        with requests.get(f"{config.API_URL}/bundle/{task_id}/{f['file_id']}",
                          headers=headers, stream=True, allow_redirects=True) as s:
            s.raise_for_status()
            with open(dest, "wb") as fh:
                for chunk in s.iter_content(chunk_size=1 << 20):
                    fh.write(chunk)


def main():
    wait = "--wait" in sys.argv
    if not config.TASK_FILE.exists():
        sys.exit("No data/appeears_tasks.json found - run script 02 first.")
    tasks = json.loads(config.TASK_FILE.read_text())

    headers = {"Authorization": f"Bearer {login()}"}
    pending = dict(tasks)
    while pending:
        for product, info in list(pending.items()):
            status = task_status(headers, info["task_id"])
            print(f"{product}: {status}")
            if status == "done":
                download_bundle(headers, product, info["task_id"])
                del pending[product]
        if not pending or not wait:
            break
        print(f"... waiting {POLL_SECONDS} s (Ctrl-C to stop; re-run later, "
              "nothing is lost)")
        time.sleep(POLL_SECONDS)

    if pending:
        print("\nSome tasks are still processing - run this script again "
              "later (or with --wait).")
    else:
        print("\nAll products downloaded. Next: "
              "python scripts/04_extract_timeseries.py")


if __name__ == "__main__":
    main()
