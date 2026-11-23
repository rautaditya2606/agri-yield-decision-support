"""Raw files -> clean crop-cycle dataset + data-quality issue log.

Matching rules (one crop cycle = one crop-calendar row):
  * harvest  -> cycle: same farm + crop, harvest date in [sowing - 30 d, sowing + 200 d].
               A harvest dated before sowing still matches so the error can be flagged.
  * inputs   -> cycle: same farm + crop, input date in [sowing - 30 d, harvest].
  * soil     -> cycle: same farm, latest valid test on or before sowing.
  * price    -> cycle: market = farm district, same crop, arrival date in
               [harvest, harvest + 30 d]; median modal price in INR/kg.
  * weather  -> see agri/weather.py.
"""
from pathlib import Path

import pandas as pd

from agri import standardize as s
from agri import weather

# Agronomic ceilings/floors in kg/ha; outside these a record is treated as impossible.
YIELD_RANGE = {"soybean": (200, 5000), "wheat": (500, 9000), "cotton": (200, 5000)}  # cotton = seed cotton
PRICE_RANGE = {"soybean": (15, 150), "wheat": (10, 80), "cotton": (30, 150)}  # INR/kg
# Months a crop can be sown in Maharashtra; anything else is usually a day/month swap.
SOWING_MONTHS = {"soybean": (5, 6, 7, 8), "cotton": (5, 6, 7, 8), "wheat": (10, 11, 12, 1)}
PH_RANGE, OC_RANGE = (3.0, 10.0), (0.0, 10.0)
ROOT = Path(__file__).resolve().parent.parent


class Log:
    def __init__(self):
        self.rows = []

    def add(self, source, record, field, value, issue, action):
        self.rows.append(dict(source=source, record=str(record), field=field, value="" if pd.api.types.is_scalar(value) and pd.isna(value) else str(value),
                              issue=issue, action=action))


def _farms(raw, log):
    df = pd.read_csv(raw / "farms.csv")
    out = pd.DataFrame({
        "farm_id": df.farm_code.map(s.farm_id),
        "farm_name": df.farm_name.str.strip(),
        "district": df.district.map(lambda v: s.lookup(s.DISTRICTS, v)),
        "lat": df.lat, "lon": df.lon,
        "farm_area_ha": df.total_area * df.area_unit.map(lambda u: s.lookup(s.AREA_TO_HA, u)),
        "irrigated": df.irrigation.map(lambda v: s.lookup(s.IRRIGATED, v)),
    })
    for col in ("farm_id", "district", "farm_area_ha", "irrigated"):
        for i in out.index[out[col].isna()]:
            log.add("farms", i + 2, col, df.iloc[i].to_dict(), "unrecognised value", "left blank")
    return out


def _soil(raw, log):
    df = pd.read_csv(raw / "soil_tests.csv")
    df["farm_id"] = df.farm.map(s.farm_id)
    df["sample_date"] = df.sample_date.map(s.date)
    bad = ~df.ph.between(*PH_RANGE) | ~df.organic_carbon_pct.between(*OC_RANGE)
    for i in df.index[bad]:
        log.add("soil_tests", i + 2, "ph/organic_carbon_pct",
                f"pH={df.ph[i]}, OC={df.organic_carbon_pct[i]}", "impossible measurement", "test excluded")
    return df[~bad]


def _calendar(raw, log, farms):
    df = pd.read_csv(raw / "crop_calendar.csv")
    out = pd.DataFrame({
        "farm_id": df.farm_id.map(s.farm_id),
        "crop": df.crop.map(lambda v: s.lookup(s.CROPS, v)),
        "sowing_date": df.sowing_date.map(s.date),
        "area_ha": df.area * df.area_unit.map(lambda u: s.lookup(s.AREA_TO_HA, u)),
    })
    for i in out.index[out.sowing_date.isna() & df.sowing_date.notna()]:
        log.add("crop_calendar", i + 2, "sowing_date", df.sowing_date[i], "unparseable date", "cycle incomplete")
    for i in out.index[df.sowing_date.isna()]:
        log.add("crop_calendar", i + 2, "sowing_date", "", "missing sowing date", "cycle incomplete")
    for i in out.index[out.sowing_date.notna() & out.crop.notna()]:
        if out.sowing_date[i].month not in SOWING_MONTHS[out.crop[i]]:
            log.add("crop_calendar", i + 2, "sowing_date", df.sowing_date[i],
                    "outside crop's sowing window (day/month swapped?)", "date rejected; cycle incomplete")
            out.loc[i, "sowing_date"] = pd.NaT
    out["season"] = [s.season(c, d) for c, d in zip(out.crop, out.sowing_date)]
    # Without a valid sowing date there is no season, so the calendar row number identifies the cycle.
    out["cycle_id"] = (out.farm_id.fillna("?") + "-" + out.crop.fillna("?") + "-"
                       + out.season.str.replace(" ", "_").fillna(pd.Series(out.index + 2, index=out.index).map("row{}".format)))
    cap = out.farm_id.map(farms.set_index("farm_id").farm_area_ha)
    for i, r in out.iterrows():
        if pd.isna(r.area_ha):
            log.add("crop_calendar", i + 2, "area", df.area[i], "missing planted area", "per-area metrics blank")
        elif r.area_ha <= 0 or r.area_ha > cap[i]:
            log.add("crop_calendar", i + 2, "area", r.area_ha, "area <= 0 or larger than farm", "per-area metrics blank")
            out.loc[i, "area_ha"] = None
        for col in ("farm_id", "crop"):
            if pd.isna(r[col]):
                log.add("crop_calendar", i + 2, col, df.iloc[i].to_dict(), "unrecognised value", "cycle incomplete")
    return out


