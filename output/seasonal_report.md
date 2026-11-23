# Seasonal crop-performance report

Cycles in calendar: **216**; complete: **207**; with usable yield: **207**; data-quality issues logged: **16**.

## Data quality

| source        | issue                                             |   count |
|:--------------|:--------------------------------------------------|--------:|
| crop_calendar | area <= 0 or larger than farm                     |       1 |
| crop_calendar | missing planted area                              |       1 |
| crop_calendar | outside crop's sowing window (day/month swapped?) |       1 |
| crop_calendar | unparseable date                                  |       1 |
| harvests      | exact duplicate row                               |       1 |
| harvests      | harvest before sowing                             |       1 |
| harvests      | matches no crop cycle                             |       2 |
| harvests      | unknown unit                                      |       1 |
| harvests      | yield outside 200-5000 kg/ha                      |       1 |
| harvests      | yield outside 500-9000 kg/ha                      |       1 |
| inputs        | negative cost                                     |       1 |
| inputs        | no input records for cycle                        |       1 |
| market_prices | no price within 30 days after harvest             |       1 |
| soil_tests    | impossible measurement                            |       2 |

Incomplete cycles:

| cycle_id                | incomplete_reason                                |
|:------------------------|:-------------------------------------------------|
| F01-wheat-rabi_2023-24  | impossible yield                                 |
| F02-soybean-kharif_2024 | no harvest record                                |
| F03-wheat-rabi_2022-23  | harvest before sowing                            |
| F03-soybean-kharif_2024 | harvest quantity unusable                        |
| F04-soybean-kharif_2023 | missing area                                     |
| F07-cotton-row117       | missing farm/crop/sowing date; no harvest record |
| F09-wheat-rabi_2020-21  | missing area                                     |
| F10-wheat-row175        | missing farm/crop/sowing date; no harvest record |
| F12-cotton-kharif_2019  | impossible yield                                 |

## Season comparison (median per crop and season)

| crop    | season       |   cycles |   median_yield_kg_ha |   median_price_inr_kg |   median_gross_return_ha |   median_input_cost_ha |   rain_mm |   hot_days_35c |
|:--------|:-------------|---------:|---------------------:|----------------------:|-------------------------:|-----------------------:|----------:|---------------:|
| cotton  | kharif 2019  |       11 |               1928.6 |                  53.4 |                 108551   |                17909   |    1145.2 |              0 |
| cotton  | kharif 2020  |       12 |               1969.8 |                  55.6 |                 108989   |                15850   |     945.6 |              0 |
| cotton  | kharif 2021  |       11 |               2005.3 |                  85.1 |                 173524   |                18465   |     881   |              0 |
| cotton  | kharif 2022  |       12 |               1905.8 |                  78.8 |                 151511   |                15260.5 |    1003.2 |              0 |
| cotton  | kharif 2023  |       12 |               1942.8 |                  70.9 |                 132984   |                15180   |     648.4 |              0 |
| cotton  | kharif 2024  |       12 |               1993.8 |                  71.7 |                 140614   |                15202   |    1089.2 |              0 |
| soybean | kharif 2019  |       12 |               2188.4 |                  37.7 |                  83329.5 |                10895   |    1005   |              0 |
| soybean | kharif 2020  |       12 |               2068   |                  36.4 |                  75037   |                10811.5 |     885.4 |              0 |
| soybean | kharif 2021  |       12 |               2148   |                  62   |                 132974   |                10361   |     781.3 |              0 |
| soybean | kharif 2022  |       12 |               2170.4 |                  52.2 |                 114056   |                10658.5 |     870   |              0 |
| soybean | kharif 2023  |       11 |               2111.7 |                  47.4 |                  97750   |                13362   |     628   |              0 |
| soybean | kharif 2024  |       10 |               2127.5 |                  41   |                  86918   |                13730   |    1056.9 |              0 |
| wheat   | rabi 2019-20 |       12 |               2496.8 |                  19.2 |                  48043   |                10663.5 |      12.8 |              3 |
| wheat   | rabi 2020-21 |       11 |               2362.5 |                  20   |                  47179   |                 8518   |      19.6 |             13 |
| wheat   | rabi 2021-22 |       12 |               2651.9 |                  20.9 |                  55377   |                10906   |      72   |             10 |
| wheat   | rabi 2022-23 |       10 |               2698.8 |                  23.8 |                  64643   |                10828   |      24.2 |              2 |
| wheat   | rabi 2023-24 |       11 |               2331.7 |                  25.2 |                  59971   |                 8524   |      44.7 |              8 |
| wheat   | rabi 2024-25 |       12 |               2497.1 |                  27.4 |                  62948   |                 8312   |      12.3 |             21 |

