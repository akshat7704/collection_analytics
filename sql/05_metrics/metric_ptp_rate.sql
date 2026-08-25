SELECT month, ptp_accounts / NULLIF(rpc_accounts, 0) AS ptp_rate FROM monthly_scorecard;
