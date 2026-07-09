# 🌦️ WeatherAI – AI Weather Database Assistant

An AI-powered weather data assistant developed with **Python** and **Flask** that enables users to query weather information using natural language instead of writing SQL manually.

The application converts user questions into SQL queries, executes them safely, and displays the results through an intuitive interface with charts, multilingual support, and export capabilities.

---

# 🚀 Features

- 🤖 Natural Language → SQL conversion
- 🌦️ Weather database queries
- 📊 Interactive charts and statistics
- 🌍 Multilingual interface
- 💬 Conversation history
- 📥 Export to Excel, Word and PowerPoint
- 🔒 Safe SQL execution
- 📱 Responsive web interface

---

# 🛠 Technologies

- Python
- Flask
- HTML5
- CSS3
- JavaScript
- SQLite
- Jinja2
- OpenAI API

---

# 📂 Repository Structure

```
WeatherAI
│
├── README.md
│
└── Weather_AI
    ├── Screenshots
    │   ├── homepage.png
    │   ├── charts.png
    │   ├── query.png
    │   ├── Export.png
    │   └── language_german.png
    │
    └── Weather_AI
        ├── exporters/
        ├── webapp/
        ├── agent.py
        ├── cli_app.py
        ├── config.py
        ├── db.py
        ├── logger.py
        ├── requirements.txt
        └── README.md
```

---

# ⚙️ Installation

Clone the repository

```bash
git clone https://github.com/iftode/WeatherAI.git
```

Go to the project folder

```bash
cd WeatherAI/Weather_AI/Weather_AI
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

# 📸 Screenshots

## 🏠 Homepage

![Homepage](Weather_AI/Screenshots/homepage.png)

---

## 📊 Weather Statistics

![Charts](Weather_AI/Screenshots/charts.png)

---

## 🤖 AI Query

![Query](Weather_AI/Screenshots/query.png)

---

## 📤 Export Results

![Export](Weather_AI/Screenshots/Export.png)

---

## 🌍 German Language

![German](Weather_AI/Screenshots/language_german.png)

---

# 🔐 Security

- SQL validation
- Safe database execution
- Read-only query support
- Exception handling
- Input validation

---

# 📈 Future Improvements

- User authentication
- PostgreSQL support
- Docker deployment
- REST API
- AI model optimization
- Cloud database support
- Interactive dashboards

---

# 👨‍💻 Author

**Iftode Iulian-Cezar**

Python Developer

GitHub: https://github.com/iftode

---

# ⭐ Support

If you found this project useful, consider giving it a ⭐ on GitHub.
