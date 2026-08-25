-- Staging view for daily_targeting. All fields kept as supplied; typing happens in clean/golden models.
CREATE OR REPLACE VIEW stg_daily_targeting AS
SELECT * FROM read_csv_auto('../../data/raw/daily_targeting.csv', all_varchar=true);
