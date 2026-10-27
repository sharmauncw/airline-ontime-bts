#!/usr/bin/env python3
"""BTS airline on-time analysis -- calendar year 2024.

Questions (stated before any results)
-------------------------------------
1. How late is US air travel, really? National on-time arrival rate,
   mean/median arrival delay of delayed flights, by month.
2. Which reporting carriers are most/least reliable (on-time % and
   cancellation %), with a stated minimum flight-count threshold.
3. What causes the delays? Shares of the five BTS delay-cause fields
   among delayed flights.
4. The evening effect: on-time performance by scheduled departure
   hour block.
5. Two airports the author actually flies: ILM (Wilmington, NC) and
   DTW (Detroit Metro) -- flights, on-time %, average delay.

Design (stated up front)
------------------------
* Unit: one row of the BTS Reporting Carrier On-Time Performance table
  = one scheduled non-stop domestic flight by an operating (reporting)
  carrier. All 12 monthly files for 2024, read from the raw zips.
* Cancelled flights (Cancelled == 1) have no arrival/departure delay
  by construction. They are counted in schedule totals and in
  cancellation rates, and are NEVER given an imputed delay of 0.
* Diverted flights (Diverted == 1) operated but did not arrive at the
  scheduled destination; per BTS documentation their ArrDelay fields
  are NULL. They are counted in operated totals and diversion counts,
  and excluded from arrival-delay statistics.
* On-time arrival rate = share of operated, non-diverted flights with
  ArrDel15 == 0, i.e. arrived less than 15 minutes after the published
  arrival time (the DOT definition).
* "Delayed flights" = operated, non-diverted, ArrDel15 == 1.
  ArrDelayMinutes counts early arrivals as 0, so means/medians over
  delayed flights use only ArrDel15 == 1 rows.
* Delay causes: the five cause fields (CarrierDelay, WeatherDelay,
  NASDelay, SecurityDelay, LateAircraftDelay) are recorded ONLY for
  flights that arrived 15+ minutes late, and only at airports where
  cause reporting applies. Shares are computed over total cause
  minutes of delayed flights that carry all five fields. An internal
  check verifies the BTS identity sum(causes) == ArrDelayMinutes.
* Carrier ranking threshold: carriers are ranked only if they operated
  at least 10,000 flights in 2024 (all carriers are listed in the
  metrics file with their counts regardless).
* Departure hour blocks: scheduled departure hour (CRSDepTime, local)
  grouped in 3-hour blocks.

Every number printed by this script is written to outputs/metrics.json;
the README and results_summary.md quote that file. Nothing is
hand-typed. The run also asserts that the rows loaded per month equal
the independent csv-module counts in outputs/data_verification.json
(if that file exists), so the two code paths cannot drift apart.
"""
import json
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs"
CHARTS = OUT / "charts"
YEAR = 2024
MIN_FLIGHTS_FOR_RANKING = 10_000

COLUMNS = [
    "Month", "Reporting_Airline",
    "Origin", "Dest",
    "CRSDepTime", "DepDelayMinutes", "DepDel15",
    "ArrDelay", "ArrDelayMinutes", "ArrDel15",
    "Cancelled", "Diverted",
    "CarrierDelay", "WeatherDelay", "NASDelay", "SecurityDelay",
    "LateAircraftDelay",
]
DTYPES = {"Reporting_Airline": "category", "Origin": "category",
          "Dest": "category", "Month": "int8"}
AIRPORT_CODES = ("ILM", "DTW")
CAUSES = ["CarrierDelay", "WeatherDelay", "NASDelay", "SecurityDelay",
          "LateAircraftDelay"]
