# Airline On-Time 2024 — results summary

All numbers below are copied from `outputs/metrics.json`, written by
`src/02_ontime_analysis.py` on its runs of 2026-10-27 (exit 0 twice;
`metrics.json` byte-identical across both runs, SHA-256
`961151e266736fc38ea104fd6f69fcd8fd1a62d6dc2a60557f73a34f95c098d7`).
Row counts are independently verified in `outputs/data_verification.json`
(csv-module counts == pandas counts, all 12 months).

## The year in one paragraph

7,079,061 scheduled flights; 96,315 cancelled (1.36%); 17,499 diverted;
79.18% of arrivals on time. 1,449,966 flights (20.82% of arrivals)
arrived 15+ minutes late, averaging 71.6 minutes late (median 41.0).
Across all arrivals, the average arrival delay was 15.9 minutes
(early arrivals counted as 0, per BTS's ArrDelayMinutes convention).

## By month

| Month | Scheduled | Cancelled % | On-time arrivals % | Delayed flights' mean delay (min) |
|---|---|---|---|---|
| Jan | 547,271 | 3.73 | 75.94 | 75.5 |
| Feb | 519,221 | 0.58 | 84.08 | 64.1 |
| Mar | 591,767 | 0.87 | 79.15 | 69.8 |
| Apr | 582,185 | 0.69 | 80.94 | 68.7 |
| May | 609,743 | 1.35 | 73.59 | 76.6 |
| Jun | 611,132 | 1.29 | 75.06 | 73.5 |
| Jul | 634,613 | 2.89 | 70.38 | 80.6 |
| Aug | 619,025 | 2.05 | 76.53 | 74.8 |
| Sep | 582,622 | 0.60 | 84.49 | 61.6 |
| Oct | 615,497 | 1.02 | 86.80 | 61.0 |
| Nov | 575,404 | 0.46 | 85.33 | 62.9 |
| Dec | 590,581 | 0.70 | 78.85 | 71.4 |

Best month: October (86.80% on time). Worst: July (70.38%; 29.62% of
arrivals 15+ late). Most cancellations: January (20,389; 3.73%).
Fewest: November (0.46%).

## Carriers (operating/reporting carriers; all 15 ranked, threshold 10,000 flights)

| Carrier | Scheduled | On-time arrivals % | Cancelled % | Delayed flights' mean delay (min) |
|---|---|---|---|---|
| Republic Airways (YX) | 301,465 | 85.93 | 1.85 | 67.5 |
| Hawaiian Airlines (HA) | 78,530 | 84.55 | 1.05 | 46.2 |
| Endeavor Air (9E) | 200,094 | 84.17 | 2.30 | 79.9 |
| Delta Air Lines (DL) | 1,009,174 | 82.74 | 0.91 | 72.0 |
| SkyWest Airlines (OO) | 744,658 | 81.00 | 1.15 | 80.4 |
| United Airlines (UA) | 760,451 | 80.14 | 1.64 | 72.7 |
| Southwest Airlines (WN) | 1,419,419 | 79.40 | 0.83 | 54.0 |
| Envoy Air (MQ) | 279,955 | 79.14 | 1.42 | 64.6 |
| Allegiant Air (G4) | 117,210 | 78.33 | 1.72 | 88.7 |
| PSA Airlines (OH) | 227,971 | 78.23 | 1.65 | 83.6 |
| Alaska Airlines (AS) | 245,819 | 77.93 | 1.96 | 50.5 |
| Spirit Airlines (NK) | 261,103 | 76.07 | 1.91 | 70.2 |
| JetBlue Airways (B6) | 240,282 | 74.49 | 1.55 | 78.7 |
| American Airlines (AA) | 984,306 | 73.87 | 1.55 | 85.7 |
| Frontier Airlines (F9) | 208,624 | 71.26 | 2.32 | 79.4 |

YX, 9E, OO, MQ and OH are regional operators that fly under the major
brands' names. Lowest cancellation rate: Southwest (0.83%), then
Delta (0.91%). Highest: Frontier (2.32%).

## Delay causes (delayed flights only; 103,794,712 cause minutes over 1,449,964 flights)

| Cause | Minutes | Share of minutes | Delayed flights with any minutes in this cause |
|---|---|---|---|
| Late-arriving aircraft | 41,973,684 | 40.44% | 51.26% |
| Air carrier | 35,823,263 | 34.51% | 54.41% |
| National Air System | 19,621,964 | 18.90% | 50.06% |
| Extreme weather | 6,195,873 | 5.97% | 6.13% |
| Security | 179,928 | 0.17% | 0.51% |

Integrity: for 100.0% of delayed flights carrying cause fields, the
five causes sum exactly to the flight's ArrDelayMinutes. Causes exist
only for flights arriving 15+ minutes late; weather's role in
*cancellations* is not visible in this table.

## The evening effect (by scheduled departure block, local time)

| Block | Scheduled | On-time arrivals % | Arrivals delayed 15+ % |
|---|---|---|---|
| 00–02 | 17,951 | 79.63 | 20.37 |
| 03–05 | 201,784 | 90.86 | 9.14 |
| 06–08 | 1,471,334 | 88.10 | 11.90 |
| 09–11 | 1,277,046 | 83.44 | 16.56 |
| 12–14 | 1,249,554 | 78.76 | 21.24 |
| 15–17 | 1,260,613 | 73.38 | 26.62 |
| 18–20 | 1,140,621 | 70.12 | 29.88 |
| 21–23 | 460,157 | 72.97 | 27.03 |

From the 03–05 peak, on-time performance falls with every block until
18–20. The 00–02 block is a small set of red-eyes (17,951 flights) and
the 21–23 recovery is partial (last flights of the day, thinner
schedule). One flight in the year carries CRSDepTime 2400; it is in
every total except these blocks.

## Two airports

| | ILM — Wilmington, NC | DTW — Detroit, MI |
|---|---|---|
| Departures scheduled | 8,069 | 131,367 |
| Departures cancelled | 1.75% | 1.03% |
| On-time departures | 83.03% | 81.64% |
| On-time arrivals | 79.67% | 82.00% |
| Delayed arrivals' mean delay | 65.9 min (median 44.0) | 80.0 min (median 45.0) |
| Total flights involving the airport | 16,141 | 262,727 |

ILM tracks the national picture closely (arrivals 79.67% vs 79.18%
nationally) but cancels more departures than average (1.75% vs
1.36%). DTW beats the nation on both cancellations (1.03%) and on-time
arrivals (82.00%) — but when a DTW arrival is late, it is later than
the national pattern (80.0 vs 71.6 minutes). ILM's counts are small
(~8,000 per direction), so its percentages carry wider uncertainty
than DTW's.
