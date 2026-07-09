import re

FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|replace)\b",
    re.IGNORECASE
)

def normalize_sql(sql: str) -> str:
    return sql.strip().strip(";").strip()

def is_safe_select(sql: str) -> tuple[bool, str]:
    s = normalize_sql(sql)

    if not s.lower().startswith("select"):
        return False, "Permis doar SELECT."

    if FORBIDDEN.search(s):
        return False, "Conține cuvinte interzise (DML/DDL)."

    # Interzicem mai multe statements
    if ";" in s:
        return False, "Nu sunt permise interogări multiple."

    return True, "OK"

def ensure_limit(sql: str, max_rows: int) -> str:
    """Adaugă LIMIT dacă nu există deja."""
    s = normalize_sql(sql)
    if re.search(r"\blimit\b", s, re.IGNORECASE):
        return s
    return f"{s} LIMIT {max_rows}"