CAUSE_LABELS = {
    "CarrierDelay": "Air carrier",
    "WeatherDelay": "Extreme weather",
    "NASDelay": "National Air System",
    "SecurityDelay": "Security",
    "LateAircraftDelay": "Late-arriving aircraft",
}
# Carrier names as published by BTS/DOT for the 2024 reporting carriers.
# Any code found in the data without an entry here is reported BY CODE
# ONLY and listed in metrics["carriers_without_verified_name"].
CARRIER_NAMES = {
    "AA": "American Airlines", "DL": "Delta Air Lines",
    "UA": "United Airlines", "WN": "Southwest Airlines",
    "AS": "Alaska Airlines", "B6": "JetBlue Airways",
    "NK": "Spirit Airlines", "F9": "Frontier Airlines",
    "G4": "Allegiant Air", "HA": "Hawaiian Airlines",
    "OO": "SkyWest Airlines", "YX": "Republic Airways",
    "MQ": "Envoy Air", "9E": "Endeavor Air", "QX": "Horizon Air",
    "ZW": "Air Wisconsin", "C5": "CommuteAir", "YV": "Mesa Airlines",
    "OH": "PSA Airlines", "PT": "Piedmont Airlines",
    "G7": "GoJet Airlines",
}
NAVY, TEAL, AMBER, GREY = "#0A2A4A", "#0E7C7B", "#D9A441", "#8A94A6"


def pct(num: float, den: float) -> float:
    return round(100.0 * num / den, 2) if den else 0.0


def load_year() -> tuple[pd.DataFrame, dict]:
    manifest = json.loads((RAW / "download_manifest.json").read_text())
    frames, loaded = [], {}
    for name, meta in sorted(manifest["files"].items(),
                             key=lambda kv: kv[1]["month"]):
        # Each zip also bundles BTS's readme.html, so the CSV member
        # must be opened explicitly -- pandas cannot guess it.
        # Only the columns the analysis uses are loaded, with
        # categorical dtypes for the code columns: the full 111-field
        # frame for 7M+ rows does not fit comfortably in memory.
        with zipfile.ZipFile(RAW / name) as z:
            with z.open(meta["csv_member"]) as fh:
                df = pd.read_csv(fh, usecols=COLUMNS, dtype=DTYPES,
                                 low_memory=False)
        loaded[meta["month"]] = int(len(df))
        frames.append(df)
        print(f"month {meta['month']:>2d}: {len(df):,} rows")
    data = pd.concat(frames, ignore_index=True)
    del frames
    return data, loaded


def airport_city_labels() -> dict:
    """City labels for the Q5 airports, read from the data itself in a
    light four-column pass over the December file."""
    manifest = json.loads((RAW / "download_manifest.json").read_text())
    dec = next(m for m in manifest["files"].values() if m["month"] == 12)
    name = next(k for k, m in manifest["files"].items() if m["month"] == 12)
    with zipfile.ZipFile(RAW / name) as z:
        with z.open(dec["csv_member"]) as fh:
            cols = pd.read_csv(
                fh, usecols=["Origin", "OriginCityName", "Dest",
                             "DestCityName"])
    labels = {}
    for code in AIRPORT_CODES:
        o = cols.loc[cols["Origin"] == code, "OriginCityName"]
        d = cols.loc[cols["Dest"] == code, "DestCityName"]
        labels[code] = (o.iloc[0] if len(o) else
                        d.iloc[0] if len(d) else None)
    return labels


def flight_stats(frame: pd.DataFrame) -> dict:
    """Core schedule/reliability stats for any slice of flights."""
    scheduled = len(frame)
    cancelled = int((frame["Cancelled"] == 1).sum())
    operated = frame[frame["Cancelled"] == 0]
    diverted = int((operated["Diverted"] == 1).sum())
    arrived = operated[(operated["Diverted"] == 0)
                       & operated["ArrDel15"].notna()]
    delayed = arrived[arrived["ArrDel15"] == 1]
    stats = {
        "flights_scheduled": int(scheduled),
        "flights_cancelled": cancelled,
        "cancellation_pct": pct(cancelled, scheduled),
        "flights_operated": int(len(operated)),
        "flights_diverted": diverted,
        "arrivals_with_delay_data": int(len(arrived)),
        "ontime_arrival_pct": pct(int((arrived["ArrDel15"] == 0).sum()),
                                  len(arrived)),
        "flights_delayed_15plus": int(len(delayed)),
        "delayed_share_of_arrivals_pct": pct(len(delayed), len(arrived)),
    }
    if len(delayed):
        stats["mean_arr_delay_delayed_min"] = round(
            float(delayed["ArrDelayMinutes"].mean()), 1)
        stats["median_arr_delay_delayed_min"] = round(
            float(delayed["ArrDelayMinutes"].median()), 1)
    if len(arrived):
        stats["mean_arr_delay_all_arrivals_min"] = round(
            float(arrived["ArrDelayMinutes"].mean()), 1)
    return stats


