"""Write the synthetic, deliberately messy source files in data/raw/.

The cooperative's real records are not available, so farm, soil, calendar, input,
harvest and price records are simulated (seeded, reproducible). Weather is REAL
(saved Open-Meteo responses). Yields are simulated from that real weather plus
irrigation and soil, so the analysis has a known ground truth to check against:
  * rainfed soybean and cotton yields rise with season rainfall
  * wheat yield falls with hot days
  * irrigated farms both spend more and yield more (a confounder for cost vs yield)
Known defects are injected on purpose; see INJECTED below.

Run `python -m agri.generate_raw --fetch-weather` once to download weather for all farms.
"""
import random
import sys
from pathlib import Path

import pandas as pd

from agri import standardize as s
from agri import weather

RAW, WX = Path("data/raw"), Path("data/weather")
YEARS = range(2019, 2025)
WX_START, WX_END = "2019-05-01", "2025-05-31"
FARMS = [  # raw id, name, district raw text, lat, lon, area, unit, irrigation, soil OC %
    ("F01", "Shinde Farm", "pune ", 18.52, 73.86, 12.0, "acre", "Canal", 0.82),
    ("f-02", "Patil Agro", "NASHIK", 20.00, 73.79, 6.5, "ha", "drip", 0.74),
    ("F3", "Gaikwad Fields", "Ahilyanagar", 19.09, 74.74, 9.0, "acres", "rainfed", 0.48),
    ("F04", "Jadhav Farm", "Solapur", 17.66, 75.91, 4.0, "hectare", "Rain-fed", 0.41),
    ("F 05", "More Brothers", "satara", 17.68, 74.02, 20.0, "acre", "Well", 0.66),
    ("F06", "Kale Farm", "Chhatrapati Sambhajinagar", 19.88, 75.34, 8.0, "acre", "rainfed", 0.45),
    ("f07", "Deshmukh Krishi", "jalna", 19.84, 75.88, 5.5, "ha", "Rainfed", 0.39),
    ("F08", "Pawar Fields", "Latur", 18.40, 76.56, 10.0, "acre", "well", 0.52),
    ("F-09", "Kulkarni Farm", "Kolhapur", 16.70, 74.24, 3.5, "hectare", "Canal", 0.88),
    ("F10", "Mane Agro", "SANGLI", 16.85, 74.58, 15.0, "acres", "drip", 0.71),
    ("F11", "Chavan Farm", "Jalgaon", 21.00, 75.56, 7.0, "ha", "rain-fed", 0.44),
    ("F 12", "Wagh Brothers", "akola", 20.70, 77.00, 9.0, "acre", "Rainfed", 0.50),
]
INJECTED = [
    "F01 wheat rabi 2023: harvest quantity typed x100 (impossible yield)",
    "F02 soybean kharif 2024: no harvest record (incomplete cycle)",
    "F03 wheat rabi 2022: harvest date before sowing date",
    "F04 soybean kharif 2023: planted area missing",
    "F05 soil test 2023: pH 14.2 (impossible)",
    "F04 soybean 2024 fertilizer row: negative cost",
    "F01 soybean kharif 2022: harvest row duplicated",
    "F05 wheat rabi 2024: no input records (input cost unavailable)",
    "F03 soybean kharif 2024: harvest row uses unknown unit 'bags'",
    "F07 cotton kharif 2021: sowing date in US month/day order, day > 12 (unparseable, rejected)",
    "F10 wheat rabi 2022: sowing date typed year-day-month (reads as August, outside the wheat sowing window)",
    "F09 wheat rabi 2020: planted area larger than the whole farm",
    "F11 soil test 2020: organic carbon -0.3 % (impossible)",
    "F12 cotton kharif 2019: harvest typed in kg as if quintals (impossible yield)",
]
CROP_NAMES = {"soybean": ["Soybean", "soya bean", "SOYBEAN "], "wheat": ["Wheat", "wheat", "WHEAT"],
              "cotton": ["Cotton", "kapas", "COTTON"]}
PRICE_LEVEL = {"soybean": [38, 36, 62, 52, 46, 42], "wheat": [19, 20, 21, 24, 25, 27],
               "cotton": [55, 56, 85, 78, 70, 71]}  # INR/kg by YEARS
