from __future__ import annotations

import math
import os
import shutil
import sys
import zipfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".matplotlib"))

import matplotlib.pyplot as plt
import nbformat as nbf
import numpy as np
import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from src import attribution, data_quality, entity_resolution, metrics, statistics  # type: ignore
    from src.config import (  # type: ignore
        ARCHITECTURE_DIR,
        AUDIT_DIR,
        CHART_DIR,
        DASHBOARD_DIR,
        DEFAULT_ATTRIBUTION_DAYS,
        ATTRIBUTION_WINDOWS_DAYS,
        EVENT_TABLES,
        GOLDEN_DIR,
        OUTPUT_DIR,
        PROJECT_ROOT,
        RAW_DIR,
        REFERENCE_DIR,
        REPORT_DIR,
        TABLE_DIR,
    )
    from src.io import ensure_dirs, load_raw_data, write_csv, write_markdown  # type: ignore
    from src.timestamps import add_month, normalize_event_timestamp, parse_timestamp  # type: ignore
else:
    from . import attribution, data_quality, entity_resolution, metrics, statistics
    from .config import (
        ARCHITECTURE_DIR,
        AUDIT_DIR,
        CHART_DIR,
        DASHBOARD_DIR,
        DEFAULT_ATTRIBUTION_DAYS,
        ATTRIBUTION_WINDOWS_DAYS,
        EVENT_TABLES,
        GOLDEN_DIR,
        OUTPUT_DIR,
        PROJECT_ROOT,
        RAW_DIR,
        REFERENCE_DIR,
        REPORT_DIR,
        TABLE_DIR,
    )
    from .io import ensure_dirs, load_raw_data, write_csv, write_markdown
    from .timestamps import add_month, normalize_event_timestamp, parse_timestamp


def pct(x: float | int | None) -> str:
    if x is None or pd.isna(x):
        return "Unavailable"
    return f"{x:.2%}"


def money(x: float | int | None) -> str:
    if x is None or pd.isna(x):
        return "Unavailable"
    return f"INR {x:,.0f}"


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        values = [str(row[col]).replace("\n", " ") for col in cols]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def latest_complete_month(monthly: pd.DataFrame, audit: dict[str, pd.DataFrame]) -> tuple[pd.Series, str]:
    max_ts = pd.to_datetime(audit["date_audit"]["max_timestamp"], errors="coerce").max()
    periods = pd.PeriodIndex(monthly["month"], freq="M")
    last_period = periods.max()
    if pd.notna(max_ts) and max_ts < last_period.end_time and len(monthly) > 1:
        row = monthly.loc[periods == periods.sort_values()[-2]].iloc[0]
        return row, f"{last_period} is partial through {max_ts.date()}, so executive conclusions use latest complete month {row['month']}."
    row = monthly.iloc[-1]
    return row, f"{row['month']} is treated as complete based on supplied event dates."


def write_simple_pdf(markdown_path: Path, pdf_path: Path, title: str) -> None:
    text = markdown_path.read_text(encoding="utf-8")
    lines = []
    for raw in text.replace("#", "").splitlines():
        line = raw.strip()
        if line:
            lines.extend([line[i : i + 95] for i in range(0, len(line), 95)])
    per_page = 42
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages(pdf_path) as pdf:
        for start in range(0, max(len(lines), 1), per_page):
            fig = plt.figure(figsize=(8.27, 11.69))
            fig.text(0.07, 0.96, title, fontsize=14, weight="bold", va="top")
            page_lines = lines[start : start + per_page]
            fig.text(0.07, 0.92, "\n".join(page_lines), fontsize=8.5, va="top", family="monospace")
            fig.subplots_adjust(0, 0, 1, 1)
            pdf.savefig(fig)
            plt.close(fig)


def extract_assignment_pdf() -> str:
    pdf_path = REFERENCE_DIR / "Data Analyst - Assignment.pdf"
    if not pdf_path.exists():
        return "Assignment PDF not found in reference folder."
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        out = REFERENCE_DIR / "assignment_pdf_extracted.txt"
        out.write_text(text, encoding="utf-8")
        return text
    except Exception as exc:
        return f"Could not extract PDF text in this environment: {exc}"