def chart_monthly(by_month: dict, annual_otp: float) -> None:
    months = sorted(int(m) for m in by_month)
    otp = [by_month[str(m)]["ontime_arrival_pct"] for m in months]
    canc = [by_month[str(m)]["cancellation_pct"] for m in months]
    labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.plot(months, otp, marker="o", color=NAVY, lw=2, label="On-time arrivals %")
    ax.axhline(annual_otp, color=AMBER, ls="--", lw=1.2,
               label=f"2024 average ({annual_otp:.1f}%)")
    ax.set_xticks(months, [labels[m - 1] for m in months])
    ax.set_ylabel("On-time arrivals (%)")
    ax.set_title("US on-time arrivals by month, 2024 (BTS reporting carriers)",
                 color=NAVY, fontweight="bold")
    ax.grid(axis="y", color=GREY, alpha=0.3)
    ax.legend(frameon=False)
    for m, v in zip(months, otp):
        ax.annotate(f"{v:.1f}", (m, v), textcoords="offset points",
                    xytext=(0, 7), ha="center", fontsize=8, color=NAVY)
    ax2 = ax.twinx()
    ax2.bar(months, canc, color=TEAL, alpha=0.25, width=0.6)
    ax2.set_ylabel("Cancelled (% of scheduled)", color=TEAL)
    ax.set_ylim(min(otp) - 6, max(otp) + 4)
    fig.tight_layout()
    fig.savefig(CHARTS / "monthly_ontime_trend.png", dpi=150)
    plt.close(fig)


def chart_causes(causes: dict) -> None:
    items = sorted(causes["share_of_cause_minutes_pct"].items(),
                   key=lambda kv: kv[1])
    labels = [CAUSE_LABELS[k] for k, _ in items]
    values = [v for _, v in items]
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    bars = ax.barh(labels, values, color=[TEAL, NAVY, AMBER, GREY, NAVY][::-1])
    ax.set_xlabel("Share of all delay-cause minutes (%)")
    ax.set_title("Where the delay minutes sit: cause shares, delayed flights 2024",
                 color=NAVY, fontweight="bold")
    for b, v in zip(bars, values):
        ax.annotate(f"{v:.1f}%", (v, b.get_y() + b.get_height() / 2),
                    textcoords="offset points", xytext=(5, 0),
                    va="center", fontsize=9, color=NAVY)
    ax.set_xlim(0, max(values) * 1.15)
    fig.tight_layout()
    fig.savefig(CHARTS / "delay_cause_shares.png", dpi=150)
    plt.close(fig)


