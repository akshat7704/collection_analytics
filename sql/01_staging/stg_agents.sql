-- Staging view for agents. All fields kept as supplied; typing happens in clean/golden models.
CREATE OR REPLACE VIEW stg_agents AS
SELECT * FROM read_csv_auto('../../data/raw/agents.csv', all_varchar=true);
