-- Staging view for field_visits. All fields kept as supplied; typing happens in clean/golden models.
CREATE OR REPLACE VIEW stg_field_visits AS
SELECT * FROM read_csv_auto('../../data/raw/field_visits.csv', all_varchar=true);
