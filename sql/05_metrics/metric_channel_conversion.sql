SELECT channel, paid_accounts / NULLIF(touched_accounts, 0) AS channel_conversion FROM channel_scorecard;
