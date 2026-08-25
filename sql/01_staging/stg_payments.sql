-- Staging view for payments. All fields kept as supplied; typing happens in clean/golden models.
CREATE OR REPLACE VIEW stg_payments AS
SELECT * FROM read_csv_auto('../../data/raw/payments.csv', all_varchar=true);
