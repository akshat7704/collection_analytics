-- Staging view for account_status_history. All fields kept as supplied; typing happens in clean/golden models.
CREATE OR REPLACE VIEW stg_account_status_history AS
SELECT * FROM read_csv_auto('../../data/raw/account_status_history.csv', all_varchar=true);
