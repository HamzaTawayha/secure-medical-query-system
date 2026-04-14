import time
import pyodbc
from config import SQL_SERVER, SQL_DATABASE, SQL_USERNAME, SQL_PASSWORD


def get_sql_connection(max_retries=3, retry_delay=8):
    connection_string = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server=tcp:{SQL_SERVER},1433;"
        f"Database={SQL_DATABASE};"
        f"Uid={SQL_USERNAME};"
        f"Pwd={SQL_PASSWORD};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "LoginTimeout=120;"
    )

    last_error = None

    for attempt in range(max_retries):
        try:
            return pyodbc.connect(connection_string)
        except pyodbc.Error as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

    raise last_error


def test_sql_connection():
    conn = get_sql_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 5 * FROM Patients;")
    rows = cursor.fetchall()
    conn.close()
    return rows


def query_patients(age_min=None, diagnosis=None, outcome=None):
    conn = get_sql_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM Patients WHERE 1=1"
    params = []

    if age_min is not None:
        query += " AND age >= ?"
        params.append(age_min)

    if diagnosis:
        query += " AND diagnosis = ?"
        params.append(diagnosis)

    if outcome:
        query += " AND outcome = ?"
        params.append(outcome)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows