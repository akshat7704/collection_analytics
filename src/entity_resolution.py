from __future__ import annotations

import pandas as pd


def resolve_agents(agents: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    clean = agents.copy()
    for col in ["agent_id", "employee_code", "agent_name", "vendor_id", "joined_at"]:
        if col not in clean.columns:
            clean[col] = pd.NA

    non_null_codes = clean["employee_code"].replace("", pd.NA)
    code_counts = clean.assign(employee_code=non_null_codes).groupby("employee_code", dropna=True)["agent_id"].nunique()
    trusted_codes = set(code_counts[code_counts >= 1].index)

    def canonical(row):
        if pd.notna(row["employee_code"]) and row["employee_code"] in trusted_codes:
            return f"EMP::{row['employee_code']}"
        return f"AGT::{row['agent_id']}"

    clean["canonical_agent_id"] = clean.apply(canonical, axis=1)
    clean["resolution_method"] = clean["employee_code"].replace("", pd.NA).apply(
        lambda x: "employee_code" if pd.notna(x) else "agent_id"
    )
    clean["resolution_confidence"] = clean["resolution_method"].map({"employee_code": "HIGH", "agent_id": "MEDIUM"})
    mapping = clean[
        ["agent_id", "canonical_agent_id", "resolution_method", "resolution_confidence"]
    ].rename(columns={"agent_id": "raw_agent_id"})
    return clean, mapping


def resolve_borrowers(borrowers: pd.DataFrame, accounts: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    clean = borrowers.copy()
    account_counts = accounts.groupby("borrower_id", dropna=False)["account_id"].nunique().rename("account_count")
    clean = clean.merge(account_counts, on="borrower_id", how="left")
    clean["canonical_borrower_id"] = "BRW::" + clean["borrower_id"].astype(str)
    clean["resolution_method"] = "stable_borrower_id"
    clean["resolution_confidence"] = "HIGH"
    mapping = clean[
        ["borrower_id", "canonical_borrower_id", "resolution_method", "resolution_confidence", "account_count"]
    ].rename(columns={"borrower_id": "raw_borrower_id"})
    return clean, mapping
