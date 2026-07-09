# 🌦️ WeatherAI – AI Weather Database Assistant

An AI-powered weather database assistant built with **Python** and **Flask** that enables users to query weather information using natural language instead of writing SQL manually.

The application automatically interprets user questions, generates SQL queries, validates them for safety, executes them on the weather database, and displays the results in an intuitive interface.

---

# 🚀 Features

- 🤖 AI-powered Natural Language to SQL conversion
- 🌍 Weather database search
- 📊 Interactive statistics and charts
- 📥 Export reports to:
  - Excel
  - Word
  - PowerPoint
- 💬 Conversation history
- 🌐 Multi-language interface
- 🔒 Safe SQL execution
- 📱 Responsive web interface

---

# 🛠️ Technologies

- Python
- Flask
- HTML5
- CSS3
- JavaScript
- SQLite
- OpenAI API
- Jinja2

---

# 📂 Project Structure

```
Weather_AI/
│
├── Screenshots/
│
├── Weather_AI/
│   ├── exporters/
│   ├── webapp/
│   ├── README.md
│   ├── agent.py
│   ├── cli_app.py
│   ├── config.py
│   ├── db.py
│   ├── logger.py
│   ├── safety.py
│   └── requirements.txt
│
├── .gitignore
└── .gitattributes
```

---

# ⚙️ Installation

Clone the repository

```bash
git clone https://github.com/iftode/WeatherAI.git
```

Navigate into the project

```bash
cd WeatherAI/Weather_AI
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the application

```bash
python agent.py
```

or

```bash
python cli_app.py
```

---

# 🎯 Main Capabilities

✔ Natural language weather queries

✔ Automatic SQL generation

✔ Secure SQL validation

✔ Weather statistics

✔ Interactive charts

✔ Conversation history

✔ Export to Excel, Word and PowerPoint

✔ Multi-language support

✔ Responsive user interface

---

# 📸 Screenshots

## Homepage

![Homepage](Weather_AI/Screenshots/homepage.png)

---

## Weather Statistics

![Statistics](Weather_AI/Screenshots/charts.png)

---

## AI Query

![Query](Weather_AI/Screenshots/query.png)

---

## Export Results

![Export](Weather_AI/Screenshots/Export.png)

---

## German Language Interface

![German](Weather_AI/Screenshots/language_german.png)

---

# 🔒 Security

The application includes several security mechanisms:

- SQL query validation
- Read-only query execution
- Input validation
- Exception handling
- Safe database connections

---

# 📈 Future Improvements

- User authentication
- Cloud database integration
- Docker deployment
- REST API
- PostgreSQL support
- AI model fine-tuning
- Interactive dashboards
- User profiles and saved conversations

---

# 👨‍💻 Author

**Iftode Iulian-Cezar**

Python Developer

GitHub: https://github.com/iftode

---

# ⭐ Support

If you like this project, consider giving it a ⭐ on GitHub.
