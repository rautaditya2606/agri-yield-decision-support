# Agricultural yield, weather and market decision support

Matches farm, soil, crop-calendar, input, harvest and market-price records by farm, crop, location and date;
joins real weather from the Open-Meteo historical API; validates units and crop cycles; and compares yield,
input cost and gross return across farms and seasons without confusing correlation with causation.

## Run

```bash
pip install -r requirements.txt
python -m agri.pipeline          # -> output/clean_crop_cycles.csv, data_quality_issues.csv, seasonal_report.md
streamlit run app.py             # dashboard
python -m pytest -q              # tests
```

Optional: `python -m agri.generate_raw` rebuilds the sample source files (seeded, same output);
add `--fetch-weather` to download weather again for all farms.

Sample size: 12 farms in 12 Maharashtra districts, 3 crops (soybean and cotton in kharif, wheat in rabi),
6 seasons (2019–2024), giving 216 crop cycles.

## Data

| Source | File | Notes |
|---|---|---|
| Farm profiles | `data/raw/farms.csv` | mixed farm codes (`F01`, `f-02`, `F 05`), district spellings, acre/ha |
| Soil tests | `data/raw/soil_tests.csv` | pH, organic carbon |
| Crop calendar | `data/raw/crop_calendar.csv` | one row per crop cycle; mixed date formats and area units |
| Inputs | `data/raw/inputs.csv` | cost per input event |
| Harvests | `data/raw/harvests.csv` | kg / quintal / tonne |
| Market prices | `data/raw/market_prices.csv` | district mandi modal price in INR per kg / quintal / tonne |
| Weather | `data/weather/F0*.json` | **real** saved Open-Meteo archive responses (request URL kept in `_request`) |

The cooperative's own records were not available, so everything except weather is **synthetic**
(`agri/generate_raw.py`), simulated from the real weather with known effects and 14 injected defects
(listed in `INJECTED`). That gives the checks a ground truth: the tests assert each defect is caught.

## Rules

**Standardisation** (`agri/standardize.py`): farm ids → `F01`; crop and district alias tables
(`Ahilyanagar` → `Ahmednagar`, `Chhatrapati Sambhajinagar` → `Aurangabad`); dates `YYYY-MM-DD`, `DD/MM/YYYY`,
`DD-Mon-YYYY` (slashes are always day-first, anything else is rejected rather than guessed). A sowing date outside
the crop's sowing months (kharif May–Aug, wheat Oct–Jan) is rejected as a likely day/month swap. A swap that
still lands inside the window (e.g. 6 July typed as 07/06) cannot be detected from the date alone. Units: area → ha, mass → kg, price → INR/kg. Season comes from the
sowing date (soybean and cotton = kharif, wheat = rabi YYYY-YY).

**Matching** (`agri/pipeline.py`, `agri/weather.py`)
- harvest → cycle: same farm + crop, harvest within sowing −30 to +200 days
- inputs → cycle: same farm + crop, dated sowing −30 days to harvest
- soil → cycle: latest valid test on or before sowing
- price → cycle: farm's district market, same crop, median price from harvest to harvest +30 days
- weather → cycle: nearest grid cell, rejected if > 15 km from the farm; daily values from sowing to actual
  harvest inclusive (Asia/Kolkata days); needs ≥ 90 % day coverage. Features: season rain, rain in first 30 days,
  mean temperature, growing degree days (base 10 °C), days above 35 °C.

**Validation**: yield outside agronomic limits (soybean and seed cotton 200–5000, wheat 500–9000 kg/ha), pH outside 3–10,
prices outside plausible INR/kg bands, negative costs, unknown units, duplicates, harvest before sowing,
missing area or harvest. Every problem goes to `output/data_quality_issues.csv` with the action taken;
cycles that cannot be trusted get `cycle_complete = False` and a reason.

**Metrics** (only when the inputs exist, else blank): yield kg/ha, input cost INR/ha, gross return INR/ha
(yield × price), net return (gross − recorded inputs).

**Correlation vs causation**: Spearman rho per crop, pooled and within irrigated / rainfed groups, only with
≥ 5 cycles. A pooled link that fades or flips inside both groups is flagged as confounded by irrigation; one
that is clearer inside both groups than pooled is flagged as hidden by mixing them. The
report states these are associations and what study would be needed to claim a cause.
