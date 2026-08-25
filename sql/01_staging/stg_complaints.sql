-- Staging view for complaints. All fields kept as supplied; typing happens in clean/golden models.
CREATE OR REPLACE VIEW stg_complaints AS
SELECT * FROM read_csv_auto('../../data/raw/complaints.csv', all_varchar=true);