MARKET_UNIT = {"Pune": "INR/quintal", "Nashik": "INR/quintal", "Ahmednagar": "INR/kg", "Solapur": "INR/quintal",
               "Satara": "INR/tonne", "Aurangabad": "INR/quintal", "Jalna": "INR/quintal", "Latur": "INR/kg",
               "Kolhapur": "INR/quintal", "Sangli": "INR/quintal", "Jalgaon": "INR/quintal", "Akola": "INR/quintal"}
UNIT_MULT = {"INR/kg": 1, "INR/quintal": 100, "INR/tonne": 1000}


def fmt(d, i):  # rotate date formats like hand-kept spreadsheets do
    return [d.strftime("%Y-%m-%d"), d.strftime("%d/%m/%Y"), d.strftime("%d-%b-%Y")][i % 3]


def cycle_dates(rnd, crop, yr):
    if crop == "soybean":
        sow = pd.Timestamp(yr, 6, 18) + pd.Timedelta(days=rnd.randint(0, 20))
        return sow, sow + pd.Timedelta(days=rnd.randint(100, 115))
    if crop == "cotton":
        sow = pd.Timestamp(yr, 6, 15) + pd.Timedelta(days=rnd.randint(0, 25))
        return sow, sow + pd.Timedelta(days=rnd.randint(165, 185))  # last picking
    sow = pd.Timestamp(yr, 11, 5) + pd.Timedelta(days=rnd.randint(0, 20))
    return sow, sow + pd.Timedelta(days=rnd.randint(120, 135))


def sim_yield(rnd, crop, w, irrigated, oc):
    rain, hot = w.precip.sum(), (w.tmax > 35).sum()
    if crop == "soybean":
        y = 900 + (900 if irrigated else 1.1 * min(rain, 900)) + 600 * oc
    elif crop == "cotton":
        y = 600 + (1100 if irrigated else 1.2 * min(rain, 950)) + 500 * oc
    else:
        y = (2600 if irrigated else 1700) + 1200 * oc - 20 * hot
    return max(y * rnd.uniform(0.9, 1.1), 700)


