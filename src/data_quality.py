from __future__ import annotations

import pandas as pd

from .config import PRIMARY_KEYS


def inventory(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in frames.items():
        date_cols = [c for c in df.columns if c.endswith("_at") or c.endswith("_date") or c == "event_at"]
        min_date = max_date = pd.NaT
        if date_cols:
            parsed = pd.concat([pd.to_datetime(df[c].replace("", pd.NA), errors="coerce") for c in date_cols], axis=0)
            min_date = parsed.min()
            max_date = parsed.max()
        rows.append(
            {
                "dataset": name,
                "rows": len(df),
                "columns": len(df.columns),
                "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 3),
                "min_event_date": min_date,
                "max_event_date": max_date,
            }
        )
    return pd.DataFrame(rows)


def schema_audit(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in frames.items():
        for col in df.columns:
            examples = [x for x in df[col].dropna().astype(str).unique()[:3]]
            rows.append({"dataset": name, "column": col, "dtype": str(df[col].dtype), "examples": "; ".join(examples)})
    return pd.DataFrame(rows)


def missingness(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in frames.items():
        for col in df.columns:
            missing = df[col].isna() | (df[col].astype(str) == "")
            rows.append(
                {
                    "dataset": name,
                    "column": col,
                    "missing_count": int(missing.sum()),
                    "missing_pct": round(float(missing.mean()), 6),
                }
            )
    return pd.DataFrame(rows).sort_values(["missing_pct", "missing_count"], ascending=False)


def key_integrity(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, key in PRIMARY_KEYS.items():
        df = frames[name]
        null_key = df[key].isna() | (df[key].astype(str) == "")
        rows.append(
            {
                "dataset": name,
                "primary_key": key,
                "row_count": len(df),
                "unique_count": df.loc[~null_key, key].nunique(),
                "duplicate_count": int(len(df.loc[~null_key]) - df.loc[~null_key, key].nunique()),
                "null_key_count": int(null_key.sum()),
            }
        )
    return pd.DataFrame(rows)


def duplicate_audit(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in frames.items():
        key = PRIMARY_KEYS.get(name)
        exact_dupes = int(df.duplicated(keep=False).sum())
        dup_key_rows = 0
        conflicting_key_rows = 0
        identical_business_key_rows = 0
        if key and key in df:
            key_dupes = df[df[key].duplicated(keep=False) & df[key].notna()]
            dup_key_rows = len(key_dupes)
            if len(key_dupes):
                for _, group in key_dupes.groupby(key, dropna=False):
                    if len(group.drop_duplicates()) == 1:
                        identical_business_key_rows += len(group)
                    else:
                        conflicting_key_rows += len(group)
        rows.append(
            {
                "dataset": name,
                "exact_duplicate_rows": exact_dupes,
                "duplicate_id_rows": dup_key_rows,
                "duplicate_ids_identical_business_rows": identical_business_key_rows,
                "duplicate_ids_conflicting_rows": conflicting_key_rows,
                "legitimate_repeated_events_note": "Event tables may repeat account/borrower by design; primary event IDs remain audited separately.",
            }
        )
    return pd.DataFrame(rows)


def fk_integrity(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    parents = {
        "account_id": set(frames["accounts"]["account_id"].dropna()),
        "borrower_id": set(frames["borrowers"]["borrower_id"].dropna()),
        "agent_id": set(frames["agents"]["agent_id"].dropna()),
        "campaign_id": set(frames["campaigns"]["campaign_id"].dropna()),
        "vendor_id": set(frames["vendor_telephony"]["vendor_id"].dropna()),
    }
    rows = []
    for name, df in frames.items():
        for key, valid in parents.items():
            if key not in df.columns or name in ["accounts", "borrowers", "agents", "campaigns", "vendor_telephony"]:
                continue
            values = df[key]
            nulls = values.isna() | (values.astype(str) == "")
            unmatched = ~values.isin(valid) & ~nulls
            rows.append(
                {
                    "dataset": name,
                    "foreign_key": key,
                    "rows": len(df),
                    "matched_rows": int((values.isin(valid) & ~nulls).sum()),
                    "unmatched_rows": int(unmatched.sum()),
                    "null_fk_rows": int(nulls.sum()),
                    "match_rate": round(float((values.isin(valid) & ~nulls).mean()), 6),
                }
            )
    return pd.DataFrame(rows)


def date_audit(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in frames.items():
        for col in df.columns:
            if col.endswith("_at") or col.endswith("_date") or col in ["event_at", "recorded_at"]:
                parsed = pd.to_datetime(df[col].replace("", pd.NA), errors="coerce")
                rows.append(
                    {
                        "dataset": name,
                        "timestamp_column": col,
                        "min_timestamp": parsed.min(),
                        "max_timestamp": parsed.max(),
                        "invalid_timestamp_count": int(parsed.isna().sum()),
                    }
                )
    return pd.DataFrame(rows)


def categorical_profile(frames: dict[str, pd.DataFrame], max_unique: int = 30) -> pd.DataFrame:
    rows = []
    for name, df in frames.items():
        for col in df.columns:
            if df[col].nunique(dropna=False) <= max_unique:
                counts = df[col].fillna("<NULL>").astype(str).value_counts().head(15)
                for value, count in counts.items():
                    rows.append({"dataset": name, "column": col, "value": value, "count": int(count)})
    return pd.DataFrame(rows)


def payment_duplicate_forensics(payments: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    p = payments.copy()
    p["amount_num"] = pd.to_numeric(p["amount"], errors="coerce")
    p["event_date"] = pd.to_datetime(p["event_at"], errors="coerce").dt.date
    success = p["payment_status"].str.upper().eq("SUCCESS")
    exact_duplicate_rows = p.duplicated(keep=False)
    duplicate_payment_id = p["payment_id"].duplicated(keep=False)
    duplicate_reference = p["payment_reference"].duplicated(keep=False) & p["payment_reference"].ne("")
    suspicious_business_event = p.duplicated(
        subset=["account_id", "event_date", "amount", "payment_method", "provider_id"], keep=False
    )

    flags = p[["payment_id", "payment_reference", "account_id", "event_at", "amount", "payment_status"]].copy()
    flags["exact_duplicate"] = exact_duplicate_rows
    flags["duplicate_payment_id"] = duplicate_payment_id
    flags["duplicate_payment_reference"] = duplicate_reference
    flags["suspicious_same_account_date_amount"] = suspicious_business_event

    raw_success_amount = p.loc[success, "amount_num"].sum()
    deduped = p.sort_values(["event_at", "payment_id"]).drop_duplicates()
    deduped = deduped.drop_duplicates(subset=["payment_id"], keep="first")
    deduped_success = deduped[deduped["payment_status"].str.upper().eq("SUCCESS")].copy()
    deduped_success = deduped_success.drop_duplicates(subset=["payment_reference"], keep="first")
    validated_success_amount = deduped_success["amount_num"].sum()
    summary = pd.DataFrame(
        [
            {
                "raw_payment_rows": len(p),
                "exact_duplicate_rows": int(exact_duplicate_rows.sum()),
                "duplicate_payment_id_rows": int(duplicate_payment_id.sum()),
                "duplicate_payment_reference_rows": int(duplicate_reference.sum()),
                "suspicious_business_event_rows": int(suspicious_business_event.sum()),
                "raw_successful_payment_amount": raw_success_amount,
                "validated_successful_payment_amount": validated_success_amount,
                "overstatement": raw_success_amount - validated_success_amount,
            }
        ]
    )
    return summary, flags, deduped_success.drop(columns=["amount_num", "event_date"], errors="ignore")


def cleaning_impact_rows(frames: dict[str, pd.DataFrame], clean_payments: pd.DataFrame, payment_summary: pd.DataFrame) -> pd.DataFrame:
    p = frames["payments"]
    return pd.DataFrame(
        [
            {
                "dataset": "payments",
                "rule": "successful payments only; exact/payment_id/payment_reference duplicates removed",
                "raw_rows": len(p),
                "corrected_rows": len(clean_payments),
                "rejected_rows": len(p) - len(clean_payments),
                "retained_rows": len(clean_payments),
                "business_impact": f"Recovery overstatement reduced by INR {payment_summary['overstatement'].iloc[0]:,.2f}",
            },
            {
                "dataset": "all",
                "rule": "raw files copied only; original source folder and data/raw files not modified",
                "raw_rows": sum(len(x) for x in frames.values()),
                "corrected_rows": sum(len(x) for x in frames.values()),
                "rejected_rows": 0,
                "retained_rows": sum(len(x) for x in frames.values()),
                "business_impact": "Raw data preserved for auditability.",
            },
        ]
    )
