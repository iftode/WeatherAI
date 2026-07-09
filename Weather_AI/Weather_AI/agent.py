import os
import json
import getpass
from typing import Any, Dict
from openai import OpenAI


# ==========================================
# API KEY HANDLING (ask once per session)
# ==========================================

_cached_api_key = None


def get_openai_api_key() -> str:
    global _cached_api_key

    if _cached_api_key:
        return _cached_api_key

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        api_key = getpass.getpass("Introdu OPENAI_API_KEY (nu se afișează): ").strip()

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY lipsă.")

    _cached_api_key = api_key
    return api_key


# ==========================================
# NL → SQL
# ==========================================

def nl_to_sql(question: str, schema: Dict[str, Any], model: str) -> str:
    api_key = get_openai_api_key()

    client = OpenAI(api_key=api_key)

    system_prompt = (
        "Ești un asistent care generează SQL MySQL STRICT pentru citire.\n"
        "Reguli obligatorii:\n"
        "1) Generează DOAR o singură interogare SELECT (fără ; la final).\n"
        "2) Interzis: INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/TRUNCATE etc.\n"
        "3) Folosește doar tabele/coloane din schema furnizată.\n"
        "4) Dacă cererea e ambiguă, alege varianta cea mai sigură și explicită.\n"
        "5) Returnează EXCLUSIV JSON valid: {\"sql\": \"...\"}\n"
    )

    payload = {
        "question": question,
        "schema": schema
    }

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        temperature=0
    )

    content = (resp.choices[0].message.content or "").strip()

    try:
        data = json.loads(content)
        sql = data["sql"].strip()
    except Exception:
        raise RuntimeError(f"Răspuns invalid de la model: {content}")

    return sql
