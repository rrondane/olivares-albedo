"""Does warm ENSO (El Nino) change the seasonality of Chilean tornadoes?

Data
----
* Tornado/waterspout database of Bastias-Curivil et al.,
  "Tornadoes and Waterspouts in Chile / Tornados y Trombas en Chile"
  (figshare, doi:10.6084/m9.figshare.25119566). The snapshot in
  data/tornados_trombas_chile_master_2026-08-06.csv is the Final_Table of
  the authors' master workbook (2026-08-06), 116 events 1554-2026.
* Oceanic Nino Index (ONI), CPC/NOAA (oni.ascii.txt), with the official
  episode definition (anomaly >= +-0.5 C for >= 5 consecutive overlapping
  3-month seasons). Snapshot in data/oni.csv (via github.com/ahuang11/ninodata).
* data/eventos_2026_provisional.csv: press-reported events newer than the
  master snapshot, pending curation. Never mixed into the headline result.

Method
------
Each event >= 1950 (ONI era) is assigned the ONI 3-month season centered on
its calendar month (May -> AMJ, etc.): the concurrent ONI anomaly and the
episode phase (el_nino / neutral / la_nina). Events whose season is not yet
published (the ongoing year) take the LATEST available anomaly with a
threshold-only phase, are flagged provisional, and enter only the
"+ provisional" variants. Seasonality is treated as a circular variable
(day of year -> angle). For "warm ENSO" vs "rest" we test:

* difference in circular mean date        (permutation test)
* difference in concentration R           (permutation test)
* Watson's two-sample U2                  (permutation test)
* rank correlation between the concurrent ONI anomaly and the circular
  distance of each event from the climatological mean date (permutation)
* share of events inside the core season  (Fisher exact test)

Everything is repeated for tornado days (unique dates, so the May 2019
outbreak counts once) and for the central-southern subset (lat <= -33).
Run from the repository root:  python enso-tornados/analisis_enso_estacionalidad.py
"""
import math
import os
import sys
from datetime import date

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import figstyle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

figstyle.use()
rng = np.random.default_rng(20240531)   # Talcahuano tornado date as seed
N_PERM = 20000

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "data", "tornados_trombas_chile_master_2026-08-06.csv")
ONI = os.path.join(HERE, "data", "oni.csv")
PROV = os.path.join(HERE, "data", "eventos_2026_provisional.csv")
OUT = os.path.join(HERE, "output")
os.makedirs(OUT, exist_ok=True)

SEASON_OF_MONTH = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ",
                   "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]


def add_time_columns(df):
    df["year"] = df["fecha"].dt.year
    df["month"] = df["fecha"].dt.month
    df["doy"] = df["fecha"].dt.dayofyear
    ylen = np.where(df["fecha"].dt.is_leap_year, 366, 365)
    df["theta"] = 2 * np.pi * (df["doy"] - 0.5) / ylen
    df["season"] = df["month"].map(lambda m: SEASON_OF_MONTH[m - 1])
    return df


# ---------------------------------------------------------------- load data
ev = pd.read_csv(DB)
ev["fecha"] = pd.to_datetime(ev["Date (Gregorian Calendar)"], errors="coerce")
ev["lat"] = pd.to_numeric(ev["Latitude"], errors="coerce")
ev = add_time_columns(ev.dropna(subset=["fecha"]).copy())
ev["provisional"] = False

prov = pd.DataFrame()
if os.path.exists(PROV):
    prov = pd.read_csv(PROV)
    prov["fecha"] = pd.to_datetime(prov["date"])
    prov = add_time_columns(prov)
    prov["provisional"] = True

oni = pd.read_csv(ONI)
merge_cols = ["season", "year", "anom_c", "oni"]
ev = ev.merge(oni[merge_cols], on=["season", "year"], how="left")
if len(prov):
    prov = prov.merge(oni[merge_cols], on=["season", "year"], how="left")

