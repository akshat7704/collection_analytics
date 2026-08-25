"""
Collections Performance Forensics & Recovery Analytics
Interactive Executive Streamlit Dashboard
"""

from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="Collections Analytics & Forensics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main {
        background-color: #0e1117;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-label {
        font-size: 13px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-val {
        font-size: 24px;
        font-weight: 700;
        color: #f8fafc;
    }
    .metric-sub {
        font-size: 12px;
        margin-top: 4px;
    }
    .badge-positive {
        color: #10b981;
    }
    .badge-negative {
        color: #ef4444;
    }
    .badge-neutral {
        color: #38bdf8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Determine root directory paths
BASE_DIR = Path(__file__).resolve().parent
TABLES_DIR = BASE_DIR / "outputs" / "tables"
CHARTS_DIR = BASE_DIR / "outputs" / "charts"
REPORTS_DIR = BASE_DIR / "reports"
DATA_DIR = BASE_DIR / "data"

@st.cache_data
def load_csv(file_name: str) -> pd.DataFrame:
    path = TABLES_DIR / file_name
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()

# Load analytical tables
monthly_df = load_csv("monthly_scorecard.csv")
claim_df = load_csv("claim_validation.csv")
channel_df = load_csv("channel_scorecard.csv")
investment_df = load_csv("investment_option_scorecard.csv")
scenarios_df = load_csv("investment_scenarios.csv")
portfolio_mix_df = load_csv("portfolio_mix.csv")
dpd_df = load_csv("dpd_scorecard.csv")
vendor_df = load_csv("vendor_scorecard.csv")
calling_time_df = load_csv("calling_time_scorecard.csv")
attempt_df = load_csv("attempt_frequency_scorecard.csv")
stats_df = load_csv("statistical_investigation_summary.csv")
counterfactual_df = load_csv("counterfactual_estimate.csv")
metric_dict_df = load_csv("metric_dictionary.csv")

# Sidebar
st.sidebar.image("https://img.icons8.com/fluency/96/combo-chart.png", width=64)
st.sidebar.title("Collections Intelligence")
st.sidebar.caption("Forensics, Claim Validation & ₹10 Cr Investment Model")

nav_selection = st.sidebar.radio(
    "Navigation Menu",
    [
        "🏛️ Executive Overview",
        "🔍 11% Claim Validation",
        "📈 Performance Reconstruction",
        "🎯 Driver & Channel Forensics",
        "💡 ₹10 Cr Investment & ROI Simulator",
        "🛡️ Data Quality & Audit Trail",
        "📚 Documentation & Downloads",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 Executive Highlights")
st.sidebar.markdown("- **Validated Recovery:** ₹114.97 Cr")
st.sidebar.markdown("- **Forensic Overstatement:** -₹19.18 Cr")
st.sidebar.markdown("- **Latest MoM Trend:** -74.67%")
st.sidebar.markdown("- **Recommended Area:** WhatsApp / Digital")
st.sidebar.markdown("- **Projected ROI:** 1.15x")

# -------------------------------------------------------------
# PAGE 1: EXECUTIVE OVERVIEW
# -------------------------------------------------------------
if nav_selection == "🏛️ Executive Overview":
    st.title("Executive Intelligence Summary")
    st.markdown(
        """
        Reconstructing **collections performance** from raw operational logs, stress-testing 
        the reported **11% MoM improvement claim**, and providing an evidence-backed capital deployment recommendation for **₹10 Crore**.
        """
    )

    # Top KPI row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Validated Recovery</div>
                <div class="metric-val">₹1,149.68M</div>
                <div class="metric-sub badge-neutral">Raw: ₹1,341.49M</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Forensic Overstatement</div>
                <div class="metric-val">-₹191.80M</div>
                <div class="metric-sub badge-negative">-14.3% phantom payments</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Latest Recovery Rate</div>
                <div class="metric-val">0.36%</div>
                <div class="metric-sub badge-neutral">Standardized Portfolio</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Reported 11% Claim</div>
                <div class="metric-val" style="color: #ef4444;">REJECTED</div>
                <div class="metric-sub badge-negative">Actual MoM: -74.67%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col5:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Recommended Investment</div>
                <div class="metric-val" style="color: #10b981;">WhatsApp / Digital</div>
                <div class="metric-sub badge-positive">ROI: 1.15x | ₹11.50 Cr Uplift</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Core Findings Layout
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Monthly Validated Recovery & Trend")
        if not monthly_df.empty and "month" in monthly_df.columns:
            fig = px.bar(
                monthly_df,
                x="month",
                y="recovered_amount",
                title="Monthly Total Amount Recovered (INR)",
                labels={"recovered_amount": "Recovered Amount (₹)", "month": "Month"},
                color="recovered_amount",
                color_continuous_scale="Blues",
            )
            fig.update_layout(showlegend=False, template="plotly_dark", height=380)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Monthly scorecard data not found.")

    with col_right:
        st.subheader("Key Findings & Verdicts")
        st.markdown(
            """
            - 🚨 **The 11% Claim is False**: Reported improvement was created by denominator shrinkage, aggressive touch attribution, and duplicate payment double-counting.
            - 🔍 **Duplicate Overstatement**: ₹19.18 Cr of duplicate payment events were detected in the raw feeds and excluded in the Golden Dataset.
            - 📱 **Channel Efficiency**: WhatsApp and Agentic Voice yield the lowest cost-per-contact and highest digital promise conversion rate.
            - 💼 **Capital Allocation**: Deploying ₹10 Cr into WhatsApp / Digital Journeys yields an estimated incremental recovery of **₹114.97M** (1.15x ROI).
            """
        )
        st.success("✅ **Recommendation**: Allocate ₹10 Cr to WhatsApp / Digital Engagement with phased A/B pilot validation.")


# -------------------------------------------------------------
# PAGE 2: 11% CLAIM VALIDATION
# -------------------------------------------------------------
elif nav_selection == "🔍 11% Claim Validation":
    st.title("Debunking the Reported 11% MoM Improvement")
    st.markdown(
        """
        Leadership reported that *'Recovery has improved by 11% month-on-month'*.
        We built an independent Golden Dataset to reconcile this claim against reality.
        """
    )

    if not claim_df.empty:
        c1, c2 = st.columns([3, 2])
        with c1:
            fig_claim = go.Figure()
            if "month" in claim_df.columns and "reported_metric_proxy" in claim_df.columns:
                fig_claim.add_trace(
                    go.Scatter(
                        x=claim_df["month"],
                        y=claim_df["reported_metric_proxy"] * 100,
                        mode="lines+markers",
                        name="Reported Proxy Metric (%)",
                        line=dict(color="#f59e0b", width=3),
                    )
                )
            if "recovery_rate" in claim_df.columns:
                fig_claim.add_trace(
                    go.Scatter(
                        x=claim_df["month"],
                        y=claim_df["recovery_rate"] * 100,
                        mode="lines+markers",
                        name="Independent Recovery Rate (%)",
                        line=dict(color="#3b82f6", width=3),
                    )
                )
            fig_claim.update_layout(
                title="Reported Proxy vs Independent Recovery Rate",
                xaxis_title="Month",
                yaxis_title="Rate (%)",
                template="plotly_dark",
                height=400,
            )
            st.plotly_chart(fig_claim, use_container_width=True)

        with c2:
            st.subheader("Forensic Gap Diagnosis")
            st.markdown(
                """
                1. **Denominator Manipulation**: Non-performing accounts were filtered out or deferred from active denominator targeting.
                2. **Touch Attribution Window Leakage**: Payments occurring days after an interaction were inappropriately credited to latest campaigns.
                3. **Duplicate Transaction Ingestion**: Batch retry payments were double-counted in reporting pipelines.
                4. **Mix Shift Distortion**: Early-stage DPD accounts temporarily entered the portfolio, inflating short-term recovery ratios (Simpson's Paradox).
                """
            )

        st.subheader("Monthly Claim Reconciled Table")
        st.dataframe(claim_df, use_container_width=True)
    else:
        st.warning("Claim validation table not found.")


# -------------------------------------------------------------
# PAGE 3: PERFORMANCE RECONSTRUCTION
# -------------------------------------------------------------
elif nav_selection == "📈 Performance Reconstruction":
    st.title("Reconstructed Monthly Performance Scorecard")
    st.markdown("Reconstructed end-to-end funnel metrics across all 12+ months on the validated Golden Dataset.")

    if not monthly_df.empty:
        # Funnel Metrics
        col1, col2, col3, col4 = st.columns(4)
        latest = monthly_df.iloc[-1]
        col1.metric("Contact Rate", f"{latest.get('contact_rate', 0)*100:.2f}%")
        col2.metric("RPC Rate", f"{latest.get('rpc_rate', 0)*100:.2f}%")
        col3.metric("PTP Rate", f"{latest.get('ptp_rate', 0)*100:.2f}%")
        col4.metric("PTP Kept Rate", f"{latest.get('ptp_kept_rate', 0)*100:.2f}%")

        st.markdown("---")

        tab_m1, tab_m2 = st.tabs(["📊 Funnel & Rates", "💰 Recoveries & Financials"])
        with tab_m1:
            fig_rates = px.line(
                monthly_df,
                x="month",
                y=["contact_rate", "rpc_rate", "ptp_rate", "ptp_kept_rate"],
                title="Operational Funnel Efficiency Over Time",
                template="plotly_dark",
                markers=True,
            )
            st.plotly_chart(fig_rates, use_container_width=True)

        with tab_m2:
            fig_fin = px.line(
                monthly_df,
                x="month",
                y=["recovery_per_account", "recovery_per_agent_hour"],
                title="Recovery Productivity per Account & Agent Hour (INR)",
                template="plotly_dark",
                markers=True,
            )
            st.plotly_chart(fig_fin, use_container_width=True)

        st.subheader("Full Scorecard Data")
        st.dataframe(monthly_df, use_container_width=True)
    else:
        st.info("No monthly scorecard data found.")


# -------------------------------------------------------------
# PAGE 4: DRIVER & CHANNEL FORENSICS
# -------------------------------------------------------------
elif nav_selection == "🎯 Driver & Channel Forensics":
    st.title("Forensic Driver & Channel Investigation")
    st.markdown("Analyzing key operational levers: Channels, DPD Buckets, Calling Windows, and Telephony Vendors.")

    t1, t2, t3, t4 = st.tabs(["📡 Channel Performance", "⏱️ DPD & Mix Shift", "⏰ Time of Day", "🏢 Vendor Benchmarks"])

    with t1:
        st.subheader("Recovery by Engagement Channel")
        if not channel_df.empty:
            c1, c2 = st.columns([2, 1])
            with c1:
                fig_ch = px.bar(
                    channel_df,
                    x="channel",
                    y="recovered_amount",
                    color="channel",
                    title="Total Amount Recovered by Channel (INR)",
                    template="plotly_dark",
                )
                st.plotly_chart(fig_ch, use_container_width=True)
            with c2:
                st.dataframe(channel_df, use_container_width=True)
        else:
            st.info("Channel data not available.")

    with t2:
        st.subheader("Delinquency (DPD) Distribution")
        if not dpd_df.empty:
            fig_dpd = px.pie(
                dpd_df,
                names="dpd_bucket",
                values="recovered_amount",
                title="Share of Recovery by DPD Bucket",
                template="plotly_dark",
                hole=0.4,
            )
            st.plotly_chart(fig_dpd, use_container_width=True)
            st.dataframe(dpd_df, use_container_width=True)

    with t3:
        st.subheader("Calling Window Productivity")
        if not calling_time_df.empty:
            hour_col = "call_hour_local" if "call_hour_local" in calling_time_df.columns else "calling_hour" if "calling_hour" in calling_time_df.columns else calling_time_df.columns[0]
            rate_col = "contact_rate" if "contact_rate" in calling_time_df.columns else calling_time_df.columns[-1]
            fig_time = px.bar(
                calling_time_df,
                x=hour_col,
                y=rate_col,
                title="Contact Rate by Calling Hour (Local Time)",
                labels={hour_col: "Calling Hour (Local)", rate_col: "Contact Rate"},
                template="plotly_dark",
            )
            st.plotly_chart(fig_time, use_container_width=True)
            st.dataframe(calling_time_df, use_container_width=True)

    with t4:
        st.subheader("Vendor Telephony Reliability")
        if not vendor_df.empty:
            st.dataframe(vendor_df, use_container_width=True)


# -------------------------------------------------------------
# PAGE 5: ₹10 CR INVESTMENT & ROI SIMULATOR
# -------------------------------------------------------------
elif nav_selection == "💡 ₹10 Cr Investment & ROI Simulator":
    st.title("₹10 Crore Strategic Investment Case")
    st.markdown("Evaluating all 6 options specified by executive leadership to maximize recovery return on investment.")

    if not investment_df.empty:
        st.subheader("Option Comparison Matrix")
        roi_col = "roi" if "roi" in investment_df.columns else "estimated_roi" if "estimated_roi" in investment_df.columns else None
        if roi_col:
            st.dataframe(
                investment_df.style.highlight_max(subset=[roi_col], color="#065f46"),
                use_container_width=True,
            )
            fig_inv = px.bar(
                investment_df,
                x="option",
                y=roi_col,
                color=roi_col,
                title="Estimated ROI by Investment Option",
                labels={roi_col: "Estimated ROI (x)", "option": "Option"},
                color_continuous_scale="Viridis",
                template="plotly_dark",
            )
            st.plotly_chart(fig_inv, use_container_width=True)
        else:
            st.dataframe(investment_df, use_container_width=True)

    st.markdown("---")
    st.subheader("🎛️ Interactive Investment Scenario Simulator")

    s_col1, s_col2, s_col3 = st.columns(3)
    with s_col1:
        budget = st.slider("Investment Budget (₹ Crore)", min_value=1.0, max_value=25.0, value=10.0, step=0.5)
    with s_col2:
        target_uplift = st.slider("Expected Recovery Uplift (%)", min_value=1.0, max_value=25.0, value=10.0, step=0.5)
    with s_col3:
        baseline_pool = st.number_input("Annual Validated Recovery Base (₹ Crore)", value=114.97)

    # Dynamic Calculations
    budget_inr = budget * 1e7
    incremental_recovery = (baseline_pool * 1e7) * (target_uplift / 100.0)
    simulated_roi = incremental_recovery / budget_inr if budget_inr > 0 else 0
    breakeven_uplift = (budget_inr / (baseline_pool * 1e7)) * 100

    r1, r2, r3 = st.columns(3)
    r1.metric("Projected Incremental Recovery", f"₹{incremental_recovery/1e7:.2f} Cr")
    r2.metric("Simulated Net ROI", f"{simulated_roi:.2f}x")
    r3.metric("Break-even Required Uplift", f"{breakeven_uplift:.2f}%")


# -------------------------------------------------------------
# PAGE 6: DATA QUALITY & AUDIT TRAIL
# -------------------------------------------------------------
elif nav_selection == "🛡️ Data Quality & Audit Trail":
    st.title("Data Quality, Forensics & Audit Trail")
    st.markdown(
        """
        Transparent tracking of all cleaning transformations, deduplication decisions, and source-of-truth rules.
        """
    )

    q1, q2 = st.columns(2)
    with q1:
        st.markdown("### 🧹 Duplicate Payment Impact")
        st.markdown(
            """
            - **Raw Payment Total**: ₹1,341,485,926
            - **Validated Golden Total**: ₹1,149,682,230
            - **Overstatement Removed**: ₹191,803,696 (-14.3%)
            - **Treatment**: Extracted unique idempotent transaction references; removed duplicate webhook deliveries.
            """
        )
    with q2:
        st.markdown("### 🕒 Timestamp Normalization")
        st.markdown(
            """
            - Converted heterogeneous string timestamps and epoch values into ISO-8601 UTC.
            - Standardized local timezone offsets to compute calling hour distributions accurately.
            - Filtered future-dated anomalous records.
            """
        )

    st.markdown("---")
    st.subheader("Statistical Investigation Summary")
    if not stats_df.empty:
        st.dataframe(stats_df, use_container_width=True)


# -------------------------------------------------------------
# PAGE 7: DOCUMENTATION & DOWNLOADS
# -------------------------------------------------------------
elif nav_selection == "📚 Documentation & Downloads":
    st.title("Reports & Submission Artifacts")
    st.markdown("Access all generated executive memos, data quality reports, and metric dictionaries.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📄 Executive Memo")
        memo_path = REPORTS_DIR / "executive_memo.md"
        if memo_path.exists():
            with open(memo_path, "r", encoding="utf-8") as f:
                memo_content = f.read()
            st.markdown(memo_content[:1200] + "...")
            st.download_button(
                "⬇️ Download Executive Memo (Markdown)",
                memo_content,
                file_name="executive_memo.md",
                mime="text/markdown",
            )
        else:
            st.info("Executive memo file not found.")

    with col2:
        st.subheader("📊 Metric Dictionary")
        if not metric_dict_df.empty:
            st.dataframe(metric_dict_df, use_container_width=True)
            csv_data = metric_dict_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download Metric Dictionary (CSV)",
                csv_data,
                file_name="metric_dictionary.csv",
                mime="text/csv",
            )

st.sidebar.caption("© Collections Forensics & Recovery Analytics Suite")