def main():
    rnd = random.Random(42)
    RAW.mkdir(parents=True, exist_ok=True)
    if "--fetch-weather" in sys.argv:
        for f in FARMS:
            weather.fetch(s.farm_id(f[0]), f[3], f[4], WX_START, WX_END, WX)
    pd.DataFrame([dict(farm_code=f[0], farm_name=f[1], district=f[2], state="Maharashtra",
                       lat=f[3], lon=f[4], total_area=f[5], area_unit=f[6], irrigation=f[7])
                  for f in FARMS]).to_csv(RAW / "farms.csv", index=False)

    soil = []
    for f in FARMS:
        for yr in YEARS:
            ph, oc = round(rnd.uniform(6.6, 8.1), 1), round(f[8] + rnd.uniform(-0.05, 0.05), 2)
            if (f[0], yr) == ("F 05", 2023):
                ph = 14.2
            if (f[0], yr) == ("F11", 2020):
                oc = -0.3
            soil.append(dict(farm=f[0], sample_date=f"15/05/{yr}", ph=ph, organic_carbon_pct=oc,
                             available_n_kg_ha=rnd.randint(180, 320)))
    pd.DataFrame(soil).to_csv(RAW / "soil_tests.csv", index=False)

    cal, harv, inp, i = [], [], [], 0
    for f in FARMS:
        fid, irrigated, oc = f[0], f[7].lower() not in ("rainfed", "rain-fed"), f[8]
        farm_ha = f[5] * (0.404686 if "acre" in f[6] else 1)
        wx, _ = weather.load(WX / f"{s.farm_id(fid)}.json")
        for yr in YEARS:
            for crop in ("soybean", "cotton", "wheat"):
                i += 1
                key = (fid, crop, yr)
                sow, hv = cycle_dates(rnd, crop, yr)
                y = sim_yield(rnd, crop, wx.loc[sow:hv], irrigated, oc)
                share = {"soybean": (0.25, 0.35), "cotton": (0.2, 0.3), "wheat": (0.3, 0.45)}[crop]
                area_ha = round(rnd.uniform(*share) * farm_ha, 2)
                area, aunit = (round(area_ha / 0.404686, 1), "acre") if i % 2 else (area_ha, "ha")
                if key == ("F04", "soybean", 2023):
                    area = None
                if key == ("F-09", "wheat", 2020):
                    area, aunit = round(farm_ha * 1.6, 2), "ha"
                sow_txt = fmt(sow, i)
                if key == ("f07", "cotton", 2021):
                    sow, sow_txt = pd.Timestamp(2021, 6, 20), "06/20/2021"
                if key == ("F10", "wheat", 2022):
                    sow = pd.Timestamp(2022, 11, 8)
                    sow_txt = sow.strftime("%Y-%d-%m")
                cal.append(dict(farm_id=fid, crop=rnd.choice(CROP_NAMES[crop]),
                                season="rabi" if crop == "wheat" else "Kharif",
                                sowing_date=sow_txt, harvest_date_planned=fmt(hv, i + 1),
                                area=area, area_unit=aunit))

                kg = y * area_ha
                qty, unit = [(round(kg / 100, 1), "quintal"), (round(kg), "kg"), (round(kg / 1000, 2), "t")][i % 3]
                hdate = hv
                if key == ("F01", "wheat", 2023):
                    qty *= 100
                if key == ("F3", "wheat", 2022):
                    hdate = sow - pd.Timedelta(days=10)
                if key == ("F3", "soybean", 2024):
                    unit = "bags"
                if key == ("F 12", "cotton", 2019):
                    qty, unit = round(kg), "quintal"
                if key != ("f-02", "soybean", 2024):
                    harv.append(dict(farm_id=fid, crop=rnd.choice(CROP_NAMES[crop]),
                                     harvest_date=fmt(hdate, i + 2), quantity=qty, unit=unit))
                if key == ("F01", "soybean", 2022):
                    harv.append(dict(harv[-1]))
                if key == ("F 05", "wheat", 2024):
                    continue
                base = (14000 if irrigated else 8000) * (1.4 if crop == "cotton" else 1)  # INR/ha
                for typ, part in (("seed", 0.25), ("fertilizer", 0.45), ("pesticide", 0.15), ("labour", 0.15)):
                    cost = round(base * part * area_ha * rnd.uniform(0.85, 1.15))
                    if key == ("F04", "soybean", 2024) and typ == "fertilizer":
                        cost = -cost
                    inp.append(dict(farm=fid, crop=crop, input_type=typ,
                                    date=fmt(sow + pd.Timedelta(days=rnd.randint(-5, 40)), i), cost_inr=cost))
    pd.DataFrame(cal).to_csv(RAW / "crop_calendar.csv", index=False)
    pd.DataFrame(harv).to_csv(RAW / "harvests.csv", index=False)
    pd.DataFrame(inp).to_csv(RAW / "inputs.csv", index=False)

    # Weekly mandi modal prices per district; price units vary by market.
    months = {"soybean": (9, 10, 11, 12), "cotton": (11, 12, 1, 2, 3), "wheat": (2, 3, 4, 5)}
    prices = []
    for market, unit in MARKET_UNIT.items():
        for d in pd.date_range("2019-09-01", "2025-05-31", freq="7D"):
            for crop, ms in months.items():
                if d.month not in ms:
                    continue
                yr = d.year if (crop == "soybean" or (crop == "cotton" and d.month >= 9)) else d.year - 1
                if yr not in YEARS or (market, crop, yr) == ("Satara", "wheat", 2024):
                    continue  # Satara 2024 wheat missing -> F05 gross return unavailable
                p = PRICE_LEVEL[crop][yr - YEARS[0]] * rnd.uniform(0.92, 1.08)
                prices.append(dict(market=market, commodity=crop.title(), arrival_date=d.strftime("%Y-%m-%d"),
                                   modal_price=round(p * UNIT_MULT[unit], 2), price_unit=unit))
    pd.DataFrame(prices).to_csv(RAW / "market_prices.csv", index=False)


if __name__ == "__main__":
    main()
