import json
import re

from ai import explain_sql, validate_sql
from db import run_select, analyze_schema, format_schema_analysis
from prompts import (
    CLASSIFY_PROMPT,
    BUSINESS_SQL_PROMPT,
    METADATA_SQL_PROMPT,
    ANALYTICS_SQL_PROMPT,
    VALIDATE_SQL_PROMPT,
)


def detect_intent(user_question: str) -> str:
    q = user_question.lower().strip()

    schema_keywords = [
        "entitati",
        "entități",
        "entitate",
        "entitățile",
        "structura",
        "schema",
        "schemă",
        "relatii",
        "relații",
        "relatie",
        "relație",
        "tabele importante",
        "tabelele importante",
        "principalele tabele",
        "main entities",
        "main tables",
        "core entities",
        "cum este modelata",
        "cum este modelată",
        "cum sunt legate",
        "cum sunt conectate",
        "cum sunt relationate",
        "cum sunt relaționate",
        "ce relatii exista",
        "ce relații există",
        "descrie schema",
        "arata schema",
        "arată schema",
    ]

    for keyword in schema_keywords:
        if keyword in q:
            return "schema_analysis"

    return "sql_query"


def make_json_safe(obj):
    if isinstance(obj, set):
        return [make_json_safe(x) for x in obj]
    if isinstance(obj, tuple):
        return [make_json_safe(x) for x in obj]
    if isinstance(obj, list):
        return [make_json_safe(x) for x in obj]
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    return obj


