-- Staging view for call_attempts. All fields kept as supplied; typing happens in clean/golden models.
CREATE OR REPLACE VIEW stg_call_attempts AS
SELECT * FROM read_csv_auto('../../data/raw/call_attempts.csv', all_varchar=true);
