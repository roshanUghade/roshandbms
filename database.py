"""
Database Management Module
Manages SQLite connection, schema initialization, migrations, transactions, and raw queries.
"""

import sqlite3
import os
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "product_management.db"
SQL_DIR = BASE_DIR / "sql"


def get_connection():
    """Returns an active SQLite database connection with row factory and foreign keys enabled."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(force_recreate=False):
    """
    Initializes the database schema, triggers, views, and seed data.
    If database exists and force_recreate is False, it will skip re-creation.
    """
    if force_recreate and DB_FILE.exists():
        try:
            os.remove(DB_FILE)
        except Exception:
            pass

    schema_file = SQL_DIR / "schema.sql"
    triggers_file = SQL_DIR / "triggers.sql"
    views_file = SQL_DIR / "views.sql"
    seed_file = SQL_DIR / "seed_data.sql"

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if tables already exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        tables_exist = cursor.fetchone() is not None

        if not tables_exist or force_recreate:
            # 1. Execute schema.sql
            if schema_file.exists():
                with open(schema_file, "r", encoding="utf-8") as f:
                    cursor.executescript(f.read())

            # 2. Execute triggers.sql
            if triggers_file.exists():
                with open(triggers_file, "r", encoding="utf-8") as f:
                    cursor.executescript(f.read())

            # 3. Execute views.sql
            if views_file.exists():
                with open(views_file, "r", encoding="utf-8") as f:
                    cursor.executescript(f.read())

            # 4. Execute seed_data.sql
            if seed_file.exists():
                with open(seed_file, "r", encoding="utf-8") as f:
                    cursor.executescript(f.read())

            conn.commit()
            print("[Database] Initialized successfully with schema, triggers, views, and seed data.")
        else:
            # Ensure triggers and views are always up-to-date
            if triggers_file.exists():
                with open(triggers_file, "r", encoding="utf-8") as f:
                    cursor.executescript(f.read())
            if views_file.exists():
                with open(views_file, "r", encoding="utf-8") as f:
                    cursor.executescript(f.read())
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[Database Error] Initialization failed: {e}")
        raise e
    finally:
        conn.close()


def query_db(query, args=(), one=False):
    """Executes a SELECT query and returns a list of dictionaries (or a single dictionary)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, args)
        rows = cur.fetchall()
        result = [dict(row) for row in rows]
        return (result[0] if result else None) if one else result
    finally:
        conn.close()


def execute_db(query, args=()):
    """Executes an INSERT, UPDATE, or DELETE query and commits changes. Returns lastrowid."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, args)
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def execute_raw_sql(sql_text):
    """
    Executes user-provided raw SQL queries for the live SQL console.
    Returns:
        success: bool
        columns: list of str
        rows: list of list/tuple
        row_count: int
        execution_time_ms: float
        error_message: str or None
    """
    start_time = time.perf_counter()
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Split script or execute single query
        statements = [stmt.strip() for stmt in sql_text.split(";") if stmt.strip()]
        last_cur = None
        
        for stmt in statements:
            last_cur = cur.execute(stmt)

        conn.commit()
        execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        if last_cur and last_cur.description:
            columns = [desc[0] for desc in last_cur.description]
            raw_rows = last_cur.fetchall()
            rows = [list(row) for row in raw_rows]
            return {
                "success": True,
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "execution_time_ms": execution_time_ms,
                "error_message": None,
                "type": "SELECT"
            }
        else:
            return {
                "success": True,
                "columns": [],
                "rows": [],
                "row_count": cur.rowcount if cur.rowcount != -1 else 0,
                "execution_time_ms": execution_time_ms,
                "error_message": None,
                "type": "DML"
            }
    except Exception as e:
        conn.rollback()
        execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "success": False,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "execution_time_ms": execution_time_ms,
            "error_message": str(e),
            "type": "ERROR"
        }
    finally:
        conn.close()


def get_database_schema_metadata():
    """
    Retrieves full metadata of all tables, columns, constraints, foreign keys,
    views, and triggers for dynamic visual inspection and ER rendering.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Get Tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = [row[0] for row in cur.fetchall()]

    schema = {"tables": {}, "views": [], "triggers": []}

    for table in tables:
        # Columns
        cur.execute(f"PRAGMA table_info({table})")
        cols = cur.fetchall()
        columns = []
        for c in cols:
            columns.append({
                "cid": c[0],
                "name": c[1],
                "type": c[2],
                "notnull": bool(c[3]),
                "dflt_value": c[4],
                "pk": bool(c[5])
            })

        # Foreign Keys
        cur.execute(f"PRAGMA foreign_key_list({table})")
        fks = cur.fetchall()
        foreign_keys = []
        for fk in fks:
            foreign_keys.append({
                "id": fk[0],
                "from_col": fk[3],
                "to_table": fk[2],
                "to_col": fk[4],
                "on_update": fk[5],
                "on_delete": fk[6]
            })

        # Row count
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]

        schema["tables"][table] = {
            "columns": columns,
            "foreign_keys": foreign_keys,
            "row_count": count
        }

    # Get Views
    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='view' ORDER BY name")
    schema["views"] = [{"name": row[0], "sql": row[1]} for row in cur.fetchall()]

    # Get Triggers
    cur.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger' ORDER BY name")
    schema["triggers"] = [{"name": row[0], "table": row[1], "sql": row[2]} for row in cur.fetchall()]

    conn.close()
    return schema