# events in seasons not yet published take the latest final ONI value with a
# threshold-only phase (the >=5-season episode rule needs the full run)
last = oni.dropna(subset=["anom_c"]).iloc[-1]
last_phase = ("el_nino" if last["anom_c"] >= 0.5
              else "la_nina" if last["anom_c"] <= -0.5 else "neutral")
n_pending = 0
for df in (ev, prov):
    if not len(df):
        continue
    miss = df["anom_c"].isna() & (df["year"] >= 1950)
    n_pending += int(miss.sum())
    df.loc[miss, "anom_c"] = last["anom_c"]
    df.loc[miss, "oni"] = last_phase
    df.loc[miss, "provisional"] = True

era_all = ev[ev["year"] >= 1950].copy()
era = era_all[~era_all["provisional"]]
print(f"{len(ev)} dated events in the database, {len(era_all)} in the ONI "
      f"era; headline sample {len(era)} (final ONI, "
      f"{era['year'].min()}-{era['year'].max()})")
print(f"{n_pending} events with unpublished ONI season take "
      f"{last['season']} {int(last['year'])} = {last['anom_c']:+.2f} C "
      f"({last_phase}, provisional); +{len(prov)} press-reported events")

cols = ["fecha", "lat", "theta", "doy", "anom_c", "oni", "year", "month",
        "provisional"]
era_plus = pd.concat([era_all[cols], prov[cols]] if len(prov)
                     else [era_all[cols]], ignore_index=True)

# ---------------------------------------------------------------- circular
def circ_mean_R(theta):
    C, S = np.mean(np.cos(theta)), np.mean(np.sin(theta))
    return math.atan2(S, C) % (2 * np.pi), math.hypot(C, S)


def rayleigh_p(theta):
    """Zar (1999) approximation for the Rayleigh test."""
    n = len(theta)
    _, R = circ_mean_R(theta)
    return math.exp(math.sqrt(1 + 4 * n + 4 * (n * n - (n * R) ** 2))
                    - (1 + 2 * n)), R


def ang_to_date(theta):
    d = theta / (2 * np.pi) * 365.2425
    dt = date(2001, 1, 1) + pd.Timedelta(days=float(d))
    return f"{dt.day:02d}-{figstyle.MESES[dt.month - 1]}"


def circ_dist(a, b):
    """Signed circular difference a-b in (-pi, pi]."""
    return (a - b + np.pi) % (2 * np.pi) - np.pi


def watson_u2(t1, t2):
    """Watson's two-sample U^2 (Zar 1999, eq. 27.17)."""
    n1, n2 = len(t1), len(t2)
    n = n1 + n2
    order = np.argsort(np.concatenate([t1, t2]), kind="mergesort")
    labels = np.concatenate([np.ones(n1), np.zeros(n2)])[order]
    d = np.cumsum(labels) / n1 - np.cumsum(1 - labels) / n2
    return (n1 * n2 / n**2) * (np.sum(d * d) - np.sum(d) ** 2 / n)


def perm_p(stat_fn, t1, t2, n_perm=N_PERM, two_sided=True):
    obs = stat_fn(t1, t2)
    pooled = np.concatenate([t1, t2])
    n1 = len(t1)
    cnt = 0
    for _ in range(n_perm):
        p = rng.permutation(pooled)
        s = stat_fn(p[:n1], p[n1:])
        if (abs(s) >= abs(obs)) if two_sided else (s >= obs):
            cnt += 1
    return obs, (cnt + 1) / (n_perm + 1)


def spearman(x, y):
    rx = pd.Series(x).rank().to_numpy()
    ry = pd.Series(y).rank().to_numpy()
    rx = (rx - rx.mean()) / rx.std()
    ry = (ry - ry.mean()) / ry.std()
    return float(np.mean(rx * ry))


def fisher_exact(a, b, c, d):
    """Two-sided Fisher exact test (sum of tables as or less probable)."""
    n, r1, c1 = a + b + c + d, a + b, a + c

    def hyper(x):
        return (math.comb(r1, x) * math.comb(n - r1, c1 - x)
                / math.comb(n, c1))

    p_obs = hyper(a)
    return sum(hyper(x) for x in range(max(0, c1 - (n - r1)),
                                       min(r1, c1) + 1)
               if hyper(x) <= p_obs * (1 + 1e-9))


