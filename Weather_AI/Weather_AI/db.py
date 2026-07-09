import os
from dataclasses import dataclass

import pymysql
from pymysql.cursors import DictCursor


@dataclass
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


def get_db_config_from_env() -> DBConfig:
    return DBConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "baza_meteo"),
    )


def connect_db(config: DBConfig):
    return pymysql.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
    )


def ping(conn) -> bool:
    try:
        conn.ping(reconnect=True)
        return True
    except Exception:
        return False


def run_select(conn, sql: str):
    with conn.cursor() as cursor:
        cursor.execute(sql)
        rows = cursor.fetchall()
    return rows


def get_schema(conn, database_name: str):
    sql = """
    SELECT
        TABLE_NAME,
        COLUMN_NAME,
        DATA_TYPE,
        COLUMN_KEY,
        IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = %s
    ORDER BY TABLE_NAME, ORDINAL_POSITION
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (database_name,))
        rows = cursor.fetchall()

    schema = {}
    for row in rows:
        table = row["TABLE_NAME"]
        schema.setdefault(table, [])
        schema[table].append({
            "column_name": row["COLUMN_NAME"],
            "data_type": row["DATA_TYPE"],
            "column_key": row["COLUMN_KEY"],
            "is_nullable": row["IS_NULLABLE"],
        })
    return schema


def schema_to_text(schema: dict) -> str:
    lines = []
    for table_name, columns in schema.items():
        lines.append(f"TABLE {table_name}")
        for col in columns:
            lines.append(
                f"  - {col['column_name']} ({col['data_type']})"
                f"{' PK' if col['column_key'] == 'PRI' else ''}"
                f"{' NULL' if col['is_nullable'] == 'YES' else ' NOT NULL'}"
            )
        lines.append("")
    return "\n".join(lines)
def save_chat_history(conn, user_question, generated_sql=None, summary=None, answer_type="weather_query"):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO chat_history 
            (user_question, generated_sql, summary, answer_type)
            VALUES (%s, %s, %s, %s)
            """,
            (user_question, generated_sql, summary, answer_type)
        )
        conn.commit()


def get_chat_history(conn, limit=50):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_question, generated_sql, summary, answer_type, created_at
            FROM chat_history
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,)
        )
        return cursor.fetchall()