## Farm comparison (mean per farm and crop)

| crop    | farm_id   | farm_name       | irrigated   |   cycles |   mean_yield_kg_ha |   mean_input_cost_ha |   mean_gross_return_ha |   mean_net_return_ha |
|:--------|:----------|:----------------|:------------|---------:|-------------------:|---------------------:|-----------------------:|---------------------:|
| cotton  | F01       | Shinde Farm     | True        |        6 |               2058 |                18692 |                 142940 |               124248 |
| cotton  | F02       | Patil Agro      | True        |        6 |               2116 |                19942 |                 146509 |               126567 |
| cotton  | F03       | Gaikwad Fields  | False       |        6 |               1873 |                11101 |                 127108 |               116007 |
| cotton  | F04       | Jadhav Farm     | False       |        6 |               1808 |                11745 |                 127507 |               115762 |
| cotton  | F05       | More Brothers   | True        |        6 |               2000 |                19356 |                 138602 |               119246 |
| cotton  | F06       | Kale Farm       | False       |        6 |               1932 |                11310 |                 131513 |               120203 |
| cotton  | F07       | Deshmukh Krishi | False       |        5 |               1747 |                11369 |                 115604 |               104235 |
| cotton  | F08       | Pawar Fields    | True        |        6 |               1970 |                19701 |                 138206 |               118505 |
| cotton  | F09       | Kulkarni Farm   | True        |        6 |               2127 |                19855 |                 147778 |               127923 |
| cotton  | F10       | Mane Agro       | True        |        6 |               1993 |                19035 |                 138366 |               119331 |
| cotton  | F11       | Chavan Farm     | False       |        6 |               2005 |                11444 |                 136214 |               124771 |
| cotton  | F12       | Wagh Brothers   | False       |        5 |               1910 |                10630 |                 138600 |               127970 |
| soybean | F01       | Shinde Farm     | True        |        6 |               2310 |                13838 |                 107631 |                93793 |
| soybean | F02       | Patil Agro      | True        |        5 |               2197 |                14093 |                 104554 |                90461 |
| soybean | F03       | Gaikwad Fields  | False       |        5 |               2040 |                 7888 |                  93458 |                85570 |
| soybean | F04       | Jadhav Farm     | False       |        5 |               1994 |                 8251 |                  90647 |                85441 |
| soybean | F05       | More Brothers   | True        |        6 |               2193 |                13639 |                 101574 |                87935 |
| soybean | F06       | Kale Farm       | False       |        6 |               2129 |                 7891 |                  97410 |                89519 |
| soybean | F07       | Deshmukh Krishi | False       |        6 |               2060 |                 7796 |                  95979 |                88183 |
| soybean | F08       | Pawar Fields    | True        |        6 |               2110 |                14196 |                  95148 |                80951 |
| soybean | F09       | Kulkarni Farm   | True        |        6 |               2417 |                14041 |                 112915 |                98874 |
| soybean | F10       | Mane Agro       | True        |        6 |               2142 |                14533 |                  97429 |                82896 |
| soybean | F11       | Chavan Farm     | False       |        6 |               2107 |                 7860 |                  96538 |                88677 |
| soybean | F12       | Wagh Brothers   | False       |        6 |               2095 |                 8066 |                  99840 |                91774 |
| wheat   | F01       | Shinde Farm     | True        |        5 |               3431 |                13761 |                  76694 |                62933 |
| wheat   | F02       | Patil Agro      | True        |        6 |               3380 |                13839 |                  75345 |                61506 |
| wheat   | F03       | Gaikwad Fields  | False       |        5 |               2301 |                 7950 |                  52398 |                44448 |
| wheat   | F04       | Jadhav Farm     | False       |        6 |               1785 |                 8121 |                  39468 |                31347 |
| wheat   | F05       | More Brothers   | True        |        6 |               3221 |                14229 |                  72695 |                58466 |
| wheat   | F06       | Kale Farm       | False       |        6 |               2097 |                 8202 |                  46080 |                37878 |
| wheat   | F07       | Deshmukh Krishi | False       |        6 |               1993 |                 7906 |                  45291 |                37385 |
| wheat   | F08       | Pawar Fields    | True        |        6 |               3077 |                13926 |                  69168 |                55242 |
| wheat   | F09       | Kulkarni Farm   | True        |        5 |               3298 |                13921 |                  76981 |                63060 |
| wheat   | F10       | Mane Agro       | True        |        5 |               2929 |                14635 |                  66478 |                51843 |
| wheat   | F11       | Chavan Farm     | False       |        6 |               1854 |                 8085 |                  42673 |                34588 |
| wheat   | F12       | Wagh Brothers   | False       |        6 |               2078 |                 7939 |                  47535 |                39596 |

