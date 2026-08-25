SELECT month, ptp_kept_accounts / NULLIF(ptp_accounts, 0) AS ptp_kept_rate FROM monthly_scorecard;