class Orchestrator:
    def __init__(self, client, model, conn, schema, max_rows=50):
        self.client = client
        self.model = model
        self.conn = conn
        self.schema = schema
        self.max_rows = max_rows

    def _extract_json(self, text: str) -> dict:
        text = (text or "").strip()

        if text.startswith("```"):
            text = text.strip("`").strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return {}

        try:
            data = json.loads(match.group(0))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _strip_code_fence(self, text: str) -> str:
        text = (text or "").strip()

        if text.startswith("```"):
            text = text.strip("`").strip()
            lower_text = text.lower()

            if lower_text.startswith("sql"):
                text = text[3:].strip()
            elif lower_text.startswith("json"):
                text = text[4:].strip()

        return text.strip()

    def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        return (response.choices[0].message.content or "").strip()

    def _schema_to_text(self) -> str:
        lines = []

        for table_name in sorted(self.schema.keys()):
            cols = self.schema.get(table_name, [])
            col_parts = []

            for col in cols:
                col_name = col.get("name", "")
                col_type = col.get("type", "")
                col_parts.append(f"{col_name} ({col_type})")

            lines.append(f"{table_name}: " + ", ".join(col_parts))

        return "\n".join(lines)

    def _selected_language(self, language_instruction: str, question: str = "") -> str:
        li = (language_instruction or "").lower()
        q = question or ""

        if "exclusively in english" in li:
            return "en"
        if "ausschließlich auf deutsch" in li:
            return "de"
        if "exclusivement en français" in li or "exclusivement en francais" in li:
            return "fr"
        if "esclusivamente in italiano" in li:
            return "it"
        if "exclusivamente em português" in li or "exclusivamente em portugues" in li:
            return "pt"
        if "αποκλειστικά στα ελληνικά" in li:
            return "el"
        if "исключительно на русском" in li:
            return "ru"
        if "日本語でのみ回答" in (language_instruction or ""):
            return "ja"
        if "仅使用中文回答" in (language_instruction or "") or "僅使用中文回答" in (language_instruction or "") or "请仅使用中文回答" in (language_instruction or ""):
            return "zh"
        if "باللغة العربية فقط" in (language_instruction or ""):
            return "ar"

        if "aceeași limbă" in li or "same language" in li:
            if re.search(r"[а-яё]", q, re.IGNORECASE):
                return "ru"
            if re.search(r"[α-ωάέήίόύώϊϋΐΰ]", q, re.IGNORECASE):
                return "el"
            if re.search(r"[\u0600-\u06FF]", q):
                return "ar"
            if re.search(r"[\u3040-\u30ff]", q):
                return "ja"
            if re.search(r"[\u4e00-\u9fff]", q):
                return "zh"
            if any(x in q.lower() for x in ["show", "describe", "table", "tables", "schema", "database", "what", "which", "how many"]):
                return "en"
            return "ro"

        return "ro"

    def _translate_if_needed(self, text: str, language_instruction: str, question: str = "") -> str:
        if not text:
            return text

        lang = self._selected_language(language_instruction, question)
        if lang == "ro":
            return text

        lang_names = {
            "en": "English",
            "de": "German",
            "fr": "French",
            "it": "Italian",
            "pt": "Portuguese",
            "el": "Greek",
            "ru": "Russian",
            "ja": "Japanese",
            "zh": "Chinese",
            "ar": "Arabic",
        }

        system_prompt = f"""
You are a translator.
Translate the user's text faithfully into {lang_names[lang]}.
Preserve meaning, formatting, table names, SQL keywords, and technical identifiers.
Return ONLY the translated text.
"""
        return self._call_llm(system_prompt, text, temperature=0)

    def _rewrite_short_question(self, question: str) -> str:
        q = (question or "").strip().lower()

        rewrites = {
            "actori": "Arată actorii",
            "actori": "Arată actorii",
            "filme": "Arată filmele",
            "film": "Arată filmele",
            "clienți": "Arată clienții",
            "clienti": "Arată clienții",
            "categorii": "Arată categoriile de filme",
            "top 10 filme": "Arată top 10 filme după numărul de închirieri",
            "top filme": "Arată top filme după numărul de închirieri",
            "cei mai buni actori": "Arată actorii cu cele mai multe apariții în filme",
            "top actori": "Arată actorii cu cele mai multe apariții în filme",
        }

        return rewrites.get(q, question)

    def _normalize_schema_intent(self, question: str, classification: dict) -> str:
        q = (question or "").lower().strip()
        current_intent = (classification.get("intent") or "").strip().lower()

        conceptual_keywords = [
            "entitati",
            "entități",
            "entitate",
            "entitățile",
            "tabele importante",
            "tabelele importante",
            "principalele tabele",
            "main entities",
            "main tables",
            "core entities",
            "relatii",
            "relații",
            "relatie",
            "relație",
            "cum este modelata",
            "cum este modelată",
            "cum sunt legate",
            "cum sunt conectate",
            "cum sunt relationate",
            "cum sunt relaționate",
            "ce relatii exista",
            "ce relații există",
        ]

        if any(keyword in q for keyword in conceptual_keywords):
            return "conceptual_schema"

        if any(x in q for x in ["show me tables", "show tables", "list tables", "afiseaza tabele", "afișează tabele", "arata tabele", "arată tabele"]):
            return "show_tables"

        if any(x in q for x in ["describe table", "descrie tabel", "show table structure", "table schema"]):
            return "describe_table"

        if any(x in q for x in ["show schema", "describe schema", "arata schema", "arată schema", "schema overview"]):
            return "show_schema"

        if current_intent in [
            "show_tables",
            "list_tables",
            "describe_table",
            "show_schema",
            "describe_schema",
            "schema_overview",
            "conceptual_schema",
        ]:
            return current_intent

        return "show_schema"

    def _looks_like_metadata_question(self, question: str, classification: dict) -> bool:
        q = (question or "").lower().strip()
        intent = (classification.get("intent") or "").lower().strip()

        metadata_terms = [
            "primary key",
            "composite primary key",
            "foreign key",
            "foreign keys",
            "fk",
            "pk",
            "index",
            "indexes",
            "constraint",
            "constraints",
            "information_schema",
            "ddl",
            "nullable fk",
            "circular dependency",
            "dependencies",
            "drop table",
            "table size",
            "row count",
            "bridge table",
            "junction table",
            "composite keys",
            "composite key",
        ]

        metadata_intents = [
            "find_tables_with_composite_primary_keys",
            "list_tables_with_composite_primary_keys",
            "composite_primary_keys",
            "foreign_keys",
            "indexes",
            "constraints",
            "metadata",
            "table_dependencies",
            "table_size",
            "drop_impact",
        ]

        if intent in metadata_intents:
            return True

        return any(term in q for term in metadata_terms)

    def _classify(self, question: str) -> dict:
        system_prompt = """
You are a MySQL query classifier. Your job is to analyze user questions and classify them into categories.

CLASSIFICATION RULES:
1. kind: One of "schema", "data", "performance", "business", "clarify"
2. intent: Specific intent within the kind
3. params: Extracted parameters (table names, columns, filters, etc.)
4. learning_mode: true if the question sounds like a learning request, false otherwise
5. skill_level: "beginner", "intermediate", or "advanced" based on question complexity
6. confidence: 0.0 to 1.0 indicating classification confidence

KIND DEFINITIONS:
- schema: Questions about database structure
- data: Questions about data content (SELECT queries, counts, aggregations, filters, comparisons)
- performance: Questions about query optimization or analysis
- business: Questions about database purpose, domain, use cases, beneficiaries
- clarify: Unclear or ambiguous questions that need clarification

IMPORTANT:
- Questions like "what is the purpose of this database" => business
- Questions like "how many films are there" => data
- Questions like "show tables" => schema
- Questions like "optimize this query" => performance
- Questions about primary keys, foreign keys, indexes, constraints, dependencies, INFORMATION_SCHEMA => data

VERY IMPORTANT:
If the user writes only a short request or just a noun/table-like word such as:
- "actors"
- "actor"
- "films"
- "customers"
- "lista actori"
- "show actors"
- "cei mai buni actori"

then prefer:
kind: "data"
intent: "select_data"

Return ONLY valid JSON.
"""

        user_prompt = f"Classify this question: {question}"
        raw = self._call_llm(system_prompt, user_prompt, temperature=0)
        data = self._extract_json(raw)

        if data:
            return make_json_safe(data)

        return {
            "kind": "data",
            "intent": "select_data",
            "params": {},
            "learning_mode": False,
            "skill_level": "beginner",
            "confidence": 0.5,
        }

    def _classify_sql_mode(self, question: str) -> dict:
        schema_text = self._schema_to_text()

        user_prompt = f"""
Schema:
{schema_text}

User request:
{question}
"""

        raw = self._call_llm(CLASSIFY_PROMPT, user_prompt, temperature=0)
        data = self._extract_json(raw)

        if not data:
            return {
                "category": "business_sql",
                "needs_sql": True,
                "needs_information_schema": False,
                "needs_clarification": False,
                "reason": "fallback",
            }

        return make_json_safe(data)

    def _build_sql_prompt(self, category: str, language_instruction: str = "") -> str:
        base_prompt = BUSINESS_SQL_PROMPT
        if category == "metadata_ddl":
            base_prompt = METADATA_SQL_PROMPT
        elif category == "advanced_analytics":
            base_prompt = ANALYTICS_SQL_PROMPT

        if language_instruction:
            return f"{base_prompt}\n\nAdditional rule for all natural-language text: {language_instruction}"
        return base_prompt

    def _try_known_sql(self, question: str, category: str) -> str | None:
        q = (question or "").lower().strip()

        if category == "metadata_ddl":
            if "composite primary key" in q or "composite primary keys" in q:
                return """
SELECT tc.TABLE_NAME
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
  ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
 AND tc.TABLE_SCHEMA = kcu.TABLE_SCHEMA
 AND tc.TABLE_NAME = kcu.TABLE_NAME
WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
  AND tc.TABLE_SCHEMA = DATABASE()
GROUP BY tc.TABLE_NAME, tc.CONSTRAINT_NAME
HAVING COUNT(kcu.COLUMN_NAME) > 1
ORDER BY tc.TABLE_NAME
""".strip()

        return None

    def _generate_sql_by_prompt(self, question: str, history: list, category: str, language_instruction: str = "") -> str:
        known_sql = self._try_known_sql(question, category)
        if known_sql:
            if not known_sql.endswith(";"):
                known_sql += ";"
            return known_sql

        schema_text = self._schema_to_text()
        history_context = history[-6:] if history else []

        system_prompt = self._build_sql_prompt(category, language_instruction=language_instruction)
        user_prompt = f"""
Database schema:
{schema_text}

Conversation history:
{json.dumps(history_context, ensure_ascii=False)}

Generate SQL for:
{question}
"""

        sql = self._call_llm(system_prompt, user_prompt, temperature=0)
        sql = self._strip_code_fence(sql)

        if sql and not sql.endswith(";"):
            sql += ";"

        return sql

    def _validate_sql(self, question: str, sql: str) -> dict:
        schema_text = self._schema_to_text()

        user_prompt = f"""
Schema:
{schema_text}

User request:
{question}

Generated SQL:
{sql}
"""

        raw = self._call_llm(VALIDATE_SQL_PROMPT, user_prompt, temperature=0)
        data = self._extract_json(raw)

        if not data:
            return {
                "valid": True,
                "issues": [],
                "fixed_sql": sql,
            }

        fixed_sql = self._strip_code_fence(str(data.get("fixed_sql", "")).strip())
        if not fixed_sql:
            fixed_sql = sql

        if fixed_sql and not fixed_sql.endswith(";"):
            fixed_sql += ";"

        issues = data.get("issues", [])
        if not isinstance(issues, list):
            issues = [str(issues)]

        return make_json_safe(
            {
                "valid": bool(data.get("valid", True)),
                "issues": issues,
                "fixed_sql": fixed_sql,
            }
        )

    def _business_complexity(self, question: str) -> str:
        system_prompt = """
You are a query depth classifier. Determine if the user wants a brief general description
or a comprehensive detailed analysis.
"""

        user_prompt = f"""
You are analyzing a database purpose query to determine if the user wants:
- "general": A brief, high-level description of what the database is for (1-2 sentences)
- "in-depth": A comprehensive analysis with multiple aspects (detailed business analysis)

Question: "{question}"

Examples:
- "what is the intended use of the current database?" -> general
- "what is this database for?" -> general
- "what does this database do?" -> general
- "what is the purpose of this database?" -> general
- "give me a comprehensive analysis of this database" -> in-depth
- "analyze this database in detail" -> in-depth
- "provide a detailed business analysis" -> in-depth
- "comprehensive database purpose analysis" -> in-depth

Return ONLY: "general" or "in-depth"
"""

        out = self._call_llm(system_prompt, user_prompt, temperature=0).lower()
        return "in-depth" if out.startswith("in-depth") else "general"

    def _business_answer(self, question: str, complexity: str, history: list, language_instruction: str = "") -> str:
        table_names = list(self.schema.keys())
        history_context = history[-6:] if history else []

        language_line = language_instruction or "Răspunde exclusiv în limba română."

        if complexity == "general":
            system_prompt = f"""
You are a database analyst. Provide brief, high-level descriptions of database purpose.
Keep responses concise (1-3 sentences).
{language_line}
"""

            user_prompt = f"""
Based on the database schema, provide a brief, general description of what this database
is designed for.

Database: current connected database
Number of tables: {len(table_names)}
Table names: {", ".join(table_names)}

Conversation history:
{history_context}

Current question:
{question}

Return JSON format:
{{
  "database_purpose": "Brief description"
}}

IMPORTANT:
- Respond ONLY with valid JSON
- Keep the description brief and general
"""
        else:
            system_prompt = f"""
You are a database analyst. Provide a detailed business analysis based on the schema.
{language_line}
"""

            user_prompt = f"""
Analyze the following database in detail.

Database: current connected database
Number of tables: {len(table_names)}
Table names: {", ".join(table_names)}

Full schema:
{self.schema}

Conversation history:
{history_context}

Current question:
{question}

Return ONLY valid JSON in this format:
{{
  "database_purpose": [],
  "business_domain": [],
  "main_use_cases": [],
  "main_entities": [],
  "beneficiaries": []
}}
"""

        txt = self._call_llm(system_prompt, user_prompt, temperature=0.2)

        try:
            obj = json.loads(self._strip_code_fence(txt))
            obj = make_json_safe(obj)

            if complexity == "general":
                return obj.get("database_purpose", txt)

            parts = []

            if obj.get("database_purpose"):
                if isinstance(obj["database_purpose"], list):
                    parts.append("Scop: " + ", ".join(obj["database_purpose"]))
                else:
                    parts.append(f"Scop: {obj['database_purpose']}")

            if obj.get("business_domain"):
                if isinstance(obj["business_domain"], list):
                    parts.append("Domeniu: " + ", ".join(obj["business_domain"]))
                else:
                    parts.append(f"Domeniu: {obj['business_domain']}")

            if obj.get("main_use_cases"):
                parts.append("Cazuri de utilizare: " + ", ".join(obj["main_use_cases"]))

            if obj.get("main_entities"):
                parts.append("Entități principale: " + ", ".join(obj["main_entities"]))

            if obj.get("beneficiaries"):
                parts.append("Beneficiari: " + ", ".join(obj["beneficiaries"]))

            text = "\n".join(parts) if parts else txt
            return self._translate_if_needed(text, language_instruction, question)
        except Exception:
            return self._translate_if_needed(txt, language_instruction, question)

    def _schema_conceptual_answer(self, question: str, language_instruction: str = "") -> str:
        analysis = analyze_schema(self.schema)
        schema_summary = format_schema_analysis(analysis)
        language_line = language_instruction or "Răspunde exclusiv în limba română."

        system_prompt = f"""
You are a database analysis assistant.

The user asks conceptual questions about the database structure.
Do NOT generate SQL.
Do NOT blindly list all tables as main entities.

Rules:
- Main entities = core business objects
- Junction tables = many-to-many link tables
- Lookup tables = auxiliary/support/classification tables
- Be clear, practical, and concise
- {language_line}
"""

        user_prompt = f"""
User question:
{question}

Schema analysis:
{schema_summary}

Original schema:
{self.schema}

Instructions:
- Explain the answer conceptually
- If the user asks about main entities, do NOT list all tables
- Mention main entities separately from junction tables and lookup tables
- If the user asks about relationships, explain one-to-many / many-to-many when relevant
"""

        return self._call_llm(system_prompt, user_prompt, temperature=0.2)

    def _schema_answer(self, question: str, classification: dict, language_instruction: str = "") -> str:
        intent = self._normalize_schema_intent(question, classification)
        params = classification.get("params", {}) or {}
        q = question.lower().strip()

        conceptual_keywords = [
            "entitati",
            "entități",
            "entitate",
            "entitățile",
            "tabele importante",
            "tabelele importante",
            "principalele tabele",
            "main entities",
            "main tables",
            "core entities",
            "relatii",
            "relații",
            "relatie",
            "relație",
            "cum este modelata",
            "cum este modelată",
            "cum sunt legate",
            "cum sunt conectate",
            "cum sunt relationate",
            "cum sunt relaționate",
            "ce relatii exista",
            "ce relații există",
        ]

        if any(keyword in q for keyword in conceptual_keywords):
            return self._schema_conceptual_answer(question, language_instruction=language_instruction)

        if intent in ["list_tables", "show_tables", "tables", "show_me_tables"]:
            tables = sorted(self.schema.keys())
            base = "Tabelele din baza de date sunt: " + ", ".join(tables)
            return self._translate_if_needed(base, language_instruction, question)

        if intent in ["show_schema", "describe_schema", "schema_overview"]:
            lines = []
            for table_name in sorted(self.schema.keys()):
                cols = ", ".join(col["name"] for col in self.schema[table_name])
                lines.append(f"- {table_name}: {cols}")
            base = "\n".join(lines)
            return self._translate_if_needed(base, language_instruction, question)

        if intent in ["describe_table", "show_table_structure", "table_schema"]:
            table_name = params.get("table")
            if table_name and table_name in self.schema:
                cols = self.schema[table_name]
                base = f"Tabelul {table_name} are coloanele: " + ", ".join(
                    f"{c['name']} ({c['type']})" for c in cols
                )
                return self._translate_if_needed(base, language_instruction, question)

            base = "Nu am putut identifica tabelul cerut."
            return self._translate_if_needed(base, language_instruction, question)

        return self._schema_conceptual_answer(question, language_instruction=language_instruction)

    def _performance_answer(self, language_instruction: str = "", question: str = "") -> str:
        base = (
            "Întrebarea pare să fie despre performanță sau optimizare SQL. "
            "În această versiune, aplicația este concentrată pe clasificare, "
            "interogare de date și descrierea bazei de date."
        )
        return self._translate_if_needed(base, language_instruction, question)

    def _clarify_answer(self, language_instruction: str = "", question: str = "") -> str:
        base = (
            "Întrebarea nu este suficient de clară. "
            "Te rog reformulează mai specific. Exemple: "
            "«arată actorii», «câte filme există», «care este scopul bazei de date?»"
        )
        return self._translate_if_needed(base, language_instruction, question)

    def handle(self, question: str, history=None, language_instruction: str = ""):
        if not question or not question.strip():
            raise ValueError("Întrebarea este goală.")

        question = self._rewrite_short_question(question)

        if history is None or not isinstance(history, list):
            history = []

        history.append({"role": "user", "content": question})

        forced_intent = detect_intent(question)
        classification = make_json_safe(self._classify(question))

        if forced_intent == "schema_analysis":
            classification["kind"] = "schema"
            classification["intent"] = self._normalize_schema_intent(question, classification)

        kind = (classification.get("kind") or "data").strip().lower()

        if kind == "clarify":
            q = question.lower().strip()
            if len(q.split()) <= 3:
                kind = "data"
                classification["kind"] = "data"
                classification["intent"] = "select_data"

        if kind == "schema" and self._looks_like_metadata_question(question, classification):
            kind = "data"
            classification["kind"] = "data"

        if kind == "business":
            complexity = self._business_complexity(question)
            answer = self._business_answer(
                question=question,
                complexity=complexity,
                history=history,
                language_instruction=language_instruction,
            )

            history.append({"role": "assistant", "content": answer})

            return make_json_safe(
                {
                    "type": "business",
                    "classification": classification,
                    "complexity": complexity,
                    "sql": None,
                    "explanation": answer,
                    "answer": answer,
                    "columns": [],
                    "rows": [],
                }
            ), make_json_safe(history)

        if kind == "schema":
            answer = self._schema_answer(
                question,
                classification,
                language_instruction=language_instruction
            )

            history.append({"role": "assistant", "content": answer})

            return make_json_safe(
                {
                    "type": "schema",
                    "classification": classification,
                    "sql": None,
                    "explanation": answer,
                    "answer": answer,
                    "columns": [],
                    "rows": [],
                }
            ), make_json_safe(history)

        if kind == "performance":
            answer = self._performance_answer(language_instruction=language_instruction, question=question)

            history.append({"role": "assistant", "content": answer})

            return make_json_safe(
                {
                    "type": "performance",
                    "classification": classification,
                    "sql": None,
                    "explanation": answer,
                    "answer": answer,
                    "columns": [],
                    "rows": [],
                }
            ), make_json_safe(history)

        if kind == "clarify":
            answer = self._clarify_answer(language_instruction=language_instruction, question=question)

            history.append({"role": "assistant", "content": answer})

            return make_json_safe(
                {
                    "type": "clarify",
                    "classification": classification,
                    "sql": None,
                    "explanation": answer,
                    "answer": answer,
                    "columns": [],
                    "rows": [],
                }
            ), make_json_safe(history)

        sql_mode = self._classify_sql_mode(question)

        short_data_request = (
            kind == "data"
            and (classification.get("intent") or "").strip().lower() == "select_data"
            and len(question.strip().split()) <= 6
        )

        if (sql_mode.get("needs_clarification") or sql_mode.get("category") == "ambiguous_request") and not short_data_request:
            answer = self._clarify_answer(language_instruction=language_instruction, question=question)

            history.append({"role": "assistant", "content": answer})

            return make_json_safe(
                {
                    "type": "clarify",
                    "classification": classification,
                    "sql_mode": sql_mode,
                    "sql": None,
                    "explanation": answer,
                    "answer": answer,
                    "columns": [],
                    "rows": [],
                }
            ), make_json_safe(history)

        sql_category = sql_mode.get("category", "business_sql")
        sql = self._generate_sql_by_prompt(
            question=question,
            history=history,
            category=sql_category,
            language_instruction=language_instruction,
        )

        if not isinstance(sql, str) or not sql.strip():
            answer = self._translate_if_needed(
                "Nu am putut genera un SQL valid pentru această întrebare.",
                language_instruction,
                question
            )

            history.append({"role": "assistant", "content": answer})

            return make_json_safe(
                {
                    "type": "error",
                    "classification": classification,
                    "sql_mode": sql_mode,
                    "sql": None,
                    "explanation": answer,
                    "answer": answer,
                    "columns": [],
                    "rows": [],
                }
            ), make_json_safe(history)

        known_sql = self._try_known_sql(question, sql_category)
        if known_sql:
            validation = {
                "valid": True,
                "issues": [],
                "fixed_sql": sql,
            }
        else:
            validation = self._validate_sql(question, sql)

        final_sql = self._strip_code_fence(validation.get("fixed_sql", sql)).strip()

        if not final_sql:
            final_sql = sql

        if "limit" not in final_sql.lower():
            final_sql = final_sql.rstrip(";") + f" LIMIT {self.max_rows};"

        final_sql = validate_sql(final_sql)

        try:
            columns, rows = run_select(self.conn, final_sql, max_rows=self.max_rows)
        except Exception as exc:
            answer = self._translate_if_needed(
                f"Eroare la executarea interogării: {exc}",
                language_instruction,
                question
            )

            history.append({"role": "assistant", "content": answer})

            return make_json_safe(
                {
                    "type": "error",
                    "classification": classification,
                    "sql_mode": sql_mode,
                    "validation": validation,
                    "sql": final_sql,
                    "explanation": answer,
                    "answer": answer,
                    "columns": [],
                    "rows": [],
                }
            ), make_json_safe(history)

        explanation = explain_sql(
            client=self.client,
            model=self.model,
            question=question,
            sql=final_sql,
            language_instruction=language_instruction,
        )

        if isinstance(columns, (tuple, set)):
            columns = list(columns)

        clean_rows = []
        for row in rows:
            if isinstance(row, (tuple, set)):
                clean_rows.append(list(row))
            else:
                clean_rows.append(row)

        final_answer = explanation or self._translate_if_needed(
            f"Am executat SQL: {final_sql}",
            language_instruction,
            question
        )

        history.append({"role": "assistant", "content": final_answer})

        return make_json_safe(
            {
                "type": "data",
                "classification": classification,
                "sql_mode": sql_mode,
                "validation": validation,
                "sql": final_sql,
                "explanation": explanation,
                "answer": final_answer,
                "columns": columns or [],
                "rows": clean_rows or [],
            }
        ), make_json_safe(history)