## Yield and selling price across seasons

- cotton: kharif 2019 1929 kg/ha @ 53.4 INR/kg, kharif 2020 1970 kg/ha @ 55.6 INR/kg, kharif 2021 2005 kg/ha @ 85.1 INR/kg, kharif 2022 1906 kg/ha @ 78.8 INR/kg, kharif 2023 1943 kg/ha @ 70.9 INR/kg, kharif 2024 1994 kg/ha @ 71.7 INR/kg (rho=0.37)
- soybean: kharif 2019 2188 kg/ha @ 37.7 INR/kg, kharif 2020 2068 kg/ha @ 36.4 INR/kg, kharif 2021 2148 kg/ha @ 62.0 INR/kg, kharif 2022 2170 kg/ha @ 52.2 INR/kg, kharif 2023 2112 kg/ha @ 47.4 INR/kg, kharif 2024 2128 kg/ha @ 41.0 INR/kg (rho=0.31)
- wheat: rabi 2019-20 2497 kg/ha @ 19.2 INR/kg, rabi 2020-21 2362 kg/ha @ 20.0 INR/kg, rabi 2021-22 2652 kg/ha @ 20.9 INR/kg, rabi 2022-23 2699 kg/ha @ 23.8 INR/kg, rabi 2023-24 2332 kg/ha @ 25.2 INR/kg, rabi 2024-25 2497 kg/ha @ 27.4 INR/kg (rho=0.09)

## Associations with yield (Spearman rho, within crop)

