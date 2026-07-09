# AI DB Agent (NL → SQL) + Export Office

CLI tool pentru conectare la orice bază MySQL, generare SQL din limbaj natural folosind OpenAI,
executarea interogărilor în siguranță (doar SELECT) și export în Excel/Word/PowerPoint.

## Instalare
```bash
pip install -r requirements.txt
```

## Setare cheie OpenAI
Windows PowerShell:
```powershell
$env:OPENAI_API_KEY="CHEIA_TA"
```

## Rulare
```bash
python app.py
```

## Comenzi
- `/schema` - listează tabele
- `/excel` - export ultimele rezultate în .xlsx
- `/word` - export raport în .docx
- `/pptx` - export prezentare în .pptx
- `/reconnect` - reconectare la altă bază
- `exit` - ieșire

## Note de securitate
- Sunt permise doar interogări `SELECT`.
- Se blochează DDL/DML și multi-statement.
- Recomandat: user DB read-only pentru demo/licență.
