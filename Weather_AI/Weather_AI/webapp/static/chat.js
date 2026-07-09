let chartInstance = null;

async function checkStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();

        const statusEl = document.getElementById('status');
        if (!statusEl) return;

        statusEl.innerText = data.connected
            ? `Conectat automat la baza de date: ${data.database}`
            : 'Nu există conexiune la baza de date';

        if (data.language) {
            const languageSelect = document.getElementById('languageSelect');
            if (languageSelect) {
                languageSelect.value = data.language;
            }
        }
    } catch (error) {
        const statusEl = document.getElementById('status');
        if (statusEl) {
            statusEl.innerText = 'Eroare la verificarea conexiunii.';
        }
    }
}

async function setLanguage() {
    try {
        const languageSelect = document.getElementById('languageSelect');
        if (!languageSelect) return;

        const language = languageSelect.value;

        await fetch('/api/set_language', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ language })
        });
    } catch (error) {
        console.error('Eroare la setarea limbii:', error);
    }
}

async function sendQuestion() {
    const questionEl = document.getElementById('question');
    const messageDiv = document.getElementById('message');
    const sqlBox = document.getElementById('sqlBox');

    if (!questionEl || !messageDiv || !sqlBox) return;

    const question = questionEl.value.trim();
    if (!question) return;

    messageDiv.innerText = 'Se procesează întrebarea...';
    sqlBox.innerText = '';

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: question })
        });

        const data = await res.json();

        if (!data.success) {
            messageDiv.innerText = data.message || 'Eroare';
            sqlBox.innerText = data.sql || '';
            clearResultsOnly();
            return;
        }

        messageDiv.innerText = data.message || '';
        sqlBox.innerText = data.sql || '';

        renderTable(data.columns || [], data.rows || []);

        if (data.statistics) {
            renderStatistics(data.statistics);
        } else {
            clearStatsOnly();
        }
    } catch (error) {
        messageDiv.innerText = 'A apărut o eroare la trimiterea întrebării.';
        sqlBox.innerText = '';
        clearResultsOnly();
    }
}

function renderTable(columns, rows) {
    const table = document.getElementById('resultTable');
    if (!table) return;

    table.innerHTML = '';

    if (!rows || rows.length === 0) {
        table.innerHTML = '<tr><td class="empty-text">Nu există rezultate.</td></tr>';
        return;
    }

    const thead = document.createElement('thead');
    const headRow = document.createElement('tr');

    columns.forEach(col => {
        const th = document.createElement('th');
        th.innerText = col;
        headRow.appendChild(th);
    });

    thead.appendChild(headRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');

    rows.forEach(row => {
        const tr = document.createElement('tr');

        columns.forEach(col => {
            const td = document.createElement('td');
            const value = row[col];
            td.innerText = value === null || value === undefined ? '' : value;
            tr.appendChild(td);
        });

        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
}

function renderStatistics(statistics) {
    const table = document.getElementById('statsTable');
    if (!table) return;

    table.innerHTML = '';

    if (!statistics || !statistics.stats || Object.keys(statistics.stats).length === 0) {
        table.innerHTML = '<tr><td class="empty-text">Nu există coloane numerice pentru statistici.</td></tr>';
        return;
    }

    const thead = document.createElement('thead');
    const headRow = document.createElement('tr');

    ['Coloană', 'Count', 'Min', 'Max', 'Average', 'Sum'].forEach(text => {
        const th = document.createElement('th');
        th.innerText = text;
        headRow.appendChild(th);
    });

    thead.appendChild(headRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');

    for (const [column, values] of Object.entries(statistics.stats)) {
        const tr = document.createElement('tr');

        const tdColumn = document.createElement('td');
        tdColumn.innerText = column;
        tr.appendChild(tdColumn);

        const tdCount = document.createElement('td');
        tdCount.innerText = values.count;
        tr.appendChild(tdCount);

        const tdMin = document.createElement('td');
        tdMin.innerText = values.min;
        tr.appendChild(tdMin);

        const tdMax = document.createElement('td');
        tdMax.innerText = values.max;
        tr.appendChild(tdMax);

        const tdAvg = document.createElement('td');
        tdAvg.innerText = values.avg;
        tr.appendChild(tdAvg);

        const tdSum = document.createElement('td');
        tdSum.innerText = values.sum;
        tr.appendChild(tdSum);

        tbody.appendChild(tr);
    }

    table.appendChild(tbody);
}

async function loadChart() {
    try {
        const res = await fetch('/api/chart_data');
        const data = await res.json();

        if (!data.success) {
            alert(data.message || 'Nu există date pentru grafic.');
            return;
        }

        const canvas = document.getElementById('chartCanvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        if (chartInstance) {
            chartInstance.destroy();
        }

        chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: data.value_column,
                    data: data.values,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    } catch (error) {
        alert('A apărut o eroare la generarea graficului.');
    }
}

async function loadStatistics() {
    try {
        const res = await fetch('/api/statistics');
        const data = await res.json();

        if (!data.success) {
            alert(data.message || 'Nu există date pentru statistici.');
            return;
        }

        renderStatistics(data.statistics);
    } catch (error) {
        alert('A apărut o eroare la generarea statisticilor.');
    }
}

async function clearHistory() {
    try {
        await fetch('/api/clear_history', { method: 'POST' });

        const messageDiv = document.getElementById('message');
        const sqlBox = document.getElementById('sqlBox');
        const questionEl = document.getElementById('question');

        if (messageDiv) messageDiv.innerText = '';
        if (sqlBox) sqlBox.innerText = '';
        if (questionEl) questionEl.value = '';

        clearResultsOnly();
        clearStatsOnly();

        if (chartInstance) {
            chartInstance.destroy();
            chartInstance = null;
        }
    } catch (error) {
        alert('A apărut o eroare la ștergerea istoricului.');
    }
}

function clearResultsOnly() {
    const resultTable = document.getElementById('resultTable');
    if (resultTable) {
        resultTable.innerHTML = '';
    }

    if (chartInstance) {
        chartInstance.destroy();
        chartInstance = null;
    }
}

function clearStatsOnly() {
    const statsTable = document.getElementById('statsTable');
    if (statsTable) {
        statsTable.innerHTML = '';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    checkStatus();

    const questionEl = document.getElementById('question');
    if (questionEl) {
        questionEl.addEventListener('keydown', function (event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendQuestion();
            }
        });
    }
});