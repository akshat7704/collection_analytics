-- Staging view for call_dispositions. All fields kept as supplied; typing happens in clean/golden models.
CREATE OR REPLACE VIEW stg_call_dispositions AS
SELECT * FROM read_csv_auto('../../data/raw/call_dispositions.csv', all_varchar=true);
