import sqlite3
import pandas as pd
from dbutils import load_file_into_db, execute_sql_from_file


def main(data_files, sql, db, output_file):
    """
    Main function to load files into a SQLite DB, execute SQL from a text file, and save results to Excel.

    :param data_files: List of file paths to load into the DB.
    :param sql: Path to a .txt file containing SQL statements.
    :param db: Path to the SQLite database file.
    :param output_file: Path to the output Excel file.
    """
    # Connect to the SQLite database
    conn = sqlite3.connect(db, timeout=30)

    # Load each file into the database
    if len(data_files) > 0:
        for file in data_files:
            load_file_into_db(file, conn)

    # Execute SQL from the provided text file and load results
    if sql is not None:
        results_df = execute_sql_from_file(sql, conn)

        # Write the results to an Excel file
        if output_file is not None:

            try:
                if not results_df.empty:
                    excel_file_path = output_file
                    with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
                        results_df.to_excel(writer, sheet_name='Sheet1', index=False)
                    print(f"Data written to {excel_file_path}")
                else:
                    print("DataFrame is empty. No data written to Excel.")
            except Exception as e:
                print(f"Failed to write DataFrame to Excel: {e}")

    # Close the database connection
    conn.close()


if __name__ == "__main__":
    # Example usage
    files = ['./data_sets/employees.csv', './data_sets/managers.csv']  # Add your file paths here
    sql_file = './queries/query.sql.txt'
    db_file = 'hr.db'
    output_excel = 'results/results.xlsx'
    main(files, sql_file, db_file, output_excel)
