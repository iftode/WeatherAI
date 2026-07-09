import re
from openai import OpenAI


FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|replace|grant|revoke)\b",
    re.I
)


def validate_sql(sql: str) -> str:
    sql = (sql or "").strip()

    if not sql:
        raise ValueError("SQL gol.")

    if sql.startswith("```"):
        sql = sql.strip("`").strip()
        if sql.lower().startswith("sql"):
            sql = sql[3:].strip()

    sql = sql.strip().strip("`").strip()

    if not sql:
        raise ValueError("SQL gol.")

    if FORBIDDEN.search(sql):
        raise ValueError("SQL conține operații interzise.")

    normalized = sql.lower().lstrip()

    if not (normalized.startswith("select") or normalized.startswith("with")):
        raise ValueError("Doar SELECT este permis.")

    if ";" in sql.strip()[:-1]:
        raise ValueError("Nu sunt permise multiple interogări.")

    if not sql.endswith(";"):
        sql += ";"

    return sql


def explain_sql(
    client: OpenAI,
    model: str,
    question: str,
    sql: str,
    language_instruction: str = "Răspunde exclusiv în limba română."
) -> str:
    system_prompt = f"""
You are a database teacher.

Explain SQL queries in very simple language.
Keep explanations short and clear.
Use only 1 sentence.
{language_instruction}
"""

    user_prompt = f"""
User question:
{question}

SQL query:
{sql}

Explain what this SQL query does.
"""

    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    return (response.choices[0].message.content or "").strip()
from openai import OpenAI
from prompts import CLASSIFY_WEATHER_PROMPT, SUMMARIZE_RESULTS_PROMPT

client = OpenAI()


def classify_weather_question(question: str) -> str:
    prompt = CLASSIFY_WEATHER_PROMPT.format(question=question)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Răspunde doar cu categoria cerută."},
            {"role": "user", "content": prompt},
        ],
        temperature=0
    )

    result = response.choices[0].message.content.strip().lower()

    if result not in ["weather_query", "conversation_history", "unrelated"]:
        return "unrelated"

    return result


def summarize_sql_results(question: str, csv_data: str) -> str:
    if not csv_data or csv_data.strip() == "":
        return "Nu au fost găsite rezultate pentru această întrebare."

    prompt = SUMMARIZE_RESULTS_PROMPT.format(
        question=question,
        csv_data=csv_data[:6000]
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Rezumi rezultatele meteo într-o singură frază."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()