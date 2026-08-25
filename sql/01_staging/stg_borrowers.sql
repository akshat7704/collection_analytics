-- Staging view for borrowers. All fields kept as supplied; typing happens in clean/golden models.
CREATE OR REPLACE VIEW stg_borrowers AS
SELECT * FROM read_csv_auto('../../data/raw/borrowers.csv', all_varchar=true);