# ---------------------------------------------------------------- analysis
def analyze(df, name, report):
    w = df[df["oni"] == "el_nino"]
    r = df[df["oni"] != "el_nino"]
    lines = [f"\n=== {name}: n={len(df)}  "
             f"(El Nino {len(w)}, neutral {sum(df['oni'] == 'neutral')}, "
             f"La Nina {sum(df['oni'] == 'la_nina')})"]
    if len(w) < 5:
        lines.append("    too few warm-ENSO events for a two-sample test")
        report.extend(lines)
        return

    for lbl, g in (("El Nino ", w), ("rest    ", r), ("all     ", df)):
        p, R = rayleigh_p(g["theta"].to_numpy())
        mu, _ = circ_mean_R(g["theta"].to_numpy())
        lines.append(f"    {lbl} n={len(g):3d}  mean date {ang_to_date(mu)}  "
                     f"R={R:.3f}  Rayleigh p={p:.4f}")

    tw, tr = w["theta"].to_numpy(), r["theta"].to_numpy()

    def dmean(a, b):
        return circ_dist(circ_mean_R(a)[0], circ_mean_R(b)[0]) \
            * 365.2425 / (2 * np.pi)

    def dR(a, b):
        return circ_mean_R(a)[1] - circ_mean_R(b)[1]

    obs, p = perm_p(dmean, tw, tr)
    lines.append(f"    d(mean date) El Nino - rest = {obs:+.1f} days   "
                 f"perm p = {p:.3f}")
    obs, p = perm_p(dR, tw, tr)
    lines.append(f"    d(concentration R)          = {obs:+.3f}        "
                 f"perm p = {p:.3f}")
    obs, p = perm_p(watson_u2, tw, tr, two_sided=False)
    lines.append(f"    Watson U2                   = {obs:.3f}         "
                 f"perm p = {p:.3f}")

    # rank correlation: ONI anomaly vs circular distance from the overall mean
    mu_all, _ = circ_mean_R(df["theta"].to_numpy())
    dev = np.abs(circ_dist(df["theta"].to_numpy(), mu_all)) \
        * 365.2425 / (2 * np.pi)
    an = df["anom_c"].to_numpy()
    rho = spearman(an, dev)
    cnt = sum(abs(spearman(rng.permutation(an), dev)) >= abs(rho)
              for _ in range(N_PERM))
    lines.append(f"    Spearman rho(ONI anom, |dev from mean date|) = "
                 f"{rho:+.3f}   perm p = {(cnt + 1) / (N_PERM + 1):.3f}")

    # share of events in the core season (15 May - 15 Jun) and in May-Aug
    for lo, hi, lbl in ((135, 166, "15 May-15 Jun"), (121, 243, "May-Aug")):
        a = int(sum(w["doy"].between(lo, hi)))
        c = int(sum(r["doy"].between(lo, hi)))
        pf = fisher_exact(a, len(w) - a, c, len(r) - c)
        lines.append(f"    core {lbl}: El Nino {a}/{len(w)} vs rest "
                     f"{c}/{len(r)}   Fisher p = {pf:.3f}")
    report.extend(lines)


def by_days(df):
    return (df.sort_values("fecha")
            .groupby("fecha", as_index=False)
            .agg({"theta": "first", "doy": "first", "anom_c": "first",
                  "oni": "first", "lat": "min", "year": "first",
                  "month": "first", "provisional": "any"}))


report = []
analyze(era, f"all events with final ONI (1950-{era['year'].max()})", report)
analyze(by_days(era), "tornado days (unique dates)", report)
analyze(era[era["lat"] <= -33], "central-southern events (lat <= -33)", report)
analyze(by_days(era[era["lat"] <= -33]),
        "central-southern tornado days", report)
