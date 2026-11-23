"""Seasonal comparison tables, associations and the markdown report."""
import pandas as pd

DRIVERS = {"rain_mm": "season rainfall (mm)", "rain_first30_mm": "rain in first 30 days (mm)",
           "gdd_base10": "growing degree days", "hot_days_35c": "days above 35 °C",
           "input_cost_ha": "input cost (INR/ha)", "soil_oc_pct": "soil organic carbon (%)"}
MIN_N = 5  # fewer paired cycles than this: no correlation reported


def usable(cycles):
    return cycles[cycles.yield_kg_ha.notna()]


def season_table(cycles):
    g = usable(cycles).groupby(["crop", "season"])
    return g.agg(cycles=("cycle_id", "count"), median_yield_kg_ha=("yield_kg_ha", "median"),
                 median_price_inr_kg=("price_inr_kg", "median"),
                 median_gross_return_ha=("gross_return_ha", "median"),
                 median_input_cost_ha=("input_cost_ha", "median"),
                 rain_mm=("rain_mm", "median"), hot_days_35c=("hot_days_35c", "median")).round(1).reset_index()


def farm_table(cycles):
    g = usable(cycles).groupby(["crop", "farm_id", "farm_name", "irrigated"])
    return g.agg(cycles=("cycle_id", "count"), mean_yield_kg_ha=("yield_kg_ha", "mean"),
                 mean_input_cost_ha=("input_cost_ha", "mean"), mean_gross_return_ha=("gross_return_ha", "mean"),
                 mean_net_return_ha=("net_return_ha", "mean")).round(0).reset_index()


def spearman(df, x, y="yield_kg_ha"):
    d = df[[x, y]].dropna()
    if len(d) < MIN_N or d[x].nunique() < 2:
        return None, len(d)
    return round(d[x].corr(d[y], method="spearman"), 2), len(d)


def associations(cycles):
    """Spearman rho of yield vs each driver, pooled and within irrigation groups."""
    rows = []
    u = usable(cycles)
    for crop, c in u.groupby("crop"):
        for x in DRIVERS:
            for grp, d in (("all", c), ("irrigated", c[c.irrigated == True]), ("rainfed", c[c.irrigated == False])):  # noqa: E712
                rho, n = spearman(d, x)
                rows.append(dict(crop=crop, driver=x, group=grp, rho=rho, n=n))
    return pd.DataFrame(rows)


def _strength(rho):
    a = abs(rho)
    return "strong" if a >= 0.7 else "moderate" if a >= 0.4 else "weak"


def findings(cycles):
    """Plain-language findings with their evidence. Never phrased as causes."""
    a = associations(cycles)
    out = []
    for (crop, x), g in a.groupby(["crop", "driver"]):
        pooled = g[(g.group == "all") & g.rho.notna()]
        if pooled.empty:
            continue
        p = pooled.iloc[0]
        within = g[(g.group != "all") & g.rho.notna()]
        few = g[(g.group != "all") & g.rho.isna()]
        line = (f"**{crop} – {DRIVERS[x]}**: pooled rho = {p.rho:+.2f} ({_strength(p.rho)}, n={p.n})")
        if len(within):
            line += "; within groups: " + ", ".join(f"{r.group} {r.rho:+.2f} (n={r.n})" for r in within.itertuples())
        if len(few):
            line += "; " + ", ".join(f"{r.group} " + (f"too few (n={r.n})" if r.n < MIN_N else "no variation")
                                     for r in few.itertuples())
        # Pooled association that shrinks/flips inside both groups = irrigation is likely the confounder.
        if abs(p.rho) >= 0.4 and len(within) == 2 and all(
                abs(r.rho) < abs(p.rho) / 2 or r.rho * p.rho < 0 for r in within.itertuples()):
            line += (" → **likely confounded by irrigation**: the pooled link mostly reflects irrigated vs "
                     "rainfed farms, not this driver itself.")
        # The reverse: a link clear inside both groups that pooling dilutes.
        elif len(within) == 2 and all(r.rho * p.rho > 0 and abs(r.rho) >= abs(p.rho) + 0.2 and abs(r.rho) >= 0.4
                                      for r in within.itertuples()):
            line += (" → **stronger within each water group**: mixing irrigated and rainfed farms hides part of "
                     "this link.")
        out.append(line)
    return out


def _md(df):
    return df.fillna("–").to_markdown(index=False)


