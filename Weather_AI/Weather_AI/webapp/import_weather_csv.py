import os
from pathlib import Path

import pandas as pd

from db import connect_db, get_db_config_from_env


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
CSV_FILE = BASE_DIR / "weather_data.csv"


def load_env_manual(env_path: Path):
    if not env_path.exists():
        raise RuntimeError(f"Fișierul .env nu există: {env_path}")

    content = env_path.read_text(encoding="utf-8-sig")

    for raw_line in content.splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ[key] = value


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={c: c.strip() for c in df.columns})

    required = [
        "city",
        "country",
        "entity",
        "continent",
        "date_record",
        "hour_record",
        "temperature_avg",
        "temperature_min",
        "temperature_max",
        "humidity",
        "precipitation",
        "wind_speed",
        "weather_code",
    ]

    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"CSV-ul nu conține coloanele necesare: {missing}")

    df = df[required].copy()
    df["date_record"] = pd.to_datetime(df["date_record"], errors="coerce").dt.date

    numeric_cols = [
        "hour_record",
        "temperature_avg",
        "temperature_min",
        "temperature_max",
        "humidity",
        "precipitation",
        "wind_speed",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["city", "date_record"])
    return df


def main():
    load_env_manual(ENV_PATH)

    print("ENV_PATH =", ENV_PATH)
    print("DB_HOST =", os.getenv("DB_HOST"))
    print("DB_PORT =", os.getenv("DB_PORT"))
    print("DB_USER =", os.getenv("DB_USER"))
    print("DB_NAME =", os.getenv("DB_NAME"))

    if not CSV_FILE.exists():
        raise FileNotFoundError(f"Fișierul {CSV_FILE} nu există în proiect.")

    if CSV_FILE.stat().st_size == 0:
        raise RuntimeError("weather_data.csv este gol. Rulează mai întâi generate_weather_csv.py.")

    df = pd.read_csv(CSV_FILE)
    df = normalize_dataframe(df)

    config = get_db_config_from_env()
    conn = connect_db(config)

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DATABASE() AS current_db, @@hostname AS host_name, @@port AS port_no")
            info = cursor.fetchone()
            print("CONNECTED_DB_INFO =", info)

            cursor.execute("TRUNCATE TABLE weather_data")

            insert_sql = """
                INSERT INTO weather_data (
                    city,
                    country,
                    entity,
                    continent,
                    date_record,
                    hour_record,
                    temperature_avg,
                    temperature_min,
                    temperature_max,
                    humidity,
                    precipitation,
                    wind_speed,
                    weather_code
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            inserted_rows = 0
            for _, row in df.iterrows():
                cursor.execute(
                    insert_sql,
                    (
                        row.get("city"),
                        row.get("country"),
                        row.get("entity"),
                        row.get("continent"),
                        row.get("date_record"),
                        None if pd.isna(row.get("hour_record")) else int(row.get("hour_record")),
                        None if pd.isna(row.get("temperature_avg")) else float(row.get("temperature_avg")),
                        None if pd.isna(row.get("temperature_min")) else float(row.get("temperature_min")),
                        None if pd.isna(row.get("temperature_max")) else float(row.get("temperature_max")),
                        None if pd.isna(row.get("humidity")) else float(row.get("humidity")),
                        None if pd.isna(row.get("precipitation")) else float(row.get("precipitation")),
                        None if pd.isna(row.get("wind_speed")) else float(row.get("wind_speed")),
                        None if pd.isna(row.get("weather_code")) else str(row.get("weather_code")),
                    ),
                )
                inserted_rows += 1

            cursor.execute("SELECT COUNT(*) AS total_rows FROM weather_data")
            total = cursor.fetchone()
            print("ROWS_AFTER_IMPORT =", total)
            print(f"Import terminat. Au fost încărcate {inserted_rows} rânduri în weather_data.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()