from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from jinja2 import Template
import sqlite3

app = FastAPI()

BASE_STYLE = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>

<style>
    :root { 
        --bg: #f2f4f7; 
        --text: #1a1a1a; 
        --card: #ffffff; 
        --accent: #007aff; 
        --nav-bg: rgba(255, 255, 255, 0.7);
        --border: rgba(0, 0, 0, 0.08);
        --radius: 28px;
    }
    [data-theme="dark"] { 
        --bg: #000000; 
        --text: #ffffff; 
        --card: #1c1c1e; 
        --accent: #0a84ff;
        --nav-bg: rgba(28, 28, 30, 0.8);
        --border: rgba(255, 255, 255, 0.1);
    }

    body { 
        background: var(--bg); 
        color: var(--text); 
        font-family: 'Inter', sans-serif; 
        transition: background 0.4s ease; 
        margin: 0;
        min-height: 100vh;
    }
    
    .container { 
        max-width: 1200px; 
        margin: 0 auto; 
        padding: 40px 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    /* Подложка для навигации */
    .nav-header {
        position: sticky;
        top: 20px;
        align-self: flex-start;
        z-index: 10;
        background: var(--nav-bg);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        padding: 8px 20px;
        border-radius: 100px;
        border: 1px solid var(--border);
        margin-bottom: 30px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .nav-link {
        color: var(--accent);
        text-decoration: none;
        font-weight: 700;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Огромные баблы на главной */
    .btn-giant { 
        padding: 45px 60px; 
        background: var(--card); 
        border: 1px solid var(--border);
        border-radius: var(--radius); 
        color: var(--text); 
        font-size: 26px; 
        font-weight: 800;
        text-decoration: none; 
        transition: all 0.25s cubic-bezier(0.2, 0, 0, 1);
        text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 15px;
    }
    
    .btn-giant:hover { 
        transform: translateY(-8px);
        border-color: var(--accent);
        box-shadow: 0 20px 40px rgba(0,0,0,0.12);
    }

    /* Ускоренная анимация */
    .fast-fade {
        animation: zoomIn;
        animation-duration: 0.35s; /* Быстрое появление */
    }

    .grid-selection { 
        display: grid; 
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); 
        gap: 15px; 
        width: 100%;
        margin-top: 20px; 
    }

    .small-bubble {
        padding: 20px;
        background: var(--card);
        border-radius: 20px;
        text-decoration: none;
        color: var(--text);
        font-weight: 600;
        text-align: center;
        border: 1px solid var(--border);
        transition: 0.2s;
    }

    .small-bubble:hover {
        background: var(--accent);
        color: white;
        border-color: var(--accent);
        transform: scale(1.05);
    }

    .schedule-grid { 
        display: grid; 
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); 
        gap: 20px; 
        width: 100%; 
    }

    .day-card { 
        background: var(--card); 
        padding: 25px; 
        border-radius: var(--radius); 
        border: 1px solid var(--border);
    }

    .day-title { 
        font-weight: 800; 
        font-size: 20px;
        color: var(--accent); 
        margin-bottom: 15px;
    }

    .lesson { 
        padding: 15px;
        background: rgba(128, 128, 128, 0.05);
        border-radius: 18px;
        margin-bottom: 12px;
    }

    .theme-toggle { 
        position: fixed; bottom: 30px; right: 30px; 
        cursor: pointer; padding: 15px; border-radius: 50%; 
        border: 1px solid var(--border); background: var(--card); color: var(--text);
        font-size: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        z-index: 100;
    }
</style>

<script>
    function toggleTheme() {
        const b = document.body;
        const theme = b.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        b.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }
    document.addEventListener('DOMContentLoaded', () => {
        document.body.setAttribute('data-theme', localStorage.getItem('theme') || 'light');
    });
</script>
<button class="theme-toggle" onclick="toggleTheme()">🌓</button>
"""

INDEX_HTML = BASE_STYLE + """
<div class="container">
    <div class="animate__animated animate__fadeInDown animate__faster" style="text-align: center; margin-top: 5vh;">
        <h1 style="font-size: 3.5rem; font-weight: 800; margin-bottom: 5px; letter-spacing: -2px;">Привет! 👋</h1>
        <p style="font-size: 1.1rem; opacity: 0.6; margin-bottom: 40px;">Выбери раздел ниже</p>
    </div>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; width: 100%; max-width: 700px;">
        <a href="/select/class" class="btn-giant fast-fade">
            <span style="font-size: 45px;">👨‍🎓</span>
            Классы
        </a>
        <a href="/select/teacher" class="btn-giant fast-fade" style="animation-delay: 0.05s;">
            <span style="font-size: 45px;">👩‍🏫</span>
            Учителя
        </a>
    </div>
</div>
"""

SELECT_HTML = BASE_STYLE + """
<div class="container animate__animated animate__fadeIn animate__faster">
    <nav class="nav-header">
        <a href="/" class="nav-link">🏠 Главная</a>
    </nav>
    
    <h1 style="align-self: flex-start; font-weight: 800; letter-spacing: -1px;">Выберите {{ type_name }}</h1>
    <div class="grid-selection">
        {% for item in items %}
        <a href="/view/{{ type_id }}/{{ item }}" class="small-bubble">{{ item }}</a>
        {% endfor %}
    </div>
</div>
"""

SCHEDULE_HTML = BASE_STYLE + """
<div class="container animate__animated animate__fadeIn animate__faster">
    <nav class="nav-header">
        <a href="/" class="nav-link">🏠 Главная</a>
        <span style="opacity: 0.2">|</span>
        <a href="/select/{{ type_id }}" class="nav-link">⬅ Назад</a>
    </nav>
    
    <h1 style="text-align: center; margin-bottom: 30px; font-weight: 800; letter-spacing: -1px;">
        Расписание: <span style="color: var(--accent);">{{ target }}</span>
    </h1>
    
    <div class="schedule-grid">
        {% for day in ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница'] %}
        <div class="day-card animate__animated animate__fadeInUp animate__faster" style="animation-delay: {{ loop.index0 * 0.05 }}s">
            <div class="day-title">{{ day }}</div>
            {% for l in lessons if l[1] == day %}
                <div class="lesson">
                    <div style="font-weight: 800; font-size: 17px; margin-bottom: 5px;">{{ l[2] }}. {{ l[5] }}</div>
                    <div style="opacity: 0.6; font-size: 13px; font-weight: 600;">
                        📍 Кабинет {{ l[6] }} <br>
                        👤 {{ l[4] if type_id == 'class' else l[3] }}
                    </div>
                </div>
            {% else %}
                <div style="text-align: center; padding: 30px; opacity: 0.2; font-weight: 600;">Пусто</div>
            {% endfor %}
        </div>
        {% endfor %}
    </div>
</div>
"""

# Функции FastAPI те же самые

# --- РОУТЫ (Остаются прежними) ---

def get_db():
    return sqlite3.connect('school.db')

@app.get("/", response_class=HTMLResponse)
async def index():
    return Template(INDEX_HTML).render()

@app.get("/select/{mode}", response_class=HTMLResponse)
async def select(mode: str):
    conn = get_db()
    cur = conn.cursor()
    if mode == "class":
        cur.execute("SELECT DISTINCT class_name FROM schedule ORDER BY length(class_name), class_name")
        type_name, type_id = "класс", "class"
    else:
        cur.execute("SELECT DISTINCT teacher_name FROM schedule ORDER BY teacher_name")
        type_name, type_id = "учителя", "teacher"
    
    items = [row[0] for row in cur.fetchall()]
    return Template(SELECT_HTML).render(items=items, type_name=type_name, type_id=type_id)

@app.get("/view/{mode}/{name}", response_class=HTMLResponse)
async def view_schedule(mode: str, name: str):
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT * FROM schedule WHERE class_name=? ORDER BY lesson_num" if mode == "class" else "SELECT * FROM schedule WHERE teacher_name=? ORDER BY lesson_num"
    cur.execute(query, (name,))
    lessons = cur.fetchall()
    return Template(SCHEDULE_HTML).render(target=name, lessons=lessons, type_id=mode)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)