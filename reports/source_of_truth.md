# Source Of Truth Decisions

| Entity / metric | Chosen source | Alternative sources | Evidence | Rationale | Implication |
|---|---|---|---|---|---|
| Borrower | `borrowers.csv` plus `accounts.borrower_id` | event borrower IDs | FK audit and stable account relationship | Accounts provide the business relationship; borrower table supplies attributes | Event borrower conflicts are not merged by name |
| Account | `accounts.csv` | status history | Account has static principal/outstanding/DPD/risk fields | Needed as portfolio denominator | Outstanding is treated as supplied static balance |
| Agent | `agents.employee_code` when present, else `agent_id` | agent name | Names are insufficient identity evidence | Avoid false merges | Agent analysis uses canonical mapping |
| Recovery | validated successful `payments.csv` | raw success totals | Duplicate payment forensics shows overstatement of INR 191,803,696 | Failed/reversed/duplicate payments do not represent cash recovery | Independent metrics use clean payments |
| Contact | `calls.call_status` answered/connected/contacted | dispositions only | Calls table contains call outcome and duration | Contact is attempt-level operational event | Contact rate denominator is attempted accounts |
| RPC/PTP | `call_dispositions.csv` and `promises_to_pay.csv` | call status | Dispositions/PTP table carry intent semantics | Keeps RPC/PTP separate from contact | Unmapped legacy codes remain a limitation |
| Attribution | latest eligible touch within 7 days | latest-touch all-time, direct payment only | Attribution sensitivity tables generated | Prevents unlimited credit assignment | Association only; not causal |
| Cost metrics | investment scenario assumptions | actual cost records | Actual cost fields unavailable | The supplied dataset lacks cost facts | Cost per rupee is modeled, not observed |
