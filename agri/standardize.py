"""Field standardisation: farm ids, crop names, districts, dates and units."""
import re

import pandas as pd

CROPS = {"soybean": "soybean", "soya bean": "soybean", "soya": "soybean", "wheat": "wheat",
         "cotton": "cotton", "kapas": "cotton"}
DISTRICTS = {"pune": "Pune", "nashik": "Nashik", "ahmednagar": "Ahmednagar",
             "ahilyanagar": "Ahmednagar",  # new name of Ahmednagar; mandi prices are filed under the old name
             "solapur": "Solapur", "satara": "Satara",
             "aurangabad": "Aurangabad", "chhatrapati sambhajinagar": "Aurangabad",  # renamed; same as above
             "jalna": "Jalna", "latur": "Latur", "kolhapur": "Kolhapur", "sangli": "Sangli",
             "jalgaon": "Jalgaon", "akola": "Akola"}
AREA_TO_HA = {"ha": 1.0, "hectare": 1.0, "hectares": 1.0, "acre": 0.404686, "acres": 0.404686}
MASS_TO_KG = {"kg": 1.0, "kgs": 1.0, "quintal": 100.0, "qtl": 100.0, "t": 1000.0, "tonne": 1000.0}
PRICE_TO_INR_PER_KG = {"inr/kg": 1.0, "inr/quintal": 0.01, "inr/tonne": 0.001}
IRRIGATED = {"canal": True, "drip": True, "well": True, "rainfed": False, "rain-fed": False}
# Slash dates are day-first (Indian convention); ambiguous mm/dd is never tried.
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%b-%Y")


def farm_id(raw):
    m = re.fullmatch(r"\s*f\s*-?\s*0*(\d+)\s*", str(raw), re.I)
    return f"F{int(m.group(1)):02d}" if m else None


def lookup(table, raw):
    """Case/space-insensitive alias lookup; None when unknown."""
    return None if pd.isna(raw) else table.get(re.sub(r"\s+", " ", str(raw)).strip().lower())


def date(raw):
    if pd.isna(raw):
        return pd.NaT
    for f in DATE_FORMATS:
        try:
            return pd.to_datetime(str(raw).strip(), format=f)
        except ValueError:
            pass
    return pd.NaT


def season(crop, sow):
    """Season label from crop + sowing date, e.g. 'kharif 2023', 'rabi 2023-24'."""
    if pd.isna(sow):
        return None
    if crop in ("soybean", "cotton"):
        return f"kharif {sow.year}"
    y = sow.year if sow.month >= 7 else sow.year - 1
    return f"rabi {y}-{str(y + 1)[2:]}"
