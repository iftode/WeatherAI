import os
import json
from datetime import datetime
from typing import Any, Dict

def log_query(log_dir: str, item: Dict[str, Any]) -> None:
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, "queries.jsonl")

    row = {
        "time": datetime.now().isoformat(timespec="seconds"),
        **item
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

def safe_err(e: Exception) -> str:
    return f"{type(e).__name__}: {str(e)}"
