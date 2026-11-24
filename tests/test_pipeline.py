import pandas as pd
import pytest

from agri import standardize as s
from agri import weather
from agri.pipeline import build
from agri.report import findings


def test_ids_names_dates():
    assert [s.farm_id(v) for v in ("F01", "f-02", "F3", "F 05", "X9")] == ["F01", "F02", "F03", "F05", None]
    assert s.lookup(s.CROPS, " SOYA  bean ") == "soybean"
    assert s.lookup(s.DISTRICTS, "Ahilyanagar") == "Ahmednagar"
    assert s.date("04/10/2023") == pd.Timestamp(2023, 10, 4)  # day-first
    assert s.date("12-Oct-2022") == s.date("2022-10-12")
    assert pd.isna(s.date("10/31/2023"))  # US order rejected, not guessed
    assert s.season("wheat", pd.Timestamp(2024, 1, 3)) == "rabi 2023-24"


def test_weather_window_and_rules():
    days = pd.date_range("2023-01-01", "2023-01-10")
    wx = pd.DataFrame({"tmax": 36.0, "tmin": 20.0, "precip": 2.0}, index=days)
    meta = {"latitude": 18.5, "longitude": 73.9}
    r = weather.match_cycle(wx, meta, 18.5, 73.9, days[0], days[-1])
    assert r["wx_status"] == "ok" and r["rain_mm"] == 20.0 and r["hot_days_35c"] == 10 and r["gdd_base10"] == 180
    assert weather.match_cycle(wx, meta, 19.5, 73.9, days[0], days[-1])["wx_status"] == "grid_cell_too_far"
    assert weather.match_cycle(wx.iloc[:5], meta, 18.5, 73.9, days[0], days[-1])["wx_status"] == "insufficient_coverage"


@pytest.fixture(scope="module")
def built():
    return build()


def test_injected_defects_are_caught(built):
    c, issues = built[0].set_index("cycle_id"), built[1]
    reasons = c.incomplete_reason
    assert reasons["F01-wheat-rabi_2023-24"] == "impossible yield"
    assert reasons["F02-soybean-kharif_2024"] == "no harvest record"
    assert reasons["F03-wheat-rabi_2022-23"] == "harvest before sowing"
    assert reasons["F03-soybean-kharif_2024"] == "harvest quantity unusable"
    assert reasons["F04-soybean-kharif_2023"] == "missing area"
    assert pd.isna(c.loc["F04-soybean-kharif_2024", "input_cost_ha"])  # negative cost row
    assert pd.isna(c.loc["F05-wheat-rabi_2024-25", "gross_return_ha"])  # no price
    assert reasons["F09-wheat-rabi_2020-21"] == "missing area"  # area larger than farm, blanked
    assert reasons["F12-cotton-kharif_2019"] == "impossible yield"
    assert set(issues.issue) >= {"exact duplicate row", "impossible measurement", "unknown unit",
                                 "unparseable date", "outside crop's sowing window (day/month swapped?)"}
    # Rows with a rejected sowing date must not grab a harvest; their harvests are logged as unmatched.
    assert c.filter(like="-row", axis=0).harvest_kg.isna().all()
    assert (issues.issue == "matches no crop cycle").sum() == 2
    assert len(c) == 216 and c.cycle_complete.sum() == 207


def test_metrics_and_units(built):
    c = built[0]
    ok = c[c.gross_return_ha.notna()]
    assert (abs(ok.gross_return_ha - ok.yield_kg_ha * ok.price_inr_kg) <= 1).all()
    assert c.price_inr_kg.dropna().between(15, 150).all()  # quintal/kg/tonne all normalised to INR/kg
    assert set(c.crop) == {"soybean", "wheat", "cotton"} and c.district.notna().all()  # incl. renamed districts
    assert (c.loc[c.yield_kg_ha.notna(), "wx_status"] == "ok").all()


def test_confounding_flagged(built):
    # Generator makes irrigated farms spend more AND yield more; pooled cost-yield link must be flagged.
    f = findings(built[0])
    assert "confounded by irrigation" in next(x for x in f if x.startswith("**wheat – input cost"))
    # Generator lowers wheat yield on hot days on every farm; pooling irrigated + rainfed dilutes it.
    assert "stronger within each water group" in next(x for x in f if x.startswith("**wheat – days above"))


def test_runs_without_scipy(built, monkeypatch):
    # Streamlit Cloud installs only requirements.txt; pandas' method="spearman" would need scipy.
    import sys
    monkeypatch.setitem(sys.modules, "scipy", None)
    assert findings(built[0])
