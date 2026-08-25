SELECT month, recovered_amount / NULLIF(eligible_accounts, 0) AS recovery_per_account FROM monthly_scorecard;
