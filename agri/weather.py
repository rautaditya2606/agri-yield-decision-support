"""Weather from the Open-Meteo historical archive API (no key needed).

Responses are saved as JSON in data/weather/ so the pipeline is reproducible offline.

Matching rules (applied in `match_cycle`):
  * Location: the farm's lat/lon is sent to the API, which snaps to the nearest
    ERA5 grid cell. The cell is accepted only if it is <= MAX_GRID_KM from the farm.
  * Time: daily values (local calendar days, Asia/Kolkata) from sowing date to
    actual harvest date, both inclusive.
  * Coverage: a cycle's weather is usable only if >= MIN_COVERAGE of those days
    have tmax, tmin and precipitation; otherwise features are left empty and flagged.
"""
import json
import math
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

API = "https://archive-api.open-meteo.com/v1/archive"
DAILY = "temperature_2m_max,temperature_2m_min,precipitation_sum"
TZ = "Asia/Kolkata"
MAX_GRID_KM = 15.0
MIN_COVERAGE = 0.9


def fetch(farm_id, lat, lon, start, end, out_dir):
    params = {"latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
              "daily": DAILY, "timezone": TZ}
    url = f"{API}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=60) as r:
        body = json.load(r)
    body["_request"] = {"url": url, "farm_id": farm_id, "farm_lat": lat, "farm_lon": lon}
    Path(out_dir, f"{farm_id}.json").write_text(json.dumps(body))
    return body


def load(path):
    """Return (daily DataFrame indexed by date, response metadata)."""
    body = json.loads(Path(path).read_text())
    d = body["daily"]
    df = pd.DataFrame({"tmax": d["temperature_2m_max"], "tmin": d["temperature_2m_min"],
                       "precip": d["precipitation_sum"]},
                      index=pd.to_datetime(d["time"]))
    return df, body


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * 6371 * math.asin(math.sqrt(a))


def match_cycle(wx, meta, farm_lat, farm_lon, sow, harvest):
    """Weather features for one crop cycle plus a status string explaining any gap."""
    out = {"wx_grid_km": round(haversine_km(farm_lat, farm_lon, meta["latitude"], meta["longitude"]), 1)}
    if out["wx_grid_km"] > MAX_GRID_KM:
        return {**out, "wx_status": "grid_cell_too_far"}
    if pd.isna(sow) or pd.isna(harvest) or harvest < sow:
        return {**out, "wx_status": "no_valid_window"}
    days = pd.date_range(sow, harvest, freq="D")
    w = wx.reindex(days)
    ok = w.dropna()
    out["wx_coverage"] = round(len(ok) / len(days), 3)
    if out["wx_coverage"] < MIN_COVERAGE:
        return {**out, "wx_status": "insufficient_coverage"}
    tmean = (ok.tmax + ok.tmin) / 2
    first30 = ok[ok.index < sow + pd.Timedelta(days=30)]
    return {**out, "wx_status": "ok",
            "rain_mm": round(ok.precip.sum(), 1),
            "rain_first30_mm": round(first30.precip.sum(), 1),
            "tmean_c": round(tmean.mean(), 2),
            "gdd_base10": round((tmean - 10).clip(lower=0).sum(), 0),
            "hot_days_35c": int((ok.tmax > 35).sum())}