if era_plus["provisional"].any():
    analyze(era_plus, "events + 2026 provisional (ENSO provisional)", report)
    analyze(by_days(era_plus), "tornado days + 2026 provisional", report)

# how often is each phase present at all? (base rate over the headline era)
y0, y1 = int(era["year"].min()), int(era["year"].max())
base = oni[(oni["year"] >= y0) & (oni["year"] <= y1)]
share = base["oni"].value_counts(normalize=True)
nw = int(sum(era["oni"] == "el_nino"))
p0 = float(share.get("el_nino", 0))
n = len(era)
pmf = [math.comb(n, k) * p0**k * (1 - p0) ** (n - k) for k in range(n + 1)]
p_binom = sum(p for k, p in enumerate(pmf) if p <= pmf[nw] * (1 + 1e-9))
report.append(f"\nBase rate check: {p0:.1%} of months {y0}-{y1} are "
              f"El Nino episodes -> expected {p0 * n:.1f} of {n} events, "
              f"observed {nw} (exact binomial two-sided p = {p_binom:.3f}). "
              "Events are not independent (outbreaks), so this p is "
              "anti-conservative; it concerns frequency, not seasonality.")

text = "\n".join(report)
print(text)
with open(os.path.join(OUT, "resultados.txt"), "w") as f:
    f.write(__doc__.split("Method")[0] + text + "\n")

# ---------------------------------------------------------------- figure
COL = {"el_nino": "#c4442e", "neutral": "#8a8a8a", "la_nina": "#2e6fb0"}
LBL = {"el_nino": "El Niño", "neutral": "Neutral", "la_nina": "La Niña"}

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(9.2, 3.6), gridspec_kw={"width_ratios": [1.15, 1]})

months = np.arange(1, 13)
width = 0.27
for k, ph in enumerate(("la_nina", "neutral", "el_nino")):
    cnt = (era.loc[era["oni"] == ph, "month"]
           .value_counts().reindex(months, fill_value=0))
    ax1.bar(months + (k - 1) * width, cnt.values, width * 0.92,
            color=COL[ph], label=LBL[ph])
ax1.set_xticks(months)
ax1.set_xticklabels(figstyle.MESES)
ax1.set_ylabel("Número de eventos")
ax1.set_title(f"Eventos por mes y fase ENSO (1950–{era['year'].max()})",
              loc="left")
ax1.legend(frameon=False)
ax1.spines[["top", "right"]].set_visible(False)
ax1.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

ax2.axhspan(-0.5, 0.5, color="0.92", zorder=0)
ax2.axhline(0, color="0.75", lw=0.8, zorder=1)
for ph in ("la_nina", "neutral", "el_nino"):
    g = era[era["oni"] == ph]
    ax2.scatter(g["doy"], g["anom_c"], s=26, color=COL[ph],
                edgecolor="white", linewidth=0.6, zorder=3)
g = era_plus[era_plus["provisional"]]
if len(g):
    ax2.scatter(g["doy"], g["anom_c"], s=34, marker="D", facecolor="none",
                edgecolor=[COL[p] for p in g["oni"]], linewidth=1.3, zorder=4)
    ax2.annotate("2026 (provisional)", xy=(g["doy"].max(), g["anom_c"].max()),
                 xytext=(6, 6), textcoords="offset points", fontsize=8.5,
                 color=COL["el_nino"])
ax2.axvspan(135, 166, color="#c4442e", alpha=0.07, zorder=0)
ax2.set_xticks([1, 60, 121, 182, 244, 305, 365])
ax2.set_xticklabels(["1 ene", "1 mar", "1 may", "1 jul",
                     "1 sep", "1 nov", "31 dic"])
ax2.set_ylabel("Anomalía ONI (°C)")
ax2.set_title("Fecha del evento y ONI concurrente", loc="left")
ax2.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(OUT, f"enso_estacionalidad_tornados.{ext}"),
                dpi=200, bbox_inches="tight")
print(f"\nfigure and results written to {OUT}/")
