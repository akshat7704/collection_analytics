-- Staging view for calls. All fields kept as supplied; typing happens in clean/golden models.
CREATE OR REPLACE VIEW stg_calls AS
SELECT * FROM read_csv_auto('../../data/raw/calls.csv', all_varchar=true);
