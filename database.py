import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "schoolflow.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"
SEED_PATH = BASE_DIR / "seed.sql"


def run_sql_file(connection, file_path):
    sql_script = file_path.read_text(encoding="utf-8")
    connection.executescript(sql_script)


def create_database():
    if DB_PATH.exists():
        DB_PATH.unlink()

    connection = sqlite3.connect(DB_PATH)

    try:
        run_sql_file(connection, SCHEMA_PATH)
        run_sql_file(connection, SEED_PATH)

        connection.commit()

        print("SchoolFlow database created successfully.")
        print(f"Database path: {DB_PATH}")

    finally:
        connection.close()


if __name__ == "__main__":
    create_database()