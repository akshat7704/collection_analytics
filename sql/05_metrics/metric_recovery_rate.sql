SELECT month, recovered_amount / NULLIF(total_outstanding_amount, 0) AS recovery_rate FROM monthly_scorecard;
