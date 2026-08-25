-- Staging view for data_dictionary. All fields kept as supplied; typing happens in clean/golden models.
CREATE OR REPLACE VIEW stg_data_dictionary AS
SELECT * FROM read_csv_auto('../../data/raw/data_dictionary.csv', all_varchar=true);
