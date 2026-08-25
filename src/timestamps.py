from __future__ import annotations

from zoneinfo import ZoneInfo

import pandas as pd

from .config import BUSINESS_TIMEZONE


def parse_timestamp(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series.replace("", pd.NA), errors="coerce")


def normalize_event_timestamp(df: pd.DataFrame, column: str = "event_at") -> pd.DataFrame:
    out = df.copy()
    if column not in out.columns:
        return out
    raw_col = f"{column}_raw"
    out[raw_col] = out[column]
    out[f"{column}_parsed"] = parse_timestamp(out[column])
    tz_source = out["timezone"] if "timezone" in out.columns else BUSINESS_TIMEZONE

    def to_utc(row):
        ts = row[f"{column}_parsed"]
        if pd.isna(ts):
            return pd.NaT
        tz_name = row["timezone"] if "timezone" in out.columns and row.get("timezone") else BUSINESS_TIMEZONE
        try:
            return ts.tz_localize(ZoneInfo(tz_name)).tz_convert("UTC")
        except (TypeError, ValueError):
            return ts.tz_convert("UTC") if ts.tzinfo else pd.NaT
        except Exception:
            return pd.NaT

    out["timezone_raw"] = tz_source
    out[f"{column}_utc"] = out.apply(to_utc, axis=1)
    out[f"{column}_local"] = out[f"{column}_utc"].dt.tz_convert(BUSINESS_TIMEZONE)
    out[f"{column}_date_local"] = out[f"{column}_local"].dt.date
    out[f"{column}_hour_local"] = out[f"{column}_local"].dt.hour
    return out


def add_month(df: pd.DataFrame, timestamp_col: str) -> pd.DataFrame:
    out = df.copy()
    out["month"] = pd.to_datetime(out[timestamp_col], errors="coerce").dt.to_period("M").astype(str)
    return out
