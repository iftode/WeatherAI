import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("Cheia OpenAI nu a fost găsită în .env")
import getpass
from datetime import datetime

from config import DEFAULT_OPENAI_MODEL, DEFAULT_MAX_ROWS, EXPORT_DIR, LOG_DIR
from db import DBConfig, connect, extract_schema, run_query, ping
from agent import nl_to_sql
from safety import is_safe_select, ensure_limit
from logger import log_query, safe_err
from exporters import export_to_excel, export_to_word, export_to_pptx

def prompt_db_config() -> DBConfig:
    print("\n=== Configurare MySQL (orice DB) ===")
    host = input("Host [localhost]: ").strip() or "localhost"
    port_str = input("Port [3306]: ").strip() or "3306"
    try:
        port = int(port_str)
    except ValueError:
        port = 3306

    user = input("User [root]: ").strip() or "root"
    password = getpass.getpass("Password: ")
    database = input("Database: ").strip()

    return DBConfig(host=host, port=port, user=user, password=password, database=database)

def print_help():
    print("\nComenzi:")
    print("  /help                 - arată comenzi")
    print("  /schema               - arată tabelele detectate")
    print("  /excel                - export ultimele rezultate în Excel")
    print("  /word                 - export ultimele rezultate în Word (raport)")
    print("  /pptx                 - export ultimele rezultate în PowerPoint")
    print("  /reconnect            - reintroduci conexiunea DB")
    print("  exit                  - ieșire\n")

def main():
    print("=== AI DB Agent (CLI) ===")
    print("Cheia OpenAI este citită automat din fișierul .env.")
    print_help()

    last = {
        "question": None,
        "sql": None,
        "rows": None,
    }

    schema_cache = None
    cfg = prompt_db_config()

    while True:
        try:
            conn = connect(cfg)
            if not ping(conn):
                raise RuntimeError("Nu pot face ping la DB.")

            schema_cache = extract_schema(conn, cfg.database)
            print(f"\n✅ Conectat la DB '{cfg.database}'. Tabele detectate: {len(schema_cache)}")
            break
        except Exception as e:
            print("❌ Conectare eșuată:", safe_err(e))
            retry = input("Mai încerci? (y/n): ").strip().lower()
            if retry != "y":
                return
            cfg = prompt_db_config()

    while True:
        cmd = input("\nTu> ").strip()

        if not cmd:
            continue

        if cmd.lower() == "exit":
            print("Bye.")
            return

        if cmd == "/help":
            print_help()
            continue

        if cmd == "/schema":
            if not schema_cache:
                print("Schema nu e disponibilă.")
            else:
                for t in schema_cache.keys():
                    print(" -", t)
            continue

        if cmd == "/reconnect":
            try:
                conn.close()
            except:
                pass
            cfg = prompt_db_config()
            try:
                conn = connect(cfg)
                schema_cache = extract_schema(conn, cfg.database)
                print(f"✅ Conectat la DB '{cfg.database}'.")
            except Exception as e:
                print("❌ Conectare eșuată:", safe_err(e))
            continue

        # export commands
        if cmd in ("/excel", "/word", "/pptx"):
            if not last["rows"]:
                print("Nu există rezultate de exportat încă.")
                continue

            if cmd == "/excel":
                path = export_to_excel(last["rows"], EXPORT_DIR, title="Results")
                print("✅ Export Excel:", path)
            elif cmd == "/word":
                path = export_to_word(last["rows"], EXPORT_DIR, last["question"], last["sql"])
                print("✅ Export Word:", path)
            else:
                path = export_to_pptx(last["rows"], EXPORT_DIR, last["question"], last["sql"])
                print("✅ Export PPTX:", path)
            continue

        # Otherwise treat input as a natural-language question
        question = cmd
        started = datetime.now()

        try:
            sql = nl_to_sql(question, schema_cache, model=DEFAULT_OPENAI_MODEL)
            ok, reason = is_safe_select(sql)
            if not ok:
                print("⛔ SQL blocat:", reason)
                print("SQL propus:", sql)
                log_query(LOG_DIR, {
                    "status": "blocked",
                    "reason": reason,
                    "question": question,
                    "sql": sql,
                })
                continue

            sql_limited = ensure_limit(sql, DEFAULT_MAX_ROWS)
            rows = run_query(conn, sql_limited)

            elapsed = (datetime.now() - started).total_seconds()

            print("\n--- SQL generat ---")
            print(sql_limited)
            print(f"--- Rezultate: {len(rows)} rânduri (max {DEFAULT_MAX_ROWS}) | {elapsed:.2f}s ---")
            for r in rows[:min(len(rows), 20)]:
                print(r)
            if len(rows) > 20:
                print("... (afișez doar primele 20 rânduri)")

            last.update({"question": question, "sql": sql_limited, "rows": rows})

            log_query(LOG_DIR, {
                "status": "ok",
                "question": question,
                "sql": sql_limited,
                "rows": len(rows),
                "seconds": elapsed
            })

            print("\nTip: /excel /word /pptx pentru export.")

        except Exception as e:
            print("❌ Eroare:", safe_err(e))
            log_query(LOG_DIR, {
                "status": "error",
                "question": question,
                "error": safe_err(e)
            })

if __name__ == "__main__":
    main()
