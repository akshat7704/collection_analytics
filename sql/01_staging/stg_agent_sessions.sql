-- Staging view for agent_sessions. All fields kept as supplied; typing happens in clean/golden models.
CREATE OR REPLACE VIEW stg_agent_sessions AS
SELECT * FROM read_csv_auto('../../data/raw/agent_sessions.csv', all_varchar=true);
