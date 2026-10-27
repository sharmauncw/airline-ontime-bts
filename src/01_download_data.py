#!/usr/bin/env python3
"""Download the BTS Reporting Carrier On-Time Performance files for 2024.

Provenance
----------
The Bureau of Transportation Statistics (BTS), U.S. Department of
Transportation, publishes the "Reporting Carrier On-Time Performance
(1987-present)" table (TranStats database OST_R) as one pre-zipped CSV
per month on transtats.bts.gov under /PREZIP/. That directory is the
canonical source; this script downloads the twelve 2024 monthly files
directly from it. U.S. Government data -- public domain.

Filename note (verified 2026-10-27)
------------------------------------
Older documentation and many tutorials cite the monthly files as

    On_Time_Reporting_Carrier_On_Time_Performance_(1987-present)_YYYY_M.zip

That parenthesised name now returns HTTP 404 on transtats.bts.gov.
The live /PREZIP/ directory listing shows the current naming uses an
underscore form instead:

    On_Time_Reporting_Carrier_On_Time_Performance_1987_present_YYYY_M.zip

This script uses the live (underscore) names and records, for every
file, its exact URL, byte size, HTTP Last-Modified header, SHA-256 and
zip member list in data/raw/download_manifest.json, so the bytes
behind every number in this project can be re-identified later. Each
zip contains exactly two members: the monthly CSV and a readme.html --
BTS's own record layout for this table, byte-identical in all twelve
2024 files (verified in src/00_verify_data.py). If a future download
of a file whose name already has a manifest entry produces a
different SHA-256, the script refuses to overwrite silently -- it
reports the mismatch and exits non-zero.

The raw zips (~28 MB each) are NOT committed to this repository --
run this script instead. See data/README_DATA.md.
"""
import hashlib
import json
import sys
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

YEAR = 2024
BASE = "https://transtats.bts.gov/PREZIP"
NAME_TEMPLATE = (
    "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip"
)

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
MANIFEST = RAW_DIR / "download_manifest.json"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {"source_table": "Reporting Carrier On-Time Performance (1987-present)",
            "source": "BTS TranStats PREZIP, transtats.bts.gov",
            "year": YEAR, "files": {}}


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    failures = []

    for month in range(1, 13):
        name = NAME_TEMPLATE.format(year=YEAR, month=month)
        url = f"{BASE}/{name}"
        path = RAW_DIR / name
        entry = manifest["files"].get(name)

        if path.exists() and entry is not None:
            digest = sha256_of(path)
            if digest == entry["sha256"]:
                with zipfile.ZipFile(path) as z:
                    entry["members"] = z.namelist()
                print(f"{name}: already downloaded, SHA-256 verified -- skipped")
                continue
            print(
                f"ERROR: {name} exists on disk but its SHA-256 ({digest}) "
                f"differs from the manifest ({entry['sha256']}). "
                "Investigate before overwriting.",
                file=sys.stderr,
            )
            return 1

        print(f"Downloading {url} ...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as resp:
                last_modified = resp.headers.get("Last-Modified")
                data = resp.read()
        except Exception as exc:  # noqa: BLE001 -- report and continue to next month
            print(f"ERROR: download failed for {name}: {exc}", file=sys.stderr)
            failures.append(name)
            continue
        path.write_bytes(data)

        digest = sha256_of(path)
        with zipfile.ZipFile(path) as z:
            members = z.namelist()
            csvs = [m for m in members if m.lower().endswith(".csv")]
            if len(csvs) != 1:
                print(
                    f"ERROR: {name} contains {len(members)} members, "
                    f"{len(csvs)} CSVs -- expected exactly 1 CSV.",
                    file=sys.stderr,
                )
                failures.append(name)
                continue
            csv_member = csvs[0]
        manifest["files"][name] = {
            "url": url,
            "month": month,
            "bytes": path.stat().st_size,
            "sha256": digest,
            "http_last_modified": last_modified,
            "retrieved": date.today().isoformat(),
            "csv_member": csv_member,
            "members": members,
        }
        print(f"  -> {path.stat().st_size:,} bytes, SHA-256 {digest[:16]}..., "
              f"member {csv_member}")

    MANIFEST.write_text(json.dumps(manifest, indent=2))
    print(f"\nWrote {MANIFEST}")
    if failures:
        print(f"FAILED months: {failures}", file=sys.stderr)
        return 1
    print(f"All 12 monthly files for {YEAR} present and hashed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
