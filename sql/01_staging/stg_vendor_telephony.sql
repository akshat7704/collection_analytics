-- Staging view for vendor_telephony. All fields kept as supplied; typing happens in clean/golden models.
CREATE OR REPLACE VIEW stg_vendor_telephony AS
SELECT * FROM read_csv_auto('../../data/raw/vendor_telephony.csv', all_varchar=true);
