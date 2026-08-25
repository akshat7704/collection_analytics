SELECT month, recovered_amount / NULLIF(agent_hours, 0) AS recovery_per_agent_hour FROM monthly_scorecard;
