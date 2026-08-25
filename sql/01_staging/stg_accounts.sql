-- Staging view for accounts. All fields kept as supplied; typing happens in clean/golden models.
CREATE OR REPLACE VIEW stg_accounts AS
SELECT * FROM read_csv_auto('../../data/raw/accounts.csv', all_varchar=true);
