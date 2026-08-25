-- Staging view for sms_events. All fields kept as supplied; typing happens in clean/golden models.
CREATE OR REPLACE VIEW stg_sms_events AS
SELECT * FROM read_csv_auto('../../data/raw/sms_events.csv', all_varchar=true);
