from __future__ import annotations

import pandas as pd


def build_channel_touches(
    calls: pd.DataFrame,
    whatsapp: pd.DataFrame,
    sms: pd.DataFrame,
    field: pd.DataFrame,
    targeting: pd.DataFrame,
    campaigns: pd.DataFrame,
) -> pd.DataFrame:
    campaign_channel = campaigns.set_index("campaign_id")["channel"].to_dict() if "campaign_id" in campaigns else {}
    frames = []
    if len(calls):
        x = calls[["account_id", "borrower_id", "event_at_local", "campaign_id"]].copy()
        x["channel"] = x["campaign_id"].map(campaign_channel).fillna("CALL")
        frames.append(x)
    if len(whatsapp):
        x = whatsapp[["account_id", "borrower_id", "event_at_local"]].copy()
        x["campaign_id"] = pd.NA
        x["channel"] = "WHATSAPP"
        frames.append(x)
    if len(sms):
        x = sms[["account_id", "borrower_id", "event_at_local"]].copy()
        x["campaign_id"] = pd.NA
        x["channel"] = "SMS"
        frames.append(x)
    if len(field):
        x = field[["account_id", "borrower_id", "event_at_local"]].copy()
        x["campaign_id"] = pd.NA
        x["channel"] = "FIELD"
        frames.append(x)
    if len(targeting):
        x = targeting[["account_id", "target_date", "campaign_id", "recommended_channel"]].copy()
        x["borrower_id"] = pd.NA
        x["event_at_local"] = pd.to_datetime(x["target_date"], errors="coerce").dt.tz_localize("Asia/Kolkata")
        x["channel"] = x["recommended_channel"].fillna("TARGETING")
        frames.append(x[["account_id", "borrower_id", "event_at_local", "campaign_id", "channel"]])
    touches = pd.concat(frames, ignore_index=True)
    touches["event_at_local"] = pd.to_datetime(touches["event_at_local"], errors="coerce", utc=True).dt.tz_convert("Asia/Kolkata")
    return touches.dropna(subset=["account_id", "event_at_local"])


def attribute_payments(payments: pd.DataFrame, touches: pd.DataFrame, window_days: int) -> pd.DataFrame:
    p = payments.copy()
    p["payment_at_local"] = pd.to_datetime(p["event_at_local"], errors="coerce", utc=True).dt.tz_convert("Asia/Kolkata")
    t = touches.copy()
    if "touch_at_local" not in t.columns and "event_at_local" in t.columns:
        t = t.rename(columns={"event_at_local": "touch_at_local"})
    elif "touch_at_local" in t.columns and "event_at_local" in t.columns:
        t = t.drop(columns=["event_at_local"])
    t = t.loc[:, ~t.columns.duplicated()]
    p = p.sort_values("payment_at_local")
    t = t.sort_values("touch_at_local")
    attributed = pd.merge_asof(
        p,
        t[["account_id", "touch_at_local", "channel", "campaign_id"]],
        left_on="payment_at_local",
        right_on="touch_at_local",
        by="account_id",
        direction="backward",
        tolerance=pd.Timedelta(days=window_days),
    )
    attributed["attribution_window_days"] = window_days
    attributed["attribution_type"] = attributed["touch_at_local"].notna().map({True: "latest_touch_within_window", False: "unattributed_or_organic"})
    return attributed


def channel_performance(attributed: pd.DataFrame, touches: pd.DataFrame) -> pd.DataFrame:
    touch_accounts = touches.groupby("channel")["account_id"].nunique().rename("touched_accounts")
    recovery = attributed.groupby("channel", dropna=False).agg(
        paid_accounts=("account_id", "nunique"),
        recovered_amount=("amount", lambda s: pd.to_numeric(s, errors="coerce").sum()),
    )
    out = recovery.join(touch_accounts, how="outer").reset_index()
    out["channel"] = out["channel"].fillna("UNATTRIBUTED")
    out["paid_accounts"] = out["paid_accounts"].fillna(0)
    out["recovered_amount"] = out["recovered_amount"].fillna(0.0)
    out["touched_accounts"] = out["touched_accounts"].fillna(0)
    out["conversion_rate"] = out["paid_accounts"] / out["touched_accounts"].replace({0: pd.NA})
    return out.sort_values("recovered_amount", ascending=False)
