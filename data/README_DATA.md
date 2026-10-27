# Data — read this first

The raw BTS files are **not committed to this repository**.

- **Source:** Bureau of Transportation Statistics (BTS), U.S. Department of
  Transportation — TranStats table **"Reporting Carrier On-Time Performance
  (1987-present)"** (database OST_R, table DL_On_Time_Performance).
  Downloaded as the twelve monthly pre-zipped CSVs for **calendar year
  2024** from the canonical PREZIP directory:
  https://transtats.bts.gov/PREZIP/
- **Licence:** Works of the U.S. federal government — **public domain**
  (17 U.S.C. § 105). BTS asks only that the Bureau be credited as the
  source.
- **Get the data:** run `python src/01_download_data.py`. It downloads
  the twelve zips into this folder and writes `download_manifest.json`
  here with each file's URL, byte size, HTTP Last-Modified header and
  SHA-256. Verify the data with `python src/00_verify_data.py`, then run
  `python src/02_ontime_analysis.py`.
- **Why not committed:** the twelve zips total ~354 MB (3.2 GB of CSV
  uncompressed). Git hosting is the wrong place for them; the
  manifest's hashes make any local copy re-identifiable byte-for-byte.
- **Filename note (verified 2026-10-27):** older guides cite the monthly
  files as `On_Time_Reporting_Carrier_On_Time_Performance_(1987-present)_YYYY_M.zip`.
  That parenthesised name now returns HTTP 404. The live PREZIP listing
  names the files with underscores:
  `On_Time_Reporting_Carrier_On_Time_Performance_1987_present_YYYY_M.zip`.
  Same table, same publisher — only the file naming changed.
- **Field definitions:** BTS's own documentation for this table is
  bundled inside every monthly zip as `readme.html` (the record
  layout; byte-identical in all twelve 2024 files, SHA-256
  `0ba795b87d903d1b556ea93c19924cab0d240deb478e53a2f551b37ea6686867`),
  mirrored on the TranStats field list,
  https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=FGJ
  (111 fields). The reporting rules are DOT's *Accounting and
  Reporting Directive No. 14 — On-Time Reporting* (see bts.gov,
  "Number 14 - On-Time Reporting"). Definitions used in this project:
  a flight is **on time** if it arrives (departs) less than 15 minutes
  after its published arrival (departure) time; `ArrDelayMinutes` counts
  early arrivals as 0; the five delay-cause fields exist only for
  flights that arrived 15+ minutes late (data from June 2003); for
  diverted flights the arrival-delay fields are NULL by design.
- **Citation:** U.S. Department of Transportation, Bureau of
  Transportation Statistics, *Reporting Carrier On-Time Performance
  (1987-present)*, TranStats. Retrieved 2026-10-27.