- **cotton – growing degree days**: pooled rho = -0.26 (weak, n=70); within groups: irrigated +0.09 (n=36), rainfed +0.08 (n=34)
- **cotton – days above 35 °C**: pooled rho = -0.08 (weak, n=70); within groups: rainfed +0.14 (n=34); irrigated no variation
- **cotton – input cost (INR/ha)**: pooled rho = +0.48 (moderate, n=70); within groups: irrigated +0.13 (n=36), rainfed +0.06 (n=34) → **likely confounded by irrigation**: the pooled link mostly reflects irrigated vs rainfed farms, not this driver itself.
- **cotton – rain in first 30 days (mm)**: pooled rho = +0.23 (weak, n=70); within groups: irrigated +0.18 (n=36), rainfed +0.27 (n=34)
- **cotton – season rainfall (mm)**: pooled rho = +0.22 (weak, n=70); within groups: irrigated +0.08 (n=36), rainfed +0.56 (n=34)
- **cotton – soil organic carbon (%)**: pooled rho = +0.54 (moderate, n=70); within groups: irrigated +0.38 (n=36), rainfed +0.13 (n=34)
- **soybean – growing degree days**: pooled rho = -0.41 (moderate, n=69); within groups: irrigated -0.43 (n=35), rainfed -0.00 (n=34)
- **soybean – days above 35 °C**: pooled rho = +0.00 (weak, n=69); within groups: irrigated -0.19 (n=35), rainfed +0.31 (n=34)
- **soybean – input cost (INR/ha)**: pooled rho = +0.26 (weak, n=68); within groups: irrigated -0.42 (n=35), rainfed -0.07 (n=33)
- **soybean – rain in first 30 days (mm)**: pooled rho = +0.25 (weak, n=69); within groups: irrigated +0.29 (n=35), rainfed +0.23 (n=34)
- **soybean – season rainfall (mm)**: pooled rho = +0.23 (weak, n=69); within groups: irrigated +0.07 (n=35), rainfed +0.53 (n=34)
- **soybean – soil organic carbon (%)**: pooled rho = +0.57 (moderate, n=69); within groups: irrigated +0.58 (n=35), rainfed +0.22 (n=34)
- **wheat – growing degree days**: pooled rho = -0.42 (moderate, n=68); within groups: irrigated -0.69 (n=33), rainfed -0.68 (n=35) → **stronger within each water group**: mixing irrigated and rainfed farms hides part of this link.
- **wheat – days above 35 °C**: pooled rho = -0.38 (weak, n=68); within groups: irrigated -0.70 (n=33), rainfed -0.82 (n=35) → **stronger within each water group**: mixing irrigated and rainfed farms hides part of this link.
- **wheat – input cost (INR/ha)**: pooled rho = +0.73 (strong, n=67); within groups: irrigated -0.23 (n=32), rainfed +0.02 (n=35) → **likely confounded by irrigation**: the pooled link mostly reflects irrigated vs rainfed farms, not this driver itself.
- **wheat – rain in first 30 days (mm)**: pooled rho = +0.04 (weak, n=68); within groups: irrigated +0.06 (n=33), rainfed -0.07 (n=35)
- **wheat – season rainfall (mm)**: pooled rho = -0.06 (weak, n=68); within groups: irrigated +0.12 (n=33), rainfed +0.07 (n=35)
- **wheat – soil organic carbon (%)**: pooled rho = +0.81 (strong, n=68); within groups: irrigated +0.29 (n=33), rainfed +0.39 (n=35) → **likely confounded by irrigation**: the pooled link mostly reflects irrigated vs rainfed farms, not this driver itself.

## How to read this (correlation is not causation)

- Every number above is an **association** across a handful of farm-seasons, not an effect estimate. Correlations need at least 5 paired cycles and are descriptive only; no significance is claimed.
- Farms differ in irrigation, soil and management at the same time. A driver that looks strong when all farms are pooled but fades inside the irrigated and rainfed groups is flagged as confounded; one that is clearer inside each group than pooled is flagged as hidden by mixing.
- Weather is a grid-cell reanalysis (Open-Meteo historical archive, ERA5-based, roughly 10–25 km cells), not an on-farm gauge.
- Gross return = yield × median district mandi price within 30 days after harvest; it ignores when the farmer actually sold. Net return subtracts recorded input cost only (no land, water or family labour).
- To claim a cause (e.g. "more fertiliser raises yield") the cooperative would need a planned comparison: split plots on the same farm and season, or a before/after change with a control farm.

## Decision-support notes

- cotton: farm means within 25 % of each other; no farm flagged.
- soybean: farm means within 25 % of each other; no farm flagged.
- wheat: lowest mean yield F04 (1785 kg/ha, rainfed) vs highest F01 (3431 kg/ha). Rule: gap > 25 % → review agronomy with the low farm; compare like-for-like irrigation first.
- wheat: median yield 2428 kg/ha in seasons with < 15 days above 35 °C vs 2197 kg/ha with ≥ 15. Association only; worth testing earlier sowing on one plot per farm.
- 9 cycle(s) incomplete; fix source records before using them for payouts or benchmarking: F01-wheat-rabi_2023-24, F02-soybean-kharif_2024, F03-wheat-rabi_2022-23, F03-soybean-kharif_2024, F04-soybean-kharif_2023, F07-cotton-row117, F09-wheat-rabi_2020-21, F10-wheat-row175, F12-cotton-kharif_2019
