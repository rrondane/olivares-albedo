"""Figures of the glacier albedo time series.

Reads data/processed/albedo_timeseries.csv and produces (PNG + PDF in
figures/):

  albedo_diario        one line per extended summer of daily MOD10A1
                       glacier-mean snow albedo on a common Nov-Mar axis,
                       with the big wildfire summers highlighted
  albedo_veranos       mean DJF albedo of every summer for the three
                       albedo variables, with the wildfire summers shaded

Colors are from the Okabe-Ito colorblind-safe palette; series are also
distinguished by marker shape and line style, never by hue alone.

Usage (from the repository root):
    python scripts/05_plot_timeseries.py
"""
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config
import figstyle

figstyle.use()

# Okabe-Ito
BLUE, ORANGE, BLACK, GRAY = "#0072B2", "#E69F00", "#000000", "#BBBBBB"
FIRE_COLORS = {2017: ORANGE, 2023: BLUE}

MIN_DAYS_FOR_MEAN = 10  # DJF days required to accept a summer mean


def check_labels(*texts):
    missing = figstyle.check(*texts)
    if missing:
        print(f"WARNING: figure font lacks glyphs {missing}", file=sys.stderr)


def to_reference_summer(dates):
    """Map every date onto a single Nov 1999 - Mar 2000 axis (2000 is a
    leap year, so Feb 29 always has a place)."""
    return pd.to_datetime([
        f"{1999 if d.month >= 11 else 2000}-{d.month:02d}-{d.day:02d}"
        for d in dates])


def save(fig, stem):
    config.FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        path = config.FIGURE_DIR / f"{stem}.{ext}"
        fig.savefig(path, dpi=300, bbox_inches="tight")
        print(f"  saved {path.relative_to(config.ROOT)}")


def plot_daily(df):
    daily = df[(df["product"] == "MOD10A1")
               & (df["variable"] == "snow_albedo")].dropna(subset=["mean"])
    if daily.empty:
        print("No MOD10A1 data yet - skipping the daily figure")
        return

    fig, ax = plt.subplots(figsize=(9, 4.5))
    y0, y1 = int(daily["summer"].min()), int(daily["summer"].max())
    for summer, grp in daily.groupby("summer"):
        x = to_reference_summer(grp["date"])
        if summer in config.FIRE_SUMMERS:
            ax.plot(x, grp["mean"], "-", color=FIRE_COLORS[int(summer)],
                    lw=1.8, marker="o", ms=3, zorder=3,
                    label=config.FIRE_SUMMERS[int(summer)])
        else:
            ax.plot(x, grp["mean"], "-", color=GRAY, lw=0.7, alpha=0.8,
                    zorder=1)
    # one legend proxy for the gray family
    ax.plot([], [], "-", color=GRAY, lw=0.7,
            label=f"otros veranos ({y0}-{y1})")

    ax.set_ylabel("Albedo de nieve MOD10A1 (fracción)")
    ax.set_title("Albedo diario de verano, glaciares Olivares Alfa y Beta")
    ax.xaxis.set_major_formatter(figstyle.fecha_formatter("{d} {mes}"))
    ax.set_ylim(0, 1)
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, loc="upper right")
    check_labels(*[t.get_text() for t in ax.get_legend().get_texts()],
                 ax.get_ylabel(), ax.get_title())
    save(fig, "albedo_diario")
    plt.close(fig)


def plot_summer_means(df):
    core = df[df["date"].dt.month.isin(config.CORE_SUMMER_MONTHS)]
    series = [
        ("MOD10A1", "snow_albedo", "MOD10A1 albedo de nieve", BLUE, "o", "-"),
        ("MCD43A3", "black_sky_albedo", "MCD43A3 cielo negro", ORANGE, "s", "--"),
        ("MCD43A3", "white_sky_albedo", "MCD43A3 cielo blanco", BLACK, "^", ":"),
    ]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    for product, variable, label, color, marker, ls in series:
        sel = core[(core["product"] == product)
                   & (core["variable"] == variable)].dropna(subset=["mean"])
        means = sel.groupby("summer")["mean"].agg(["mean", "count"])
        means = means[means["count"] >= MIN_DAYS_FOR_MEAN]
        if means.empty:
            continue
        ax.plot(means.index, means["mean"], ls, color=color, marker=marker,
                ms=5, lw=1.5, label=label)

    for summer, label in config.FIRE_SUMMERS.items():
        ax.axvspan(summer - 0.4, summer + 0.4, color="0.85", zorder=0)
        ax.annotate(label.split("(")[1].rstrip(")"), xy=(summer, 0.02),
                    ha="center", fontsize=8, rotation=90, va="bottom")

    ax.set_xlabel("Verano (año en que termina)")
    ax.set_ylabel("Albedo medio DEF (fracción)")
    ax.set_title("Albedo medio de verano, glaciares Olivares Alfa y Beta")
    ax.set_ylim(0, 1)
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, loc="upper right")
    check_labels(*[t.get_text() for t in ax.get_legend().get_texts()],
                 ax.get_xlabel(), ax.get_ylabel(), ax.get_title())
    save(fig, "albedo_veranos")
    plt.close(fig)


def main():
    if not config.TIMESERIES_FILE.exists():
        sys.exit("No time series CSV - run script 04 first.")
    df = pd.read_csv(config.TIMESERIES_FILE, parse_dates=["date"])
    plot_daily(df)
    plot_summer_means(df)


if __name__ == "__main__":
    main()