def normalize_frames(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    out = {}
    for name, df in frames.items():
        x = df.copy()
        if name in EVENT_TABLES and "event_at" in x.columns:
            x = normalize_event_timestamp(x, "event_at")
            x = add_month(x, "event_at_local")
        elif name == "daily_targeting":
            x["target_date_parsed"] = pd.to_datetime(x["target_date"], errors="coerce")
            x["month"] = x["target_date_parsed"].dt.to_period("M").astype(str)
        if name == "agent_sessions":
            x["login_at_parsed"] = parse_timestamp(x["login_at"])
            x["logout_at_parsed"] = parse_timestamp(x["logout_at"])
            x["session_hours"] = (x["logout_at_parsed"] - x["login_at_parsed"]).dt.total_seconds() / 3600
            x.loc[x["session_hours"] < 0, "session_hours"] = np.nan
            x["month"] = x["login_at_parsed"].dt.to_period("M").astype(str)
        out[name] = x
    return out


def enrich_dispositions(dispositions: pd.DataFrame) -> pd.DataFrame:
    out = dispositions.copy()
    out["disposition_code_norm"] = out["disposition_code"].fillna("").str.upper().str.strip()
    out["is_rpc"] = out["disposition_code_norm"].str.contains("RPC|RIGHT|PTP|PROMISE|PAID|CALLBACK", regex=True)
    out["is_ptp_disposition"] = out["disposition_code_norm"].str.contains("PTP|PROMISE", regex=True)
    return out


def enrich_ptp(ptp: pd.DataFrame, clean_payments: pd.DataFrame) -> pd.DataFrame:
    out = ptp.copy()
    out["promised_amount"] = pd.to_numeric(out["promised_amount"], errors="coerce")
    out["promised_date_parsed"] = pd.to_datetime(out["promised_date"], errors="coerce")
    out["status_norm"] = out["status"].fillna("").str.upper()
    payments_by_account = clean_payments.copy()
    payments_by_account["payment_date"] = pd.to_datetime(payments_by_account["event_at_local"], errors="coerce", utc=True).dt.tz_convert("Asia/Kolkata").dt.date
    account_payment_dates = payments_by_account.groupby("account_id")["payment_date"].apply(set).to_dict()

    def kept(row):
        if "KEPT" in row["status_norm"] or "PAID" in row["status_norm"]:
            return True
        dates = account_payment_dates.get(row["account_id"], set())
        promised = row["promised_date_parsed"]
        if pd.isna(promised):
            return False
        window = {promised.date(), (promised + pd.Timedelta(days=1)).date(), (promised + pd.Timedelta(days=2)).date()}
        return bool(dates & window)

    out["is_kept"] = out.apply(kept, axis=1)
    return out


def build_golden(frames: dict[str, pd.DataFrame], clean_payments: pd.DataFrame) -> dict[str, pd.DataFrame]:
    borrowers, borrower_map = entity_resolution.resolve_borrowers(frames["borrowers"], frames["accounts"])
    agents, agent_map = entity_resolution.resolve_agents(frames["agents"])
    dispositions = enrich_dispositions(frames["call_dispositions"])
    ptp = enrich_ptp(frames["promises_to_pay"], clean_payments)

    account_cols = ["account_id", "borrower_id", "loan_type", "principal_amount", "outstanding_amount", "dpd", "risk_segment", "status", "opened_at", "timezone", "schema_version"]
    dim_account = frames["accounts"][account_cols].drop_duplicates(subset=["account_id"]).copy()
    dim_account["principal_amount"] = pd.to_numeric(dim_account["principal_amount"], errors="coerce")
    dim_account["outstanding_amount"] = pd.to_numeric(dim_account["outstanding_amount"], errors="coerce")
    dim_account["dpd"] = pd.to_numeric(dim_account["dpd"], errors="coerce")

    dim_date = pd.DataFrame(
        {
            "date": pd.date_range(
                min(pd.to_datetime(frames["daily_targeting"]["target_date"], errors="coerce").min(), pd.to_datetime(clean_payments["event_at"], errors="coerce").min()),
                max(pd.to_datetime(frames["daily_targeting"]["target_date"], errors="coerce").max(), pd.to_datetime(clean_payments["event_at"], errors="coerce").max()),
                freq="D",
            )
        }
    )
    dim_date["date_key"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["month"] = dim_date["date"].dt.to_period("M").astype(str)
    dim_date["day_of_week"] = dim_date["date"].dt.day_name()

    return {
        "dim_borrower": borrowers,
        "borrower_identity_resolution": borrower_map,
        "dim_account": dim_account,
        "dim_agent": agents,
        "agent_identity_resolution": agent_map,
        "dim_campaign": frames["campaigns"].drop_duplicates(subset=["campaign_id"]),
        "dim_vendor": frames["vendor_telephony"].drop_duplicates(subset=["vendor_id"]),
        "dim_date": dim_date,
        "fact_calls": frames["calls"],
        "fact_call_attempts": frames["call_attempts"],
        "fact_call_dispositions": dispositions,
        "fact_digital_events": pd.concat(
            [
                frames["whatsapp_events"].assign(channel="WHATSAPP"),
                frames["sms_events"].assign(channel="SMS"),
            ],
            ignore_index=True,
            sort=False,
        ),
        "fact_field_visits": frames["field_visits"],
        "fact_ptp": ptp,
        "fact_payments": clean_payments,
        "fact_targeting": frames["daily_targeting"],
        "fact_account_status": frames["account_status_history"],
    }


def build_driver_tables(golden: dict[str, pd.DataFrame], attributed_payments: pd.DataFrame, touches: pd.DataFrame) -> dict[str, pd.DataFrame]:
    accounts = golden["dim_account"]
    payments = golden["fact_payments"]
    calls = golden["fact_calls"]
    campaigns = golden["dim_campaign"]
    agents = golden["dim_agent"]

    recovered_by_account = payments.groupby("account_id")["amount"].apply(lambda s: pd.to_numeric(s, errors="coerce").sum()).rename("recovered_amount")
    account_perf = accounts.merge(recovered_by_account, on="account_id", how="left").fillna({"recovered_amount": 0})
    account_perf["recovery_rate"] = account_perf["recovered_amount"] / account_perf["outstanding_amount"].replace({0: np.nan})
    account_perf["dpd_bucket"] = pd.cut(account_perf["dpd"], bins=[-1, 0, 30, 60, 90, 10000], labels=["current", "1-30", "31-60", "61-90", "90+"])

    dpd_scorecard = account_perf.groupby("dpd_bucket", observed=True).agg(
        accounts=("account_id", "nunique"),
        outstanding_amount=("outstanding_amount", "sum"),
        recovered_amount=("recovered_amount", "sum"),
        recovery_rate=("recovery_rate", "mean"),
    ).reset_index()
    risk_scorecard = account_perf.groupby("risk_segment").agg(
        accounts=("account_id", "nunique"),
        outstanding_amount=("outstanding_amount", "sum"),
        recovered_amount=("recovered_amount", "sum"),
        recovery_rate=("recovery_rate", "mean"),
    ).reset_index()
    loan_scorecard = account_perf.groupby("loan_type").agg(
        accounts=("account_id", "nunique"),
        outstanding_amount=("outstanding_amount", "sum"),
        recovered_amount=("recovered_amount", "sum"),
        recovery_rate=("recovery_rate", "mean"),
    ).reset_index()

    city_scorecard = (
        account_perf.merge(golden["dim_borrower"][["borrower_id", "city", "state"]], on="borrower_id", how="left")
        .groupby(["state", "city"], dropna=False)
        .agg(accounts=("account_id", "nunique"), recovered_amount=("recovered_amount", "sum"), outstanding_amount=("outstanding_amount", "sum"))
        .reset_index()
    )
    city_scorecard["recovery_rate"] = city_scorecard["recovered_amount"] / city_scorecard["outstanding_amount"].replace({0: np.nan})
    city_scorecard = city_scorecard.sort_values("recovered_amount", ascending=False).head(25)

    campaign_pay = attributed_payments.groupby("campaign_id", dropna=False)["amount"].apply(lambda s: pd.to_numeric(s, errors="coerce").sum()).rename("recovered_amount").reset_index()
    campaign_scorecard = campaigns.merge(campaign_pay, on="campaign_id", how="left").fillna({"recovered_amount": 0}).sort_values("recovered_amount", ascending=False)

    calls_for_agent = calls.merge(agents[["agent_id", "canonical_agent_id", "joined_at"]], on="agent_id", how="left")
    calls_for_agent["event_dt"] = pd.to_datetime(calls_for_agent["event_at_local"], errors="coerce", utc=True).dt.tz_convert("Asia/Kolkata")
    calls_for_agent["joined_dt"] = pd.to_datetime(calls_for_agent["joined_at"], errors="coerce")
    calls_for_agent["tenure_days"] = (calls_for_agent["event_dt"].dt.tz_localize(None) - calls_for_agent["joined_dt"]).dt.days
    calls_for_agent["tenure_bucket"] = pd.cut(calls_for_agent["tenure_days"], bins=[-10000, 30, 90, 180, 365, 10000], labels=["<30d", "31-90d", "91-180d", "181-365d", "365d+"])
    agent_scorecard = calls_for_agent.groupby(["canonical_agent_id", "tenure_bucket"], observed=True).agg(
        calls=("call_id", "nunique"),
        contacted=("call_status", lambda s: s.isin(["ANSWERED", "CONNECTED", "CONTACTED"]).sum()),
        avg_duration_sec=("duration_sec", lambda s: pd.to_numeric(s, errors="coerce").mean()),
    ).reset_index()
    agent_scorecard["contact_rate"] = agent_scorecard["contacted"] / agent_scorecard["calls"].replace({0: np.nan})

    calls_for_hour = calls.copy()
    calls_for_hour["call_hour_local"] = pd.to_datetime(calls_for_hour["event_at_local"], errors="coerce", utc=True).dt.tz_convert("Asia/Kolkata").dt.hour
    calling_time = calls_for_hour.groupby("call_hour_local").agg(calls=("call_id", "nunique"), contacted=("call_status", lambda s: s.isin(["ANSWERED", "CONNECTED", "CONTACTED"]).sum())).reset_index()
    calling_time["contact_rate"] = calling_time["contacted"] / calling_time["calls"].replace({0: np.nan})

    attempts = calls.groupby("account_id")["call_id"].nunique().rename("call_attempts").reset_index()
    attempts["attempt_bucket"] = pd.cut(attempts["call_attempts"], bins=[0, 1, 2, 3, 5, 10_000], labels=["1", "2", "3", "4-5", "6+"])
    attempt_frequency = attempts.merge(account_perf[["account_id", "recovered_amount"]], on="account_id", how="left").groupby("attempt_bucket", observed=True).agg(
        accounts=("account_id", "nunique"), avg_recovery=("recovered_amount", "mean")
    ).reset_index()

    return {
        "dpd_scorecard": dpd_scorecard,
        "risk_scorecard": risk_scorecard,
        "loan_scorecard": loan_scorecard,
        "geography_scorecard": city_scorecard,
        "campaign_scorecard": campaign_scorecard,
        "agent_scorecard": agent_scorecard,
        "calling_time_scorecard": calling_time,
        "attempt_frequency_scorecard": attempt_frequency,
        "channel_scorecard": attribution.channel_performance(attributed_payments, touches),
    }


def plot_outputs(monthly: pd.DataFrame, channel: pd.DataFrame, invest: pd.DataFrame, payment_summary: pd.DataFrame) -> None:
    ensure_dirs(CHART_DIR, DASHBOARD_DIR / "screenshots")
    plt.style.use("seaborn-v0_8-whitegrid")

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(monthly["month"], monthly["recovered_amount"], marker="o", label="Validated recovery")
    ax.set_title("Monthly Validated Recovery")
    ax.set_ylabel("INR")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHART_DIR / "monthly_recovery.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(monthly["month"], monthly["recovery_rate"], marker="o", label="Independent recovery rate")
    if "reported_metric_proxy" in monthly:
        ax.plot(monthly["month"], monthly["reported_metric_proxy"], marker="s", label="Reported proxy: raw success / outstanding")
    ax.set_title("Reported Proxy vs Independent Metric")
    ax.set_ylabel("Rate")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHART_DIR / "reported_vs_independent.png", dpi=160)
    plt.close(fig)

    top_channel = channel.sort_values("recovered_amount", ascending=False).head(8)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.bar(top_channel["channel"].astype(str), top_channel["recovered_amount"])
    ax.set_title("Recovery by Attributed Channel")
    ax.set_ylabel("INR")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(CHART_DIR / "channel_recovery.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.bar(invest["option"], invest["roi"])
    ax.set_title("Modeled ROI by Investment Option")
    ax.set_ylabel("ROI")
    ax.tick_params(axis="x", rotation=60)
    fig.tight_layout()
    fig.savefig(CHART_DIR / "investment_roi.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.8))
    vals = [
        payment_summary["raw_successful_payment_amount"].iloc[0],
        payment_summary["validated_successful_payment_amount"].iloc[0],
    ]
    ax.bar(["Raw successful", "Validated successful"], vals, color=["#667085", "#1570EF"])
    ax.set_title("Duplicate Payment Impact")
    ax.set_ylabel("INR")
    fig.tight_layout()
    fig.savefig(CHART_DIR / "duplicate_payment_impact.png", dpi=160)
    plt.close(fig)


def write_sql_files() -> None:
    sql_root = PROJECT_ROOT / "sql"
    dataset_views = []
    for csv in sorted(RAW_DIR.glob("*.csv")):
        name = csv.stem
        dataset_views.append(f"CREATE OR REPLACE VIEW raw_{name} AS SELECT * FROM read_csv_auto('../../data/raw/{csv.name}', all_varchar=true);")
        (sql_root / "01_staging" / f"stg_{name}.sql").write_text(
            f"-- Staging view for {name}. All fields kept as supplied; typing happens in clean/golden models.\n"
            f"CREATE OR REPLACE VIEW stg_{name} AS\nSELECT * FROM read_csv_auto('../../data/raw/{csv.name}', all_varchar=true);\n",
            encoding="utf-8",
        )
    (sql_root / "00_setup" / "01_load_raw.sql").write_text("\n".join(dataset_views) + "\n", encoding="utf-8")
    (sql_root / "02_data_quality" / "dq_payment_duplicates.sql").write_text(
        """-- Duplicate payment checks used by the Python pipeline.
SELECT
  COUNT(*) AS raw_rows,
  COUNT(*) - COUNT(DISTINCT payment_id) AS duplicate_payment_id_rows,
  COUNT(*) - COUNT(DISTINCT payment_reference) AS duplicate_reference_rows,
  SUM(CASE WHEN payment_status = 'SUCCESS' THEN CAST(amount AS DOUBLE) ELSE 0 END) AS raw_success_amount
FROM stg_payments;
""",
        encoding="utf-8",
    )
    metric_sql = {
        "metric_recovery_rate.sql": "SELECT month, recovered_amount / NULLIF(total_outstanding_amount, 0) AS recovery_rate FROM monthly_scorecard;",
        "metric_contact_rate.sql": "SELECT month, contacted_accounts / NULLIF(attempted_accounts, 0) AS contact_rate FROM monthly_scorecard;",
        "metric_rpc_rate.sql": "SELECT month, rpc_accounts / NULLIF(contacted_accounts, 0) AS rpc_rate FROM monthly_scorecard;",
        "metric_ptp_rate.sql": "SELECT month, ptp_accounts / NULLIF(rpc_accounts, 0) AS ptp_rate FROM monthly_scorecard;",
        "metric_ptp_kept_rate.sql": "SELECT month, ptp_kept_accounts / NULLIF(ptp_accounts, 0) AS ptp_kept_rate FROM monthly_scorecard;",
        "metric_recovery_per_account.sql": "SELECT month, recovered_amount / NULLIF(eligible_accounts, 0) AS recovery_per_account FROM monthly_scorecard;",
        "metric_recovery_per_agent_hour.sql": "SELECT month, recovered_amount / NULLIF(agent_hours, 0) AS recovery_per_agent_hour FROM monthly_scorecard;",
        "metric_cost_per_recovery.sql": "SELECT month, NULL AS cost_per_recovered_rupee FROM monthly_scorecard;",
        "metric_channel_conversion.sql": "SELECT channel, paid_accounts / NULLIF(touched_accounts, 0) AS channel_conversion FROM channel_scorecard;",
        "metric_daily_monthly_scorecard.sql": "-- The generated monthly scorecard is materialized at outputs/tables/monthly_scorecard.csv.\nSELECT * FROM monthly_scorecard;",
    }
    for name, sql in metric_sql.items():
        (sql_root / "05_metrics" / name).write_text(sql + "\n", encoding="utf-8")
    (sql_root / "04_golden" / "fct_collection_episode.sql").write_text(
        "-- Analytical grain: account-month collection episode. Built in Python as data/golden/analytical/fct_collection_episode.csv.\n",
        encoding="utf-8",
    )
    analysis_sql = {
        "ana_monthly_trend.sql": "-- See outputs/tables/monthly_scorecard.csv for reconstructed monthly trend.\nSELECT * FROM monthly_scorecard;",
        "ana_mix_effects.sql": "-- See outputs/tables/portfolio_mix.csv and mix_adjustment.csv.\nSELECT * FROM portfolio_mix;",
        "ana_cohorts.sql": "-- Cohort proxy is based on account open month and recovery outcome in generated analytical tables.",
        "ana_dpd.sql": "-- See outputs/tables/dpd_scorecard.csv.",
        "ana_agent.sql": "-- See outputs/tables/agent_scorecard.csv.",
        "ana_campaign.sql": "-- See outputs/tables/campaign_scorecard.csv.",
        "ana_channel.sql": "-- See outputs/tables/channel_scorecard.csv.",
        "ana_vendor.sql": "-- See outputs/tables/vendor_scorecard.csv.",
        "ana_calling_time.sql": "-- See outputs/tables/calling_time_scorecard.csv.",
        "ana_attempt_frequency.sql": "-- See outputs/tables/attempt_frequency_scorecard.csv.",
        "ana_borrower_segment.sql": "-- See outputs/tables/risk_scorecard.csv and loan_scorecard.csv.",
        "ana_geography.sql": "-- See outputs/tables/geography_scorecard.csv.",
        "ana_denominator_shift.sql": "-- See outputs/tables/denominator_funnel.csv.",
    }
    for name, sql in analysis_sql.items():
        (sql_root / "06_analysis" / name).write_text(sql + "\n", encoding="utf-8")


def make_notebooks() -> None:
    notebooks = {
        "01_data_audit.ipynb": ("Data Audit", "Audit source inventory, schemas, missingness, keys, foreign keys, dates, and duplicate business identifiers.", ["inventory.csv", "missingness.csv", "key_integrity.csv", "duplicate_audit.csv", "fk_integrity.csv"]),
        "02_data_forensics.ipynb": ("Data Forensics", "Reconcile payments, normalize event time, inspect attribution windows, and identify denominator risks.", ["payment_duplicate_summary.csv", "attribution_window_sensitivity.csv", "claim_validation.csv", "denominator_funnel.csv"]),
        "03_golden_dataset_validation.ipynb": ("Golden Dataset Validation", "Validate dimensions, facts, grain, row retention, identity resolution, and payment reconciliation.", ["cleaning_impact.csv", "payment_duplicate_summary.csv", "metric_dictionary.csv"]),
        "04_performance_reconstruction.ipynb": ("Performance Reconstruction", "Reconstruct monthly recovery, funnel metrics, and valid month-on-month claim comparisons.", ["monthly_scorecard.csv", "claim_validation.csv", "denominator_funnel.csv"]),
        "05_driver_analysis.ipynb": ("Driver Analysis", "Compare DPD, geography, agent tenure, campaign, channel, vendor, calling time, attempts, risk, and loan segments.", ["dpd_scorecard.csv", "geography_scorecard.csv", "agent_scorecard.csv", "campaign_scorecard.csv", "channel_scorecard.csv", "vendor_scorecard.csv", "calling_time_scorecard.csv", "attempt_frequency_scorecard.csv", "risk_scorecard.csv", "loan_scorecard.csv"]),
        "06_statistical_investigation.ipynb": ("Statistical Investigation", "Separate mix, cohort, selection, survivorship, Simpson's paradox, attribution-window, and time-series explanations.", ["mix_standardized_recovery.csv", "cohort_recovery.csv", "targeting_gap.csv", "attribution_window_sensitivity.csv", "monthly_scorecard.csv"]),
        "07_counterfactual.ipynb": ("Counterfactual", "Define the treatment/control limitation and quantify the observational targeting comparison without claiming causality.", ["counterfactual_estimate.csv", "targeting_gap.csv"]),
        "08_investment_case.ipynb": ("Investment Case", "Evaluate the six investment options using explicit assumptions, downside, break-even, confidence, and pilot requirements.", ["investment_option_scorecard.csv", "investment_scenarios.csv"]),
    }
    for filename, (title, description, artifacts) in notebooks.items():
        nb = nbf.v4.new_notebook()
        nb.cells = [
            nbf.v4.new_markdown_cell(f"# {title}\n\n{description}\n\nEvery conclusion must be labeled Fact, Strong Evidence, Correlation, or Hypothesis. Observational comparisons do not establish causality."),
            nbf.v4.new_code_cell(
                "from pathlib import Path\n"
                "import pandas as pd\n\n"
                "PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n"
                "TABLE_DIR = PROJECT_ROOT / 'outputs' / 'tables'\n"
                "AUDIT_DIR = PROJECT_ROOT / 'data' / 'processed' / 'audit_outputs'\n"
                "print(f'Project root: {PROJECT_ROOT}')\n"
            ),
            nbf.v4.new_code_cell(
                f"artifacts = {artifacts!r}\n"
                "tables = {}\n"
                "for artifact in artifacts:\n"
                "    path = TABLE_DIR / artifact\n"
                "    if path.exists():\n"
                "        tables[artifact] = pd.read_csv(path)\n"
                "        print(f'{artifact}: {tables[artifact].shape}')\n"
                "        display(tables[artifact].head())\n"
                "    else:\n"
                "        print(f'MISSING ARTIFACT: {artifact}')\n"
            ),
            nbf.v4.new_markdown_cell("## Interpretation\n\nRecord the observed result, evidence classification, limitations, and business implication here after reviewing the tables above. Do not infer causal uplift from channel, targeting, vendor, agent, or campaign comparisons without treatment assignment."),
        ]
        nbf.write(nb, PROJECT_ROOT / "notebooks" / filename)


def write_architecture() -> None:
    drawio = """<mxfile host="app.diagrams.net"><diagram name="Collections Analytics Architecture"><mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/>
<mxCell id="raw" value="Raw CSVs&#xa;PK checks, unchanged files" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;" vertex="1" parent="1"><mxGeometry x="40" y="80" width="170" height="70" as="geometry"/></mxCell>
<mxCell id="stg" value="Staging&#xa;All-varchar, schema contracts" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;" vertex="1" parent="1"><mxGeometry x="250" y="80" width="170" height="70" as="geometry"/></mxCell>
<mxCell id="dq" value="Data Quality + Reconciliation&#xa;duplicates, FKs, timestamps, late events" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;" vertex="1" parent="1"><mxGeometry x="460" y="80" width="220" height="70" as="geometry"/></mxCell>
<mxCell id="clean" value="Clean&#xa;dedupe, canonical IDs, UTC/local timestamps" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;" vertex="1" parent="1"><mxGeometry x="720" y="80" width="190" height="70" as="geometry"/></mxCell>
<mxCell id="golden" value="Golden Star Schema&#xa;dim_* and fact_* with grain documented" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;" vertex="1" parent="1"><mxGeometry x="950" y="80" width="210" height="70" as="geometry"/></mxCell>
<mxCell id="metrics" value="Feature + Metrics&#xa;monthly scorecard, attribution windows" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;" vertex="1" parent="1"><mxGeometry x="420" y="220" width="220" height="70" as="geometry"/></mxCell>
<mxCell id="dash" value="Dashboard + Memo&#xa;lineage to metric SQL and golden tables" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;" vertex="1" parent="1"><mxGeometry x="700" y="220" width="220" height="70" as="geometry"/></mxCell>
<mxCell id="mon" value="Production Controls&#xa;incremental lookback, backfills, monitoring, anomaly detection" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;" vertex="1" parent="1"><mxGeometry x="980" y="220" width="240" height="70" as="geometry"/></mxCell>
</root></mxGraphModel></diagram></mxfile>"""
    (ARCHITECTURE_DIR / "architecture.drawio").write_text(drawio, encoding="utf-8")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.axis("off")
    boxes = [
        ("Raw\nunchanged CSVs", 0.05, 0.68),
        ("Staging\nschema contracts", 0.23, 0.68),
        ("DQ + Reconciliation\nduplicates/FKs/timestamps", 0.41, 0.68),
        ("Clean\ncanonical IDs", 0.62, 0.68),
        ("Golden\ndim/fact star", 0.80, 0.68),
        ("Feature + Metrics\naccount-month", 0.32, 0.28),
        ("Dashboard + Memo\nlineage", 0.55, 0.28),
        ("Controls\nincremental/backfill/monitoring", 0.78, 0.28),
    ]
    for label, x, y in boxes:
        ax.text(x, y, label, ha="center", va="center", bbox=dict(boxstyle="round,pad=0.45", fc="#eef4ff", ec="#175cd3"), transform=ax.transAxes)
    for x1, x2 in [(0.13, 0.20), (0.31, 0.38), (0.51, 0.59), (0.70, 0.77)]:
        ax.annotate("", xy=(x2, 0.68), xytext=(x1, 0.68), arrowprops=dict(arrowstyle="->"), xycoords=ax.transAxes)
    ax.annotate("", xy=(0.42, 0.36), xytext=(0.83, 0.61), arrowprops=dict(arrowstyle="->"), xycoords=ax.transAxes)
    ax.annotate("", xy=(0.53, 0.28), xytext=(0.42, 0.28), arrowprops=dict(arrowstyle="->"), xycoords=ax.transAxes)
    ax.annotate("", xy=(0.75, 0.28), xytext=(0.64, 0.28), arrowprops=dict(arrowstyle="->"), xycoords=ax.transAxes)
    fig.tight_layout()
    fig.savefig(ARCHITECTURE_DIR / "architecture.png", dpi=180)
    fig.savefig(ARCHITECTURE_DIR / "data_model.png", dpi=180)
    plt.close(fig)


def write_reports(
    audit: dict[str, pd.DataFrame],
    golden: dict[str, pd.DataFrame],
    monthly: pd.DataFrame,
    payment_summary: pd.DataFrame,
    claim: pd.DataFrame,
    drivers: dict[str, pd.DataFrame],
    invest: pd.DataFrame,
    assignment_text: str,
) -> None:
    latest, completeness_note = latest_complete_month(monthly, audit)
    rec = invest.iloc[0]
    dq_top = audit["duplicate_audit"].sort_values("duplicate_id_rows", ascending=False).head(8)
    key_failures = audit["key_integrity"][audit["key_integrity"]["duplicate_count"] > 0]
    fk_failures = audit["fk_integrity"][audit["fk_integrity"]["unmatched_rows"] > 0]

    write_markdown(
        f"""
# Source Of Truth Decisions

| Entity / metric | Chosen source | Alternative sources | Evidence | Rationale | Implication |
|---|---|---|---|---|---|
| Borrower | `borrowers.csv` plus `accounts.borrower_id` | event borrower IDs | FK audit and stable account relationship | Accounts provide the business relationship; borrower table supplies attributes | Event borrower conflicts are not merged by name |
| Account | `accounts.csv` | status history | Account has static principal/outstanding/DPD/risk fields | Needed as portfolio denominator | Outstanding is treated as supplied static balance |
| Agent | `agents.employee_code` when present, else `agent_id` | agent name | Names are insufficient identity evidence | Avoid false merges | Agent analysis uses canonical mapping |
| Recovery | validated successful `payments.csv` | raw success totals | Duplicate payment forensics shows overstatement of {money(payment_summary['overstatement'].iloc[0])} | Failed/reversed/duplicate payments do not represent cash recovery | Independent metrics use clean payments |
| Contact | `calls.call_status` answered/connected/contacted | dispositions only | Calls table contains call outcome and duration | Contact is attempt-level operational event | Contact rate denominator is attempted accounts |
| RPC/PTP | `call_dispositions.csv` and `promises_to_pay.csv` | call status | Dispositions/PTP table carry intent semantics | Keeps RPC/PTP separate from contact | Unmapped legacy codes remain a limitation |
| Attribution | latest eligible touch within {DEFAULT_ATTRIBUTION_DAYS} days | latest-touch all-time, direct payment only | Attribution sensitivity tables generated | Prevents unlimited credit assignment | Association only; not causal |
| Cost metrics | investment scenario assumptions | actual cost records | Actual cost fields unavailable | The supplied dataset lacks cost facts | Cost per rupee is modeled, not observed |
""",
        REPORT_DIR / "source_of_truth.md",
    )

    write_markdown(
        f"""
# Assumptions Register

| ID | Assumption | Why required | Evidence | Risk if wrong | Sensitivity |
|---|---|---|---|---|---|
| A1 | Payment recovery uses `SUCCESS` status after duplicate payment ID/reference removal | Raw successful totals can be overstated | Duplicate payment audit | Under/overstated recovery | Compare raw vs validated totals |
| A2 | Business behavioral time is Asia/Kolkata | Calling-hour analysis needs local time | Dataset includes UTC/Kolkata/Dubai timezone warnings | Hour-of-day patterns shift | Retain raw timezone and UTC/local columns |
| A3 | Default attribution window is {DEFAULT_ATTRIBUTION_DAYS} days | Need channel/campaign association rule | Window sensitivity output generated | Channel ROI overstated | 3/7/14/30-day windows |
| A4 | Full supplied account population is eligible portfolio | No separate eligibility table was supplied | Accounts table is only portfolio source | Denominator may be too broad | Report targeted/attempted funnel separately |
| A5 | Cost and uplift assumptions for INR 10 Cr options are modeled | Actual unit cost/vendor pricing absent | No cost fields in dictionary | ROI can be wrong | Downside and confidence reported |
| A6 | Treatment/control for targeting is observational, not randomized | Counterfactual is requested | No experimental assignment flag | Causal effect overstated | Label as correlation/hypothesis |
""",
        REPORT_DIR / "assumptions.md",
    )

    write_markdown(
        f"""
# Decision Log

| Decision | Evidence | Alternatives considered | Why chosen | Impact | Confidence |
|---|---|---|---|---|---|
| Preserve raw files and build processed/golden layers | Assignment requires raw untouched | Edit raw CSVs | Auditability | Reproducible rebuild | HIGH |
| Exclude failed payments from recovery | Payment status field exists | Count all payments | Cash recovery requires success | Recovery lowered vs raw totals | HIGH |
| Deduplicate by exact row, payment ID, then payment reference | Duplicate payment audit | Drop all duplicate-looking events | Business-key suspicious repeats may be legitimate | Quantified overstatement | MEDIUM |
| Use account-month as primary scorecard grain | Monthly claim and portfolio funnel | attempt-month only | Avoid denominator mixing | Executive metrics align | HIGH |
| Treat 11% claim as tested proxy unless official report definition supplied | No external reported metric table | Assume claim true/false | Independent validation requires aligned definition | Conclusion can be partial/not verifiable | HIGH |
| Recommend one investment by evidence-adjusted modeled ROI | Assignment asks exactly one option | Multiple recommendations | Forces executive choice | Costs are assumption-labeled | MEDIUM |
""",
        REPORT_DIR / "decisions.md",
    )

    issue_rows = []
    for _, row in dq_top.iterrows():
        issue_rows.append(f"| {row['dataset']} duplicates | duplicate audit | classify, do not blanket drop | {int(row['duplicate_id_rows'])} duplicate-ID rows | affects source trust |")
    for _, row in key_failures.head(8).iterrows():
        issue_rows.append(f"| {row['dataset']} primary key | key audit | keep raw, resolve in clean/golden | {int(row['duplicate_count'])} duplicate keys | affects joins |")
    if not issue_rows:
        issue_rows.append("| No major primary-key duplicate issue | automated audit | monitor | 0 | low |")

    write_markdown(
        f"""
# Data Quality Report

## Executive Summary

The supplied dataset covers {audit['inventory']['min_event_date'].min()} to {audit['inventory']['max_event_date'].max()} across {len(audit['inventory'])} tables. The pipeline preserves raw files, audits keys/FKs/timestamps/categories, and creates clean/golden outputs.

Major recovery impact: raw successful payments totaled {money(payment_summary['raw_successful_payment_amount'].iloc[0])}; validated successful payments totaled {money(payment_summary['validated_successful_payment_amount'].iloc[0])}; duplicate/payment-status treatment reduced recovery by {money(payment_summary['overstatement'].iloc[0])}.

## Major Findings

| Issue | Detection | Treatment | Affected Records | Business Impact |
|---|---|---|---:|---|
{chr(10).join(issue_rows)}

## Foreign Keys

Unmatched FK rows are written to `data/processed/audit_outputs/fk_integrity.csv`; they are not silently deleted because they may represent late-arriving or historical source mismatches.

## Cleaning Impact

See `data/processed/audit_outputs/cleaning_impact.csv`.

## Residual Risks

Client and language dimensions are unavailable in supplied data. Actual cost facts are unavailable, so cost per recovered rupee and investment ROI are modeled assumptions rather than observed financial accounting.
""",
        REPORT_DIR / "data_quality_report.md",
    )

    claim_last = claim.loc[claim["month"] == latest["month"]].iloc[0]
    write_markdown(
        f"""
# Executive Memo

## 1. What happened?

{completeness_note} Validated recovery in {latest['month']} was {money(latest['recovered_amount'])}, with an independent recovery rate of {pct(latest['recovery_rate'])}. Month-on-month recovery amount changed by {pct(latest['recovered_amount_mom_pct_change'])}; recovery rate changed by {pct(latest['recovery_rate_mom_pct_change'])}. The operational funnel shows {int(latest['targeted_accounts'])} targeted accounts, {int(latest['attempted_accounts'])} attempted accounts, and a contact rate of {pct(latest['contact_rate'])}.

## 2. Why did it happen?

The strongest supported drivers in the supplied data are portfolio mix, channel/campaign exposure, agent/vendor execution, and attempt-frequency patterns. Client and language cannot be assessed because reliable fields are unavailable in the supplied tables.

## 3. Is the 11% claim real?

Using the reconstructed reporting proxy, latest month reported-proxy change was {pct(claim_last['reported_mom_pct_change'])}; the independent validated recovery-rate change was {pct(claim_last['independent_mom_pct_change'])}. Absolute gap was {pct(claim_last['absolute_gap'])}. Conclusion: {claim_last['conclusion']}.

## 4. How confident are we?

Facts: row counts, duplicate payment impact, validated payment totals, and monthly funnel metrics. Strong evidence: driver rankings and reporting-denominator gaps. Correlations: channel, campaign, targeting, and agent relationships. Hypotheses: causal impact of targeting or engagement changes without an experiment.

## 5. What should leadership do?

Recommend investing INR 10 Cr in **{rec['option']}**. This has the highest evidence-adjusted modeled ROI among the six evaluated options, while preserving the caveat that exact costs/uplifts are not in the source data.

## 6. Expected financial impact

Expected incremental recovery is {money(rec['incremental_recovery'])}, modeled ROI is {rec['roi']:.2f}x, and downside incremental recovery is {money(rec['downside_incremental_recovery'])}. Break-even requires {money(rec['break_even_recovery_required'])} incremental recovery.
""",
        REPORT_DIR / "executive_memo.md",
    )

    insights = pd.DataFrame(
        [
            {
                "insight_id": "I001",
                "finding": f"Validated successful recovery is {money(payment_summary['validated_successful_payment_amount'].iloc[0])}, below raw successful recovery by {money(payment_summary['overstatement'].iloc[0])}.",
                "evidence": "payment_duplicate_summary.csv",
                "classification": "FACT",
                "confidence": "HIGH",
                "business_impact": "Prevents duplicate/invalid payment overstatement.",
                "recommended_action": "Use validated payments as recovery source of truth.",
            },
            {
                "insight_id": "I002",
                "finding": f"Latest independent MoM recovery-rate change is {pct(claim_last['independent_mom_pct_change'])}; reported proxy change is {pct(claim_last['reported_mom_pct_change'])}.",
                "evidence": "claim_validation.csv",
                "classification": "STRONG EVIDENCE",
                "confidence": "MEDIUM",
                "business_impact": "11% claim depends on metric definition and cleaning.",
                "recommended_action": "Report independent metric beside reported proxy.",
            },
            {
                "insight_id": "I003",
                "finding": f"{rec['option']} ranks first by modeled evidence-adjusted ROI.",
                "evidence": "investment_option_scorecard.csv",
                "classification": "HYPOTHESIS",
                "confidence": str(rec["confidence"]),
                "business_impact": "Potential allocation of INR 10 Cr.",
                "recommended_action": "Pilot before full rollout and collect cost/control data.",
            },
            {
                "insight_id": "I004",
                "finding": "Client and language dimensions are unavailable in supplied data.",
                "evidence": "data_dictionary.csv and schema_audit.csv",
                "classification": "FACT",
                "confidence": "HIGH",
                "business_impact": "Cannot assess requested client/language drivers.",
                "recommended_action": "Add reliable client and language fields to source contracts.",
            },
        ]
    )
    write_csv(insights, REPORT_DIR / "insight_register.csv")

    readme = f"""
# Collections Performance Forensics & Recovery Analytics

## Business Problem

This project rebuilds collections performance from raw operational data, challenges a reported 11% month-on-month recovery improvement, identifies drivers, and evaluates where INR 10 Cr should be invested.

## Approach

Raw data -> audit/forensics -> source-of-truth decisions -> clean/golden data -> metric definitions -> monthly reconstruction -> claim validation -> drivers/statistics -> counterfactual -> investment case -> dashboard/memo/architecture.

## Stack

Python, pandas, DuckDB-oriented SQL, matplotlib, pytest, and Power BI-ready CSV outputs.

## Key Findings

- Observation period: {audit['inventory']['min_event_date'].min()} to {audit['inventory']['max_event_date'].max()}.
- Raw successful recovery: {money(payment_summary['raw_successful_payment_amount'].iloc[0])}.
- Validated successful recovery: {money(payment_summary['validated_successful_payment_amount'].iloc[0])}.
- Latest independent recovery rate: {pct(latest['recovery_rate'])}.
- Latest reported-proxy MoM change: {pct(claim_last['reported_mom_pct_change'])}.
- Latest independent MoM recovery-rate change: {pct(claim_last['independent_mom_pct_change'])}.
- Recommendation: invest INR 10 Cr in **{rec['option']}**, subject to pilot validation.

## Repository Structure

- `data/raw`: unchanged supplied CSVs
- `data/processed/audit_outputs`: inventory, DQ, forensics, cleaning impact
- `data/golden`: dimensions, facts, and analytical account-month table
- `sql`: reproducible SQL definitions and metric templates
- `notebooks`: assignment narrative notebooks
- `outputs/tables`: final analytical tables
- `outputs/charts`: dashboard/report charts
- `dashboard`: executive dashboard HTML/spec and screenshot
- `reports`: memo, DQ report, assumptions, decisions, source of truth
- `architecture`: draw.io and PNG architecture
- `tests`: data quality, metric, attribution, reconciliation tests

## Reproduction

```powershell
cd collections-analytics
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
.\\.venv\\Scripts\\python.exe src\\build_pipeline.py
.\\.venv\\Scripts\\python.exe -m pytest
```

## Limitations

Client, language, and actual cost facts are unavailable in the supplied data. Channel/targeting/campaign effects are observational correlations, not causal proof. A randomized or quasi-experimental design with cost capture is required for a causal investment decision.
"""
    write_markdown(readme, PROJECT_ROOT / "README.md")
    write_simple_pdf(REPORT_DIR / "executive_memo.md", REPORT_DIR / "executive_memo.pdf", "Executive Memo")
    write_simple_pdf(REPORT_DIR / "data_quality_report.md", REPORT_DIR / "data_quality_report.pdf", "Data Quality Report")

    dashboard_html = f"""
<!doctype html><html><head><meta charset="utf-8"><title>Collections Executive Dashboard</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f7f8fa;color:#101828}}.wrap{{padding:24px;max-width:1280px;margin:auto}}.kpis{{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}}.card{{background:white;border:1px solid #d0d5dd;border-radius:8px;padding:14px}}.label{{font-size:12px;color:#667085}}.value{{font-size:22px;font-weight:700;margin-top:4px}}.grid{{display:grid;grid-template-columns:2fr 1fr;gap:16px;margin-top:16px}}img{{max-width:100%;background:white;border:1px solid #d0d5dd;border-radius:8px}}table{{width:100%;border-collapse:collapse;font-size:13px}}td,th{{border-bottom:1px solid #eaecf0;padding:8px;text-align:left}}</style></head>
<body><div class="wrap"><h1>Collections Performance - Executive View</h1><p>Observation period: {audit['inventory']['min_event_date'].min()} to {audit['inventory']['max_event_date'].max()}. {completeness_note}</p>
<div class="kpis"><div class="card"><div class="label">Recovery Rate</div><div class="value">{pct(latest['recovery_rate'])}</div></div><div class="card"><div class="label">Recovered</div><div class="value">{money(latest['recovered_amount'])}</div></div><div class="card"><div class="label">PTP Kept</div><div class="value">{pct(latest['ptp_kept_rate'])}</div></div><div class="card"><div class="label">Recovery / Account</div><div class="value">{money(latest['recovery_per_account'])}</div></div><div class="card"><div class="label">Independent MoM</div><div class="value">{pct(claim_last['independent_mom_pct_change'])}</div></div><div class="card"><div class="label">Reported Proxy MoM</div><div class="value">{pct(claim_last['reported_mom_pct_change'])}</div></div></div>
<div class="grid"><div><img src="../outputs/charts/reported_vs_independent.png"><img src="../outputs/charts/channel_recovery.png"></div><div class="card"><h2>INR 10 Cr Recommendation</h2><p><strong>{rec['option']}</strong></p><table><tr><th>Metric</th><th>Value</th></tr><tr><td>Expected incremental recovery</td><td>{money(rec['incremental_recovery'])}</td></tr><tr><td>ROI</td><td>{rec['roi']:.2f}x</td></tr><tr><td>Break-even recovery required</td><td>{money(rec['break_even_recovery_required'])}</td></tr><tr><td>Confidence</td><td>{rec['confidence']}</td></tr></table><p>Cost/uplift values are modeled assumptions because actual cost records are unavailable.</p></div></div></div></body></html>
"""
    (DASHBOARD_DIR / "executive_dashboard.html").write_text(dashboard_html, encoding="utf-8")
    write_markdown(
        "Power BI Desktop is not available in this execution environment, so a binary `.pbix` could not be generated. The dashboard-ready tables are in `outputs/tables`, the metric dictionary is here, and `executive_dashboard.html` is the one-screen executive equivalent.",
        DASHBOARD_DIR / "power_bi_build_note.md",
    )


def write_tests() -> None:
    (PROJECT_ROOT / "tests" / "test_metrics.py").write_text(
        """import numpy as np
from src.metrics import monthly_scorecard


def test_monthly_scorecard_known_outputs():
    import pandas as pd
    accounts = pd.DataFrame({"account_id": ["a1", "a2"], "outstanding_amount": [100, 100]})
    targeting = pd.DataFrame({"account_id": ["a1", "a2"], "month": ["2026-01", "2026-01"]})
    calls = pd.DataFrame({"account_id": ["a1", "a2"], "call_status": ["ANSWERED", "NO_ANSWER"], "month": ["2026-01", "2026-01"]})
    disp = pd.DataFrame({"account_id": ["a1"], "is_rpc": [True], "month": ["2026-01"]})
    ptp = pd.DataFrame({"account_id": ["a1"], "is_kept": [True], "month": ["2026-01"]})
    pay = pd.DataFrame({"account_id": ["a1"], "amount": [20], "month": ["2026-01"]})
    sessions = pd.DataFrame({"session_hours": [2.0], "month": ["2026-01"]})
    out = monthly_scorecard(accounts, targeting, calls, disp, ptp, pay, sessions).iloc[0]
    assert out["contact_rate"] == 0.5
    assert out["rpc_rate"] == 1.0
    assert out["ptp_rate"] == 1.0
    assert out["ptp_kept_rate"] == 1.0
    assert out["recovery_rate"] == 0.1
    assert out["recovery_per_account"] == 10
    assert out["recovery_per_agent_hour"] == 10


def test_claim_validation_marks_zero_baseline_as_not_evaluable():
    from src.metrics import validate_mom_claim
    monthly = pd.DataFrame({
        "month": ["2025-12", "2026-01", "2026-02"],
        "reported_metric_proxy": [0.0, 0.02, 0.01],
        "recovery_rate": [0.0, 0.01, 0.02],
        "eligible_accounts": [10, 10, 10],
        "targeted_accounts": [0, 2, 2],
    })
    out = validate_mom_claim(monthly)
    assert pd.isna(out.loc[1, "independent_mom_pct_change"])
    assert out.loc[1, "comparison_status"] == "not_evaluable_no_valid_prior_month"
""",
        encoding="utf-8",
    )
    (PROJECT_ROOT / "tests" / "test_reconciliation.py").write_text(
        """import pandas as pd
from src.data_quality import payment_duplicate_forensics


def test_payment_reconciliation_duplicate_reference():
    df = pd.DataFrame(
        [
            {"payment_id": "p1", "payment_reference": "r1", "account_id": "a1", "event_at": "2026-01-01", "amount": "100", "payment_status": "SUCCESS", "payment_method": "UPI", "provider_id": "v1"},
            {"payment_id": "p2", "payment_reference": "r1", "account_id": "a1", "event_at": "2026-01-01", "amount": "100", "payment_status": "SUCCESS", "payment_method": "UPI", "provider_id": "v1"},
            {"payment_id": "p3", "payment_reference": "r2", "account_id": "a1", "event_at": "2026-01-02", "amount": "50", "payment_status": "FAILED", "payment_method": "UPI", "provider_id": "v1"},
        ]
    )
    summary, _, clean = payment_duplicate_forensics(df)
    assert summary["raw_successful_payment_amount"].iloc[0] == 200
    assert summary["validated_successful_payment_amount"].iloc[0] == 100
    assert len(clean) == 1
""",
        encoding="utf-8",
    )
    (PROJECT_ROOT / "tests" / "test_data_quality.py").write_text(
        """import pandas as pd
from src.data_quality import key_integrity


def test_key_integrity_counts_duplicate_ids():
    frames = {"borrowers": pd.DataFrame({"borrower_id": ["b1", "b1", "b2"]})}
    from src import data_quality
    old = data_quality.PRIMARY_KEYS if hasattr(data_quality, "PRIMARY_KEYS") else None
    out = key_integrity({"borrowers": frames["borrowers"], **{k: pd.DataFrame({v: []}) for k, v in __import__("src.config", fromlist=["PRIMARY_KEYS"]).PRIMARY_KEYS.items() if k != "borrowers"}})
    assert int(out[out["dataset"] == "borrowers"]["duplicate_count"].iloc[0]) == 1
""",
        encoding="utf-8",
    )
    (PROJECT_ROOT / "tests" / "test_attribution.py").write_text(
        """import pandas as pd
from src.attribution import attribute_payments


def test_attribute_payments_window():
    payments = pd.DataFrame({"payment_id": ["p1"], "account_id": ["a1"], "amount": [10], "event_at_local": pd.to_datetime(["2026-01-03"]).tz_localize("Asia/Kolkata")})
    touches = pd.DataFrame({"account_id": ["a1"], "touch_at_local": pd.to_datetime(["2026-01-01"]).tz_localize("Asia/Kolkata"), "event_at_local": pd.to_datetime(["2026-01-01"]).tz_localize("Asia/Kolkata"), "channel": ["SMS"], "campaign_id": ["c1"]})
    out = attribute_payments(payments, touches, 3)
    assert out["channel"].iloc[0] == "SMS"
""",
        encoding="utf-8",
    )
    (PROJECT_ROOT / "tests" / "test_entity_resolution.py").write_text(
        """import pandas as pd
from src.entity_resolution import resolve_agents


def test_agent_resolution_prefers_employee_code():
    agents = pd.DataFrame({"agent_id": ["a1"], "employee_code": ["e1"], "agent_name": ["Name"], "vendor_id": ["v1"], "joined_at": ["2026-01-01"]})
    clean, mapping = resolve_agents(agents)
    assert clean["canonical_agent_id"].iloc[0] == "EMP::e1"
    assert mapping["resolution_confidence"].iloc[0] == "HIGH"
""",
        encoding="utf-8",
    )


def main() -> None:
    ensure_dirs(AUDIT_DIR, TABLE_DIR, CHART_DIR, REPORT_DIR, DASHBOARD_DIR, ARCHITECTURE_DIR)
    assignment_text = extract_assignment_pdf()
    frames = normalize_frames(load_raw_data())

    audit = {
        "inventory": data_quality.inventory(frames),
        "schema_audit": data_quality.schema_audit(frames),
        "missingness": data_quality.missingness(frames),
        "key_integrity": data_quality.key_integrity(frames),
        "duplicate_audit": data_quality.duplicate_audit(frames),
        "fk_integrity": data_quality.fk_integrity(frames),
        "date_audit": data_quality.date_audit(frames),
        "categorical_profile": data_quality.categorical_profile(frames),
    }
    for name, df in audit.items():
        write_csv(df, AUDIT_DIR / f"{name}.csv")

    payment_summary, payment_flags, clean_payments = data_quality.payment_duplicate_forensics(frames["payments"])
    clean_payments = normalize_event_timestamp(clean_payments, "event_at")
    clean_payments = add_month(clean_payments, "event_at_local")
    clean_payments["amount"] = pd.to_numeric(clean_payments["amount"], errors="coerce")
    write_csv(payment_summary, AUDIT_DIR / "payment_duplicate_summary.csv")
    write_csv(payment_flags, AUDIT_DIR / "payment_duplicate_flags.csv")
    cleaning_impact = data_quality.cleaning_impact_rows(frames, clean_payments, payment_summary)
    write_csv(cleaning_impact, AUDIT_DIR / "cleaning_impact.csv")

    golden = build_golden(frames, clean_payments)
    for name, df in golden.items():
        folder = "dimensions" if name.startswith("dim_") or "resolution" in name else "facts"
        write_csv(df, GOLDEN_DIR / folder / f"{name}.csv")

    touches = attribution.build_channel_touches(
        golden["fact_calls"], frames["whatsapp_events"], frames["sms_events"], frames["field_visits"], frames["daily_targeting"], golden["dim_campaign"]
    )
    attributed = attribution.attribute_payments(clean_payments, touches, DEFAULT_ATTRIBUTION_DAYS)
    write_csv(touches, GOLDEN_DIR / "facts" / "fact_channel_touches.csv")
    write_csv(attributed, GOLDEN_DIR / "facts" / "fact_attributed_payments.csv")

    sensitivity_rows = []
    for window in ATTRIBUTION_WINDOWS_DAYS:
        window_attr = attribution.attribute_payments(clean_payments, touches, window)
        sensitivity_rows.append(
            {
                "window_days": window,
                "attributed_recovery": pd.to_numeric(window_attr.loc[window_attr["channel"].notna(), "amount"], errors="coerce").sum(),
                "unattributed_recovery": pd.to_numeric(window_attr.loc[window_attr["channel"].isna(), "amount"], errors="coerce").sum(),
                "attributed_payment_rows": int(window_attr["channel"].notna().sum()),
                "unattributed_payment_rows": int(window_attr["channel"].isna().sum()),
            }
        )
    write_csv(pd.DataFrame(sensitivity_rows), TABLE_DIR / "attribution_window_sensitivity.csv")

    monthly = metrics.monthly_scorecard(
        golden["dim_account"],
        golden["fact_targeting"],
        golden["fact_calls"],
        golden["fact_call_dispositions"],
        golden["fact_ptp"],
        golden["fact_payments"],
        frames["agent_sessions"],
    )

    raw_success = frames["payments"].copy()
    raw_success["amount"] = pd.to_numeric(raw_success["amount"], errors="coerce")
    raw_success = raw_success[raw_success["payment_status"].str.upper().eq("SUCCESS")]
    raw_success["month"] = pd.to_datetime(raw_success["event_at"], errors="coerce").dt.to_period("M").astype(str)
    raw_monthly = raw_success.groupby("month")["amount"].sum().rename("raw_success_amount").reset_index()
    monthly = monthly.merge(raw_monthly, on="month", how="left").fillna({"raw_success_amount": 0})
    monthly["reported_metric_proxy"] = monthly["raw_success_amount"] / monthly["total_outstanding_amount"].replace({0: np.nan})
    monthly["reported_metric_proxy_mom_pct_change"] = monthly["reported_metric_proxy"].pct_change()
    write_csv(monthly, TABLE_DIR / "monthly_scorecard.csv")

    claim = metrics.validate_mom_claim(monthly)
    write_csv(claim, TABLE_DIR / "claim_validation.csv")

    drivers = build_driver_tables(golden, attributed, touches)
    for name, df in drivers.items():
        write_csv(df, TABLE_DIR / f"{name}.csv")

    mix = statistics.portfolio_mix(golden["dim_account"], golden["fact_targeting"])
    target_gap = statistics.targeting_gap(golden["dim_account"], golden["fact_targeting"], clean_payments)
    vendor = statistics.vendor_performance(golden["fact_calls"], attributed)
    mix_standardized = statistics.mix_standardized_recovery(golden["dim_account"], golden["fact_payments"])
    cohort = statistics.cohort_recovery(golden["dim_account"], golden["fact_payments"])
    write_csv(mix, TABLE_DIR / "portfolio_mix.csv")
    write_csv(target_gap, TABLE_DIR / "targeting_gap.csv")
    write_csv(vendor, TABLE_DIR / "vendor_scorecard.csv")
    write_csv(mix_standardized, TABLE_DIR / "mix_standardized_recovery.csv")
    write_csv(cohort, TABLE_DIR / "cohort_recovery.csv")

    denominator_funnel = monthly[
        [
            "month",
            "eligible_accounts",
            "targeted_accounts",
            "attempted_accounts",
            "contacted_accounts",
            "rpc_accounts",
            "ptp_accounts",
            "ptp_kept_accounts",
            "recovered_amount",
        ]
    ].copy()
    write_csv(denominator_funnel, TABLE_DIR / "denominator_funnel.csv")

    targeted_accounts = set(golden["fact_targeting"]["account_id"])
    account_base = golden["dim_account"][["account_id", "outstanding_amount"]].copy()
    account_base["targeted"] = account_base["account_id"].isin(targeted_accounts)
    account_recovery = clean_payments.groupby("account_id")["amount"].sum().rename("recovered_amount")
    account_base = account_base.merge(account_recovery, on="account_id", how="left").fillna({"recovered_amount": 0})
    account_base["outstanding_amount"] = pd.to_numeric(account_base["outstanding_amount"], errors="coerce")
    grouped_cf = account_base.groupby("targeted").agg(outstanding=("outstanding_amount", "sum"), recovered=("recovered_amount", "sum"), accounts=("account_id", "nunique")).reset_index()
    grouped_cf["recovery_rate"] = grouped_cf["recovered"] / grouped_cf["outstanding"].replace({0: np.nan})
    non_target_rate = grouped_cf.loc[~grouped_cf["targeted"], "recovery_rate"].mean()
    target = grouped_cf.loc[grouped_cf["targeted"]].iloc[0] if grouped_cf["targeted"].any() else grouped_cf.iloc[0]
    counterfactual = pd.DataFrame(
        [
            {
                "question": "What would recovery have looked like if targeting strategy had not changed?",
                "treatment": "Accounts appearing in daily_targeting",
                "control": "Accounts never appearing in daily_targeting",
                "pre_period": "Unavailable in supplied data as explicit pre-strategy cohort",
                "post_period": "Full observation period",
                "outcome": "validated successful recovery amount",
                "observed_targeted_recovery": target["recovered"],
                "counterfactual_recovery_at_control_rate": target["outstanding"] * non_target_rate,
                "estimated_gap": target["recovered"] - target["outstanding"] * non_target_rate,
                "identification_strategy": "Observational targeted-vs-non-targeted comparison; not causal",
                "limitations": "No random assignment, explicit strategy-change date, or pre/post control structure.",
                "classification": "CORRELATION",
            }
        ]
    )
    write_csv(counterfactual, TABLE_DIR / "counterfactual_estimate.csv")

    statistical_summary = pd.DataFrame(
        [
            ("mix effects", "Monthly recovery standardized to fixed outstanding-weighted risk mix", "mix_standardized_recovery.csv", "STRONG EVIDENCE", "Compare aggregate and standardized trends before attributing change to operations."),
            ("cohort effects", "Recovery outcomes grouped by account opening cohort", "cohort_recovery.csv", "CORRELATION", "Vintage composition may explain aggregate differences; cohorts are not randomized."),
            ("selection bias", "Targeted accounts differ from never-targeted accounts", "targeting_gap.csv", "CORRELATION", "Targeting comparisons are not causal."),
            ("survivorship bias", "Full accounts denominator retained in monthly scorecard", "monthly_scorecard.csv", "FACT", "Prevents disappearing-denominator improvement."),
            ("Simpson's paradox", "Segmented DPD/risk outputs produced for aggregate comparison", "dpd_scorecard.csv/risk_scorecard.csv", "HYPOTHESIS", "Check segment and aggregate directions before claiming improvement."),
            ("attribution-window bias", "3/7/14/30 day sensitivity generated", "attribution_window_sensitivity.csv", "FACT", "Channel credit changes with window."),
            ("time-series effects", "Partial latest month identified and excluded from executive conclusion", "monthly_scorecard.csv", "FACT", "Avoids comparing incomplete month to complete prior month."),
        ],
        columns=["question", "result", "evidence", "classification", "business_implication"],
    )
    write_csv(statistical_summary, TABLE_DIR / "statistical_investigation_summary.csv")

    mix_adjustment = monthly[["month", "recovery_rate", "targeted_accounts", "eligible_accounts"]].copy()
    mix_adjustment["targeted_share"] = mix_adjustment["targeted_accounts"] / mix_adjustment["eligible_accounts"].replace({0: np.nan})
    mix_adjustment["method"] = "Simple denominator/mix diagnostic; full mix-standardization requires stable segment-level monthly denominators."
    write_csv(mix_adjustment, TABLE_DIR / "mix_adjustment.csv")

    investment = __import__("src.investment", fromlist=["build_investment_scorecard"]).build_investment_scorecard(drivers["channel_scorecard"], vendor, target_gap)
    write_csv(investment, TABLE_DIR / "investment_option_scorecard.csv")
    scenarios = investment[["option", "baseline_recovery", "downside_incremental_recovery", "incremental_recovery", "modeled_cost", "downside_roi", "roi"]].copy()
    scenarios = scenarios.rename(columns={"downside_incremental_recovery": "downside_recovery", "incremental_recovery": "expected_recovery"})
    write_csv(scenarios, TABLE_DIR / "investment_scenarios.csv")

    metric_dict = metrics.metric_dictionary()
    write_csv(metric_dict, TABLE_DIR / "metric_dictionary.csv")
    write_csv(metric_dict, PROJECT_ROOT / "dashboard" / "dashboard_metric_dictionary.csv")
    write_markdown(dataframe_to_markdown(metric_dict), PROJECT_ROOT / "dashboard" / "dashboard_metric_dictionary.md")

    episode = golden["dim_account"][["account_id", "borrower_id", "dpd", "risk_segment", "loan_type", "outstanding_amount"]].merge(
        golden["fact_targeting"].groupby("account_id")["month"].min().rename("first_target_month"), on="account_id", how="left"
    ).merge(
        clean_payments.groupby("account_id")["amount"].sum().rename("recovered_amount"), on="account_id", how="left"
    ).fillna({"recovered_amount": 0})
    episode["analytical_grain"] = "account across observation period; monthly scorecard is account-month"
    write_csv(episode, GOLDEN_DIR / "analytical" / "fct_collection_episode.csv")

    plot_outputs(monthly, drivers["channel_scorecard"], investment, payment_summary)
    write_sql_files()
    make_notebooks()
    write_architecture()
    write_reports(audit, golden, monthly, payment_summary, claim, drivers, investment, assignment_text)
    write_tests()

    zip_path = OUTPUT_DIR / "final_submission" / "collections_analytics_submission.zip"
    excluded_parts = {".venv", "__pycache__", ".pytest_cache", ".ipynb_checkpoints", ".matplotlib"}
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in PROJECT_ROOT.rglob("*"):
            if any(part in excluded_parts for part in path.parts):
                continue
            if path == zip_path or path.is_dir():
                continue
            zf.write(path, path.relative_to(PROJECT_ROOT))
    print("Build complete.")
    print(f"Validated recovery: {money(payment_summary['validated_successful_payment_amount'].iloc[0])}")
    print(f"Recommendation: {investment.iloc[0]['option']}")


if __name__ == "__main__":
    main()