def _harvests(raw, log):
    df = pd.read_csv(raw / "harvests.csv")
    dup = df.duplicated()
    for i in df.index[dup]:
        log.add("harvests", i + 2, "*", df.iloc[i].to_dict(), "exact duplicate row", "dropped")
    df = df[~dup]
    out = pd.DataFrame({
        "farm_id": df.farm_id.map(s.farm_id),
        "crop": df.crop.map(lambda v: s.lookup(s.CROPS, v)),
        "harvest_date": df.harvest_date.map(s.date),
        "harvest_kg": df.quantity * df.unit.map(lambda u: s.lookup(s.MASS_TO_KG, u)),
        "row": df.index + 2,
    })
    for i in out.index[out.harvest_kg.isna()]:
        log.add("harvests", out.row[i], "unit", df.unit[i], "unknown unit", "quantity left blank")
    return out


def _inputs(raw, log):
    df = pd.read_csv(raw / "inputs.csv")
    df["farm_id"] = df.farm.map(s.farm_id)
    df["crop"] = df.crop.map(lambda v: s.lookup(s.CROPS, v))
    df["date"] = df.date.map(s.date)
    neg = df.cost_inr < 0
    for i in df.index[neg]:
        log.add("inputs", i + 2, "cost_inr", df.cost_inr[i], "negative cost", "row excluded; cycle input cost blank")
    df["bad"] = neg
    return df


def _prices(raw, log):
    df = pd.read_csv(raw / "market_prices.csv")
    df["district"] = df.market.map(lambda v: s.lookup(s.DISTRICTS, v))
    df["crop"] = df.commodity.map(lambda v: s.lookup(s.CROPS, v))
    df["date"] = df.arrival_date.map(s.date)
    df["inr_per_kg"] = df.modal_price * df.price_unit.map(lambda u: s.lookup(s.PRICE_TO_INR_PER_KG, u))
    lo = df.crop.map(lambda c: PRICE_RANGE.get(c, (0, 0))[0])
    hi = df.crop.map(lambda c: PRICE_RANGE.get(c, (0, 0))[1])
    bad = df.inr_per_kg.isna() | ~df.inr_per_kg.between(lo, hi)
    for i in df.index[bad]:
        log.add("market_prices", i + 2, "modal_price", f"{df.modal_price[i]} {df.price_unit[i]}",
                "unknown unit or impossible price", "excluded")
    return df[~bad]


