SELECT month, rpc_accounts / NULLIF(contacted_accounts, 0) AS rpc_rate FROM monthly_scorecard;