def markdown(cycles, issues):
    u = usable(cycles)
    seasons = season_table(cycles)
    lines = [
        "# Seasonal crop-performance report", "",
        f"Cycles in calendar: **{len(cycles)}**; complete: **{int(cycles.cycle_complete.sum())}**; "
        f"with usable yield: **{len(u)}**; data-quality issues logged: **{len(issues)}**.", "",
        "## Data quality", "",
        _md(issues.groupby(["source", "issue"]).size().rename("count").reset_index()), "",
        "Incomplete cycles:", "",
        _md(cycles.loc[~cycles.cycle_complete, ["cycle_id", "incomplete_reason"]]), "",
        "## Season comparison (median per crop and season)", "", _md(seasons), "",
        "## Farm comparison (mean per farm and crop)", "", _md(farm_table(cycles)), "",
        "## Yield and selling price across seasons", "",
    ]
    for crop, s in seasons.groupby("crop"):
        rho, n = spearman(s, "median_price_inr_kg", "median_yield_kg_ha") if len(s) >= MIN_N else (None, len(s))
        lines.append(f"- {crop}: " + ", ".join(f"{r.season} {r.median_yield_kg_ha:.0f} kg/ha @ "
                                                f"{r.median_price_inr_kg:.1f} INR/kg" for r in s.itertuples())
                     + (f" (only {n} seasons, too few to correlate)" if rho is None else f" (rho={rho})"))
    lines += [
        "", "## Associations with yield (Spearman rho, within crop)", "",
        *[f"- {f}" for f in findings(cycles)], "",
        "## How to read this (correlation is not causation)", "",
        "- Every number above is an **association** across a handful of farm-seasons, not an effect estimate. "
        f"Correlations need at least {MIN_N} paired cycles and are descriptive only; no significance is claimed.",
        "- Farms differ in irrigation, soil and management at the same time. A driver that looks strong when all "
        "farms are pooled but fades inside the irrigated and rainfed groups is flagged as confounded; one that is "
        "clearer inside each group than pooled is flagged as hidden by mixing.",
        "- Weather is a grid-cell reanalysis (Open-Meteo historical archive, ERA5-based, roughly 10–25 km cells), not an on-farm gauge.",
        "- Gross return = yield × median district mandi price within 30 days after harvest; it ignores when "
        "the farmer actually sold. Net return subtracts recorded input cost only (no land, water or family labour).",
        "- To claim a cause (e.g. \"more fertiliser raises yield\") the cooperative would need a planned comparison: "
        "split plots on the same farm and season, or a before/after change with a control farm.", "",
        "## Decision-support notes", "",
        *decision_notes(cycles),
    ]
    return "\n".join(lines) + "\n"


def decision_notes(cycles):
    """Transparent, rule-based suggestions; each states the rule and the evidence."""
    notes, u = [], usable(cycles)
    ft = farm_table(cycles)
    for crop, g in ft.groupby("crop"):
        if g.mean_yield_kg_ha.nunique() > 1:
            lo, hi = g.loc[g.mean_yield_kg_ha.idxmin()], g.loc[g.mean_yield_kg_ha.idxmax()]
            notes.append(f"- {crop}: lowest mean yield {lo.farm_id} ({lo.mean_yield_kg_ha:.0f} kg/ha, "
                         f"{'irrigated' if lo.irrigated else 'rainfed'}) vs highest {hi.farm_id} "
                         f"({hi.mean_yield_kg_ha:.0f} kg/ha). Rule: gap > 25 % → review agronomy with the low farm; "
                         f"compare like-for-like irrigation first."
                         if lo.mean_yield_kg_ha < 0.75 * hi.mean_yield_kg_ha else
                         f"- {crop}: farm means within 25 % of each other; no farm flagged.")
    w = u[(u.crop == "wheat") & u.hot_days_35c.notna()]
    if len(w) >= MIN_N:
        hot = w[w.hot_days_35c >= 15].yield_kg_ha.median()
        cool = w[w.hot_days_35c < 15].yield_kg_ha.median()
        notes.append(f"- wheat: median yield {cool:.0f} kg/ha in seasons with < 15 days above 35 °C vs {hot:.0f} "
                     "kg/ha with ≥ 15. Association only; worth testing earlier sowing on one plot per farm.")
    inc = cycles[~cycles.cycle_complete]
    if len(inc):
        notes.append(f"- {len(inc)} cycle(s) incomplete; fix source records before using them for payouts or "
                     "benchmarking: " + ", ".join(inc.cycle_id))
    return notes
