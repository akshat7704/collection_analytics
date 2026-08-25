SELECT month, contacted_accounts / NULLIF(attempted_accounts, 0) AS contact_rate FROM monthly_scorecard;
