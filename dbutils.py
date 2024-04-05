import os
import pandas as pd
from pandas.errors import DatabaseError


def load_file_into_db(filename, conn):
    """
    Loads data from a given file into a SQLite database table named after the file.
    """

    # Check if filename parsing is correct
    if not filename or '.' not in filename:
        raise ValueError("Invalid or empty filename specified.")

    try:
        table_name = extract_table_name_from_path(filename)
    except ValueError as e:
        print(e)
        table_name = "default_table_name"  # Fallback table name or handle error as needed

    print(f"Using table name: {table_name}")

    # Ensure the table name is not empty
    if not table_name.strip():
        raise ValueError("Empty table name specified.")

    df = pd.read_csv(filename)

    # SQLite does not enforce the size and precision that some of these types might suggest.
    # Adjust the mapping as necessary for your use case.
    dtype_mapping = {
        'int64': 'INTEGER',
        'int32': 'INTEGER',
        'float64': 'REAL',
        'float32': 'REAL',
        'object': 'TEXT',  # Assuming object columns are strings; adjust if your use case differs.
        # Add more mappings as needed
    }

    # Generate SQL data types for each column, quoting column names to handle spaces and reserved keywords.
    sql_column_types = []
    for col_name, dtype in df.dtypes.items():
        sql_type = dtype_mapping.get(str(dtype), 'TEXT')  # Fallback to TEXT if the dtype isn't explicitly mapped.
        col_name_quoted = f'"{col_name}"'  # Quote column names to handle any special characters or reserved words.
        sql_column_types.append(f'{col_name_quoted} {sql_type}')

    try:
        # Create a cursor object
        cur = conn.cursor()

        # Construct the CREATE TABLE SQL statement with proper formatting.
        create_table_sql = (f"CREATE TABLE IF NOT EXISTS \"{table_name}\" (\n    " + ",\n    ".join(sql_column_types)
                            + "\n);")
        print(create_table_sql)

        cur.execute(create_table_sql)

        # Commit the changes
        conn.commit()

    except DatabaseError as e:
        conn.rollback()  # Rollback in case of error
        raise e

    # Extract dtypes and map to SQLite types
    sql_dtypes = {col: dtype_mapping[str(df[col].dtype)] for col in df.columns}

    print(sql_dtypes)

    df.to_sql(table_name, conn, if_exists='replace', index=False, dtype=sql_dtypes)


def execute_sql_from_file(sql_file, conn):
    """
    Executes SQL statements stored in a .txt file.

    :param sql_file: Path to a .txt file containing SQL statements.
    :param conn: SQLite database connection object.
    """
    # Read the entire SQL file
    with open(sql_file, 'r') as file:
        sql_content = file.read()

    # Use the chunksize parameter
    chunk_size = 100  # Adjust based on your memory constraints and dataset

    # Debugging print to check each command
    print(f"Executing SQL command: {sql_content[:450]}...")  # Print first 450 characters to avoid clutter

    try:
        # Use the generator to accumulate chunks into a list
        chunks = list(fetch_chunks(sql_content, conn, chunk_size))

        # Concatenate the list of DataFrames into a single DataFrame
        results_df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()

        print(results_df.head())

    except DatabaseError as exc:
        raise ValueError(f"Execution failed on sql '{sql_content}': {exc}")

    return results_df


# Generator function to yield chunks of data
def fetch_chunks(query, connection, chunk_size):
    for chunk in pd.read_sql_query(query, connection, chunksize=chunk_size):
        yield chunk


# Function to extract table name from path
def extract_table_name_from_path(path):
    # Extract the filename from the path
    filename = os.path.basename(path)

    if not filename or filename.startswith('.'):
        raise ValueError("Filename is either empty or starts with a dot, indicating it might be hidden or invalid.")

    # Splitting by '.' and removing empty parts
    parts = [part for part in filename.split('.') if part]

    # Handle filenames without an extension or hidden files with a proper name
    if not parts or (len(parts) == 1 and filename.startswith('.')):
        raise ValueError("Filename does not contain a valid name before the extension.")

    # The first part is the table name for standard filenames, the second part for hidden files with an extension
    table_name = parts[0] if not filename.startswith('.') else parts[1]

    return table_name

