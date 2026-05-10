import sqlite3

def init_db():
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()
    # Таблица расписания
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT,
            lesson_num INTEGER,
            class_name TEXT,
            teacher_name TEXT,
            subject TEXT,
            room TEXT,
            difficulty INTEGER
        )
    ''')
    # Таблица избранного для бота
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER,
            class_name TEXT
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()