def build(raw_dir=ROOT / "data/raw", weather_dir=ROOT / "data/weather"):
    raw, log = Path(raw_dir), Log()
    farms = _farms(raw, log)
    soil, cal = _soil(raw, log), _calendar(raw, log, farms)
    harv, inputs, prices = _harvests(raw, log), _inputs(raw, log), _prices(raw, log)
    wx = {f: weather.load(Path(weather_dir) / f"{f}.json") for f in farms.farm_id.dropna()}
    fmeta = farms.set_index("farm_id")
    used_harvests, rows = set(), []

    for _, c in cal.iterrows():
        r = c.to_dict()
        f = fmeta.loc[c.farm_id] if c.farm_id in fmeta.index else None
        reasons = []
        if f is not None:
            r.update(farm_name=f.farm_name, district=f.district, irrigated=f.irrigated)
        if pd.isna(c.sowing_date) or pd.isna(c.crop) or f is None:
            reasons.append("missing farm/crop/sowing date")

        h = harv[(harv.farm_id == c.farm_id) & (harv.crop == c.crop)]
        # No sowing date = no window; matching anyway could steal another season's harvest.
        h = h[(h.harvest_date - c.sowing_date).dt.days.between(-30, 200)] if pd.notna(c.sowing_date) else h[:0]
        h = h[~h.row.isin(used_harvests)]
        if len(h) == 0:
            reasons.append("no harvest record")
        else:
            h = h.iloc[0]
            used_harvests.add(h.row)
            r.update(harvest_date=h.harvest_date, harvest_kg=h.harvest_kg)
            if h.harvest_date < c.sowing_date:
                reasons.append("harvest before sowing")
                log.add("harvests", h.row, "harvest_date", f"harvest {h.harvest_date.date()}, sowing {c.sowing_date.date()}",
                        "harvest before sowing", "cycle incomplete")
                r["harvest_kg"] = None
            elif pd.isna(h.harvest_kg):
                reasons.append("harvest quantity unusable")
        if pd.isna(c.area_ha):
            reasons.append("missing area")

        # yield, with impossible values flagged and removed
        if pd.notna(r.get("harvest_kg")) and pd.notna(c.area_ha):
            y = r["harvest_kg"] / c.area_ha
            lo, hi = YIELD_RANGE[c.crop]
            if lo <= y <= hi:
                r["yield_kg_ha"] = round(y, 1)
            else:
                log.add("harvests", h.row, "quantity", round(y), f"yield outside {lo}-{hi} kg/ha",
                        "yield blank; cycle incomplete")
                reasons.append("impossible yield")

        end = r.get("harvest_date", pd.NaT)
        if pd.notna(c.sowing_date) and pd.notna(end) and end >= c.sowing_date:
            i = inputs[(inputs.farm_id == c.farm_id) & (inputs.crop == c.crop)
                       & inputs.date.between(c.sowing_date - pd.Timedelta(days=30), end)]
            if len(i) == 0:
                log.add("inputs", "-", "*", c.cycle_id, "no input records for cycle", "input cost blank")
            elif not i.bad.any() and pd.notna(c.area_ha):
                r["input_cost_ha"] = round(i.cost_inr.sum() / c.area_ha)

            p = prices[(prices.district == r.get("district")) & (prices.crop == c.crop)
                       & prices.date.between(end, end + pd.Timedelta(days=30))]
            if len(p):
                r["price_inr_kg"] = round(p.inr_per_kg.median(), 2)
            else:
                log.add("market_prices", "-", "*", c.cycle_id, "no price within 30 days after harvest",
                        "gross return blank")
            if f is not None:
                r.update(weather.match_cycle(*wx[c.farm_id], f.lat, f.lon, c.sowing_date, end))

        st = soil[(soil.farm_id == c.farm_id) & (soil.sample_date <= c.sowing_date)] if pd.notna(c.sowing_date) else soil[:0]
        if len(st):
            last = st.sort_values("sample_date").iloc[-1]
            r.update(soil_ph=last.ph, soil_oc_pct=last.organic_carbon_pct)

        if pd.notna(r.get("yield_kg_ha")) and pd.notna(r.get("price_inr_kg")):
            r["gross_return_ha"] = round(r["yield_kg_ha"] * r["price_inr_kg"])
            if pd.notna(r.get("input_cost_ha")):
                r["net_return_ha"] = r["gross_return_ha"] - r["input_cost_ha"]
        r["cycle_complete"] = not reasons
        r["incomplete_reason"] = "; ".join(reasons)
        rows.append(r)

    for _, h in harv[~harv.row.isin(used_harvests)].iterrows():
        log.add("harvests", h.row, "*", f"{h.farm_id} {h.crop} {h.harvest_date}", "matches no crop cycle", "dropped")

    cols = ["cycle_id", "farm_id", "farm_name", "district", "irrigated", "crop", "season", "sowing_date",
            "harvest_date", "area_ha", "harvest_kg", "yield_kg_ha", "input_cost_ha", "price_inr_kg",
            "gross_return_ha", "net_return_ha", "soil_ph", "soil_oc_pct", "wx_status", "wx_grid_km",
            "wx_coverage", "rain_mm", "rain_first30_mm", "tmean_c", "gdd_base10", "hot_days_35c",
            "cycle_complete", "incomplete_reason"]
    return pd.DataFrame(rows).reindex(columns=cols), pd.DataFrame(log.rows)


def main(out_dir=ROOT / "output"):
    from agri import report
    cycles, issues = build()
    out = Path(out_dir)
    out.mkdir(exist_ok=True)
    cycles.to_csv(out / "clean_crop_cycles.csv", index=False)
    issues.to_csv(out / "data_quality_issues.csv", index=False)
    (out / "seasonal_report.md").write_text(report.markdown(cycles, issues))
    print(f"{len(cycles)} cycles ({cycles.cycle_complete.sum()} complete), {len(issues)} issues -> {out}/")


if __name__ == "__main__":
    main()
