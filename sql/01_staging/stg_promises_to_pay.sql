-- Staging view for promises_to_pay. All fields kept as supplied; typing happens in clean/golden models.
CREATE OR REPLACE VIEW stg_promises_to_pay AS
SELECT * FROM read_csv_auto('../../data/raw/promises_to_pay.csv', all_varchar=true);
