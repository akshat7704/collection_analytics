-- Staging view for whatsapp_events. All fields kept as supplied; typing happens in clean/golden models.
CREATE OR REPLACE VIEW stg_whatsapp_events AS
SELECT * FROM read_csv_auto('../../data/raw/whatsapp_events.csv', all_varchar=true);
