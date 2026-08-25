-- Staging view for campaigns. All fields kept as supplied; typing happens in clean/golden models.
CREATE OR REPLACE VIEW stg_campaigns AS
SELECT * FROM read_csv_auto('../../data/raw/campaigns.csv', all_varchar=true);
