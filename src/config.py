from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REFERENCE_DIR = PROJECT_ROOT / "data" / "reference"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
AUDIT_DIR = PROCESSED_DIR / "audit_outputs"
GOLDEN_DIR = PROJECT_ROOT / "data" / "golden"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
TABLE_DIR = OUTPUT_DIR / "tables"
CHART_DIR = OUTPUT_DIR / "charts"
REPORT_DIR = PROJECT_ROOT / "reports"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
ARCHITECTURE_DIR = PROJECT_ROOT / "architecture"

BUSINESS_TIMEZONE = "Asia/Kolkata"
ATTRIBUTION_WINDOWS_DAYS = [3, 7, 14, 30]
DEFAULT_ATTRIBUTION_DAYS = 7

DATASETS = {
    "borrowers": "borrowers.csv",
    "accounts": "accounts.csv",
    "agents": "agents.csv",
    "agent_sessions": "agent_sessions.csv",
    "campaigns": "campaigns.csv",
    "daily_targeting": "daily_targeting.csv",
    "calls": "calls.csv",
    "call_attempts": "call_attempts.csv",
    "call_dispositions": "call_dispositions.csv",
    "whatsapp_events": "whatsapp_events.csv",
    "sms_events": "sms_events.csv",
    "field_visits": "field_visits.csv",
    "promises_to_pay": "promises_to_pay.csv",
    "payments": "payments.csv",
    "vendor_telephony": "vendor_telephony.csv",
    "complaints": "complaints.csv",
    "account_status_history": "account_status_history.csv",
}

PRIMARY_KEYS = {
    "borrowers": "borrower_id",
    "accounts": "account_id",
    "agents": "agent_id",
    "agent_sessions": "session_id",
    "campaigns": "campaign_id",
    "daily_targeting": "target_id",
    "calls": "call_id",
    "call_attempts": "attempt_id",
    "call_dispositions": "disposition_id",
    "whatsapp_events": "whatsapp_event_id",
    "sms_events": "sms_event_id",
    "field_visits": "visit_id",
    "promises_to_pay": "ptp_id",
    "payments": "payment_id",
    "vendor_telephony": "vendor_id",
    "complaints": "complaint_id",
    "account_status_history": "history_id",
}

EVENT_TABLES = [
    "daily_targeting",
    "calls",
    "call_attempts",
    "call_dispositions",
    "whatsapp_events",
    "sms_events",
    "field_visits",
    "promises_to_pay",
    "payments",
    "complaints",
    "account_status_history",
]