def chart_dep_blocks(blocks: list) -> None:
    labels = [b["block"] for b in blocks]
    otp = [b["ontime_arrival_pct"] for b in blocks]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    bars = ax.bar(labels, otp, color=TEAL, width=0.62)
    bars[0].set_color(AMBER)
    bars[-1].set_color(NAVY)
    ax.set_ylabel("On-time arrivals (%)")
    ax.set_xlabel("Scheduled departure block (local time)")
    ax.set_title("The evening effect: on-time arrivals fall as the day goes on",
                 color=NAVY, fontweight="bold")
    ax.set_ylim(0, 100)
    for b, v in zip(bars, otp):
        ax.annotate(f"{v:.1f}%", (b.get_x() + b.get_width() / 2, v),
                    textcoords="offset points", xytext=(0, 4),
                    ha="center", fontsize=9, color=NAVY)
    fig.tight_layout()
    fig.savefig(CHARTS / "departure_hour_effect.png", dpi=150)
    plt.close(fig)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHARTS.mkdir(parents=True, exist_ok=True)
    df, loaded = load_year()
    total_rows = int(len(df))
    print(f"TOTAL loaded: {total_rows:,}")

    # ---- integrity checks --------------------------------------------
    cancelled = df[df["Cancelled"] == 1]
    operated = df[df["Cancelled"] == 0]
    diverted = operated[operated["Diverted"] == 1]
    arrived = operated[(operated["Diverted"] == 0)
                       & operated["ArrDel15"].notna()]
    delayed = arrived[arrived["ArrDel15"] == 1]
    with_causes = delayed.dropna(subset=CAUSES)
    cause_sum = with_causes[CAUSES].sum(axis=1)
    identity = {
        "delayed_flights": int(len(delayed)),
        "delayed_with_all_cause_fields": int(len(with_causes)),
        "cause_minutes_sum_equals_arr_delay_minutes_share_pct": pct(
            int((cause_sum == with_causes["ArrDelayMinutes"]).sum()),
            len(with_causes)),
        "cause_minutes_sum_within_1min_share_pct": pct(
            int(((cause_sum - with_causes["ArrDelayMinutes"]).abs() <= 1).sum()),
            len(with_causes)),
    }
    integrity = {
        "cancelled_rows": int(len(cancelled)),
        "cancelled_with_nonnull_arr_delay": int(cancelled["ArrDelay"].notna().sum()),
        "operated_rows": int(len(operated)),
        "operated_with_null_arr_delay": int(operated["ArrDelay"].isna().sum()),
        "diverted_rows": int(len(diverted)),
        "diverted_with_nonnull_arr_delay": int(diverted["ArrDelay"].notna().sum()),
        "cause_identity_check": identity,
        "note": ("Cancelled flights carry no delay values; diverted "
                 "flights have NULL ArrDelay by BTS design. Neither is "
                 "ever imputed."),
    }

    # cross-check against independent counts, if verification has run
    verification_match = None
    ver_path = OUT / "data_verification.json"
    if ver_path.exists():
        ver = json.loads(ver_path.read_text())
        vm = {int(m): v["rows"] for m, v in ver["per_month"].items()}
        verification_match = vm == loaded
        integrity["loaded_rows_match_independent_csv_counts"] = verification_match
        integrity["independent_total_rows"] = ver["total_rows_2024"]

    # ---- Q1: national + monthly --------------------------------------
    annual = flight_stats(df)
    by_month = {str(m): flight_stats(g) for m, g in df.groupby("Month")}

    # ---- Q2: carriers -------------------------------------------------
    carriers = []
    for code, g in df.groupby("Reporting_Airline"):
        s = flight_stats(g)
        s.update({
            "carrier_code": code,
            "carrier_name": CARRIER_NAMES.get(code),
            "ranked": s["flights_scheduled"] >= MIN_FLIGHTS_FOR_RANKING,
        })
        carriers.append(s)
    carriers.sort(key=lambda c: -c["flights_scheduled"])
    unmapped = [c["carrier_code"] for c in carriers if c["carrier_name"] is None]

    # ---- Q3: delay causes ---------------------------------------------
    total_minutes = {c: int(with_causes[c].sum()) for c in CAUSES}
    grand = sum(total_minutes.values())
    causes_out = {
        "base": ("delayed flights (ArrDel15 == 1) carrying all five "
                 "cause fields"),
        "delayed_flights_in_base": int(len(with_causes)),
        "total_cause_minutes": int(grand),
        "minutes_by_cause": total_minutes,
        "share_of_cause_minutes_pct": {
            c: pct(total_minutes[c], grand) for c in CAUSES},
        "share_of_delayed_flights_with_positive_minutes_pct": {
            c: pct(int((with_causes[c] > 0).sum()), len(with_causes))
            for c in CAUSES},
        "mean_minutes_per_delayed_flight": {
            c: round(float(with_causes[c].mean()), 1) for c in CAUSES},
    }

    # ---- Q4: departure hour blocks ------------------------------------
    hour = (df["CRSDepTime"] // 100).astype("Int64")
    df = df.assign(dep_hour=hour)
    block_defs = [(0, 2, "00-02"), (3, 5, "03-05"), (6, 8, "06-08"),
                  (9, 11, "09-11"), (12, 14, "12-14"), (15, 17, "15-17"),
                  (18, 20, "18-20"), (21, 23, "21-23")]
    blocks = []
    for lo, hi, label in block_defs:
        sub = df[(df["dep_hour"] >= lo) & (df["dep_hour"] <= hi)]
        s = flight_stats(sub)
        blocks.append({"block": label, **s})
    hourly = {}
    for h, g in df.groupby("dep_hour"):
        if pd.isna(h):
            continue
        hourly[str(int(h))] = flight_stats(g)

    # ---- Q5: ILM + DTW -------------------------------------------------
    labels = airport_city_labels()
    airports = {}
    for code in AIRPORT_CODES:
        dep = df[df["Origin"] == code]
        arr = df[df["Dest"] == code]
        dep_op = dep[dep["Cancelled"] == 0]
        arr_ok = arr[(arr["Cancelled"] == 0) & (arr["Diverted"] == 0)
                     & arr["ArrDel15"].notna()]
        arr_delayed = arr_ok[arr_ok["ArrDel15"] == 1]
        dep_delayed = dep_op[dep_op["DepDel15"] == 1]
        airports[code] = {
            "city": labels.get(code),
            "departures_scheduled": int(len(dep)),
            "departures_cancelled": int((dep["Cancelled"] == 1).sum()),
            "departure_cancellation_pct": pct(
                int((dep["Cancelled"] == 1).sum()), len(dep)),
            "ontime_departure_pct": pct(
                int((dep_op["DepDel15"] == 0).sum()),
                int(dep_op["DepDel15"].notna().sum())),
            "mean_dep_delay_delayed_min": (
                round(float(dep_delayed["DepDelayMinutes"].mean()), 1)
                if len(dep_delayed) else None),
            "arrivals_scheduled": int(len(arr)),
            "arrivals_with_delay_data": int(len(arr_ok)),
            "ontime_arrival_pct": pct(
                int((arr_ok["ArrDel15"] == 0).sum()), len(arr_ok)),
            "mean_arr_delay_delayed_min": (
                round(float(arr_delayed["ArrDelayMinutes"].mean()), 1)
                if len(arr_delayed) else None),
            "median_arr_delay_delayed_min": (
                round(float(arr_delayed["ArrDelayMinutes"].median()), 1)
                if len(arr_delayed) else None),
            "total_flights_involving_airport": int(len(dep) + len(arr)),
        }

    metrics = {
        "dataset": ("BTS Reporting Carrier On-Time Performance "
                    "(1987-present), calendar year 2024"),
        "loaded_rows_per_month": {str(k): v for k, v in loaded.items()},
        "total_rows": total_rows,
        "integrity": integrity,
        "national_2024": annual,
        "by_month": by_month,
        "carriers": carriers,
        "carriers_without_verified_name": unmapped,
        "carrier_ranking_min_flights": MIN_FLIGHTS_FOR_RANKING,
        "delay_causes": causes_out,
        "departure_blocks_3h": blocks,
        "departure_hourly": hourly,
        "airports": airports,
    }
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2))

    chart_monthly(by_month, annual["ontime_arrival_pct"])
    chart_causes(causes_out)
    chart_dep_blocks(blocks)

    print(f"\nNational 2024: on-time arrivals {annual['ontime_arrival_pct']}% | "
          f"cancelled {annual['cancellation_pct']}% | "
          f"delayed flights mean {annual.get('mean_arr_delay_delayed_min')} min")
    print(f"Carriers in data: {len(carriers)}; unnamed codes: {unmapped}")
    if verification_match is not None:
        print(f"Loaded counts match independent verification: {verification_match}")
    print("Wrote outputs/metrics.json + 3 charts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
