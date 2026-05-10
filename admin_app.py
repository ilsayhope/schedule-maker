import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QStackedWidget, QListWidget, QLineEdit, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, 
                             QSpinBox, QMessageBox, QTreeWidget, QTreeWidgetItem, QDialog, QFormLayout)
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect
import requests
import sqlite3

# --- БАЗА ДАННЫХ (JSON Storage) ---
DB_FILE = "school"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "teachers": [], "rooms": [], "subjects": {}, "profiles": {}, 
        "classes": {}, "limits": {}, "schedule": {}
    }

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- ГЛАВНОЕ ОКНО ---
class MinimalAdmin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("School Admin Panel")
        self.resize(1200, 800)
        self.db = load_db()
        self.current_class = None
        
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Боковая панель (Sidebar) ---
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setObjectName("Sidebar")
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(10, 20, 10, 20)

        title = QLabel("SCHOOL OS")
        title.setObjectName("Logo")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(title)
        side_layout.addSpacing(30)

        self.tabs = QStackedWidget()
        self.nav_btns = []

        # Добавляем кнопку в самый низ бокового меню
        side_layout.addStretch() # Это отодвинет кнопку вниз
        
        self.btn_sync = QPushButton("🚀 ОТПРАВИТЬ НА СЕРВЕР")
        # Если хочешь, чтобы она выделялась стилем:
        self.btn_sync.setStyleSheet("background-color: #34c759; color: black; font-weight: bold; padding: 15px;")
        
        # Привязываем действие
        self.btn_sync.clicked.connect(self.upload_to_server)
        
        side_layout.addWidget(self.btn_sync)
        
        # Настройка вкладок
        tab_info = [
            ("📅 Расписание", self.create_schedule_tab()),
            ("👤 Учителя", self.create_list_tab("teachers", "ФИО учителя...")),
            ("🚪 Кабинеты", self.create_rooms_tab()),
            ("📚 Предметы", self.create_subjects_tab()),
            ("🔗 Профили", self.create_profiles_tab())
        ]

        for i, (name, widget) in enumerate(tab_info):
            btn = QPushButton(name)
            btn.setObjectName("NavBtn")
            btn.clicked.connect(lambda _, idx=i: self.switch_tab(idx))
            self.nav_btns.append(btn)
            side_layout.addWidget(btn)
            self.tabs.addWidget(widget)

        side_layout.addStretch()

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.tabs)
        self.switch_tab(0) # Старт с Расписания

    def upload_to_server(self):
        # URL твоего Flask-сервера
        url = "http://IP_ТВОЕГО_СЕРВЕРА:5000/upload" 
        
        try:
            # Сначала сохраняем все последние изменения в файл
            save_db(self.db) 
            
            # Отправляем файл на сервер
            with open(DB_FILE, 'rb') as f:
                files = {'file': (DB_FILE, f)}
                response = requests.post(url, files=files, timeout=10)
            
            if response.status_code == 200:
                QMessageBox.information(self, "Успех", "Данные успешно отправлены на сервер!")
            else:
                QMessageBox.warning(self, "Ошибка", f"Сервер ответил ошибкой: {response.status_code}")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сети", f"Не удалось связаться с сервером:\n{str(e)}")

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; color: #ffffff; font-family: 'Segoe UI', Arial; }
            #Sidebar { background-color: #1e1e1e; border-right: 1px solid #2d2d2d; }
            #Logo { font-size: 20px; font-weight: bold; color: #4dabf7; letter-spacing: 2px; }
            #NavBtn { text-align: left; padding: 12px 20px; font-size: 14px; border: none; border-radius: 8px; background: transparent; color: #a0a0a0; }
            #NavBtn:hover { background-color: #2d2d2d; color: #ffffff; }
            #NavBtn[active="true"] { background-color: #4dabf7; color: #121212; font-weight: bold; }
            QStackedWidget { background-color: #121212; }
            QLineEdit, QSpinBox, QComboBox { background-color: #1e1e1e; border: 1px solid #333; padding: 10px; border-radius: 6px; color: white; }
            QPushButton { background-color: #2d2d2d; border: none; padding: 10px 15px; border-radius: 6px; font-weight: bold; color: white; }
            QPushButton:hover { background-color: #3d3d3d; }
            QListWidget, QTreeWidget, QTableWidget { background-color: #1e1e1e; border: 1px solid #2d2d2d; border-radius: 8px; color: white; outline: none; }
            QTableWidget::item { padding: 5px; }
            QHeaderView::section { background-color: #2d2d2d; color: #a0a0a0; border: none; padding: 5px; font-weight: bold; }
        """)

    def switch_tab(self, index):
        # Анимация переключения
        current = self.tabs.currentWidget()
        next_w = self.tabs.widget(index)
        
        for i, btn in enumerate(self.nav_btns):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn); btn.style().polish(btn)

        self.tabs.setCurrentIndex(index)
        
        # Обновляем комбобоксы в расписании и профилях при переходе
        if index in [0, 4]: 
            self.refresh_profile_combos()

    # --- ВКЛАДКА 2: УЧИТЕЛЯ (Универсальный список) ---
    def create_list_tab(self, db_key, placeholder):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(40, 40, 40, 40)
        l.addWidget(QLabel("Управление", styleSheet="font-size: 24px; font-weight: bold;"))
        
        inp_layout = QHBoxLayout()
        inp = QLineEdit(); inp.setPlaceholderText(placeholder)
        btn = QPushButton("Добавить")
        inp_layout.addWidget(inp); inp_layout.addWidget(btn)
        
        lst = QListWidget()
        lst.addItems(self.db[db_key])
        
        def add_item():
            val = inp.text().strip()
            if val and val not in self.db[db_key]:
                self.db[db_key].append(val)
                lst.addItem(val)
                save_db(self.db)
                inp.clear()

        btn.clicked.connect(add_item)
        l.addLayout(inp_layout); l.addWidget(lst)
        return w

    # --- ВКЛАДКА 3: КАБИНЕТЫ (С парсером промежутков) ---
    def create_rooms_tab(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(40, 40, 40, 40)
        l.addWidget(QLabel("Кабинеты (можно вводить '1-30', 'Актовый зал')", styleSheet="font-size: 24px; font-weight: bold;"))
        
        inp_layout = QHBoxLayout()
        inp = QLineEdit(); inp.setPlaceholderText("Например: 1-10, 15, Спортзал")
        btn = QPushButton("Добавить")
        inp_layout.addWidget(inp); inp_layout.addWidget(btn)
        
        lst = QListWidget()
        lst.addItems(self.db["rooms"])
        
        def add_rooms():
            text = inp.text().strip()
            for part in text.split(','):
                part = part.strip()
                if '-' in part and part.replace('-', '').isdigit():
                    start, end = map(int, part.split('-'))
                    new_rooms = [str(i) for i in range(start, end + 1)]
                else:
                    new_rooms = [part]
                
                for r in new_rooms:
                    if r and r not in self.db["rooms"]:
                        self.db["rooms"].append(r)
                        lst.addItem(r)
            save_db(self.db)
            inp.clear()

        btn.clicked.connect(add_rooms)
        l.addLayout(inp_layout); l.addWidget(lst)
        return w

    # --- ВКЛАДКА 4: ПРЕДМЕТЫ (С кэфом) ---
    def create_subjects_tab(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(40, 40, 40, 40)
        l.addWidget(QLabel("Предметы и Сложность", styleSheet="font-size: 24px; font-weight: bold;"))
        
        inp_layout = QHBoxLayout()
        inp_name = QLineEdit(); inp_name.setPlaceholderText("Название...")
        inp_diff = QSpinBox(); inp_diff.setRange(1, 15); inp_diff.setPrefix("Кэф: ")
        btn = QPushButton("Добавить")
        inp_layout.addWidget(inp_name); inp_layout.addWidget(inp_diff); inp_layout.addWidget(btn)
        
        lst = QListWidget()
        for k, v in self.db["subjects"].items(): lst.addItem(f"{k} (Кэф: {v})")
        
        def add_sub():
            name = inp_name.text().strip()
            if name:
                self.db["subjects"][name] = inp_diff.value()
                lst.addItem(f"{name} (Кэф: {inp_diff.value()})")
                save_db(self.db)
                inp_name.clear()

        btn.clicked.connect(add_sub)
        l.addLayout(inp_layout); l.addWidget(lst)
        return w

    # --- ВКЛАДКА 5: ПРОФИЛИ ---
    def create_profiles_tab(self):
        self.prof_w = QWidget(); l = QVBoxLayout(self.prof_w); l.setContentsMargins(40, 40, 40, 40)
        l.addWidget(QLabel("Создание связки", styleSheet="font-size: 24px; font-weight: bold;"))
        
        form = QHBoxLayout()
        self.cb_tch = QComboBox(); self.cb_sub = QComboBox(); self.cb_rm = QComboBox()
        btn = QPushButton("Создать Профиль")
        btn.setStyleSheet("background-color: #4dabf7; color: black;")
        
        for cb in (self.cb_tch, self.cb_sub, self.cb_rm): form.addWidget(cb)
        form.addWidget(btn)
        
        self.prof_lst = QListWidget()
        for p in self.db["profiles"]: self.prof_lst.addItem(p)
        
        def save_profile():
            t, s, r = self.cb_tch.currentText(), self.cb_sub.currentText(), self.cb_rm.currentText()
            if t and s and r:
                p_name = f"{s} | {t} | каб.{r}"
                self.db["profiles"][p_name] = {"t": t, "s": s, "r": r}
                self.prof_lst.addItem(p_name)
                save_db(self.db)

        btn.clicked.connect(save_profile)
        l.addLayout(form); l.addWidget(self.prof_lst)
        return self.prof_w

    def refresh_profile_combos(self):
        for cb, key in [(self.cb_tch, "teachers"), (self.cb_sub, "subjects"), (self.cb_rm, "rooms")]:
            cb.clear()
            items = list(self.db[key].keys()) if key == "subjects" else self.db[key]
            cb.addItems(items)

    # --- ВКЛАДКА 1: РАСПИСАНИЕ ---
    def create_schedule_tab(self):
        w = QWidget(); main_l = QHBoxLayout(w)
        
        # Левая панель: Классы (Дерево параллелей)
        left_panel = QWidget(); left_panel.setFixedWidth(200)
        ll = QVBoxLayout(left_panel); ll.setContentsMargins(10,10,10,10)
        
        add_class_layout = QHBoxLayout()
        self.inp_class = QLineEdit(); self.inp_class.setPlaceholderText("Напр. 5А")
        btn_add_c = QPushButton("+")
        add_class_layout.addWidget(self.inp_class); add_class_layout.addWidget(btn_add_c)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self.select_class)
        self.refresh_tree()
        
        btn_add_c.clicked.connect(self.add_class)
        ll.addLayout(add_class_layout); ll.addWidget(self.tree)

        # Правая панель: Таблица
        right_panel = QWidget(); rl = QVBoxLayout(right_panel)
        self.lbl_class = QLabel("Выберите класс"); self.lbl_class.setStyleSheet("font-size: 20px; font-weight: bold;")
        
        # Лимиты сложности по дням
        limit_layout = QHBoxLayout()
        self.day_limits = {}
        for day in ["Пн", "Вт", "Ср", "Чт", "Пт"]:
            limit_layout.addWidget(QLabel(day))
            sb = QSpinBox(); sb.setRange(0, 100); sb.setValue(30)
            sb.valueChanged.connect(lambda v, d=day: self.save_limit(d, v))
            self.day_limits[day] = sb
            limit_layout.addWidget(sb)
            
        self.table = QTableWidget(8, 5)
        self.table.setHorizontalHeaderLabels(["Пн", "Вт", "Ср", "Чт", "Пт"])
        self.table.setVerticalHeaderLabels([str(i) for i in range(1, 9)])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.cellDoubleClicked.connect(self.edit_cell)

        rl.addWidget(self.lbl_class); rl.addLayout(limit_layout); rl.addWidget(self.table)
        main_l.addWidget(left_panel); main_l.addWidget(right_panel)
        return w

    def add_class(self):
        c_name = self.inp_class.text().strip().upper()
        if c_name:
            parallel = ''.join(filter(str.isdigit, c_name))
            if parallel not in self.db["classes"]: self.db["classes"][parallel] = []
            if c_name not in self.db["classes"][parallel]:
                self.db["classes"][parallel].append(c_name)
                save_db(self.db)
                self.refresh_tree()
        self.inp_class.clear()

    def refresh_tree(self):
        self.tree.clear()
        for par in sorted(self.db["classes"].keys(), key=int):
            root = QTreeWidgetItem([f"{par} параллель"])
            for c in sorted(self.db["classes"][par]): root.addChild(QTreeWidgetItem([c]))
            self.tree.addTopLevelItem(root)
            root.setExpanded(True)

    def select_class(self, item):
        if item.childCount() == 0: # Это конкретный класс
            self.current_class = item.text(0)
            self.lbl_class.setText(f"Расписание: {self.current_class}")
            
            # Загружаем лимиты
            limits = self.db.get("limits", {}).get(self.current_class, {})
            for d, sb in self.day_limits.items(): sb.setValue(limits.get(d, 30))
            
            self.render_table()

    def save_limit(self, day, val):
        if self.current_class:
            if "limits" not in self.db: self.db["limits"] = {}
            if self.current_class not in self.db["limits"]: self.db["limits"][self.current_class] = {}
            self.db["limits"][self.current_class][day] = val
            save_db(self.db)

    def render_table(self):
        self.table.clearContents()
        if self.current_class not in self.db["schedule"]: return
        
        days = ["Пн", "Вт", "Ср", "Чт", "Пт"]
        for col, day in enumerate(days):
            day_data = self.db["schedule"][self.current_class].get(day, {})
            day_score = 0
            
            for row in range(8):
                lesson = day_data.get(str(row))
                if lesson:
                    t, s, r = lesson["t"], lesson["s"], lesson["r"]
                    item = QTableWidgetItem(f"{s}\n{t}\nкаб. {r}")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(row, col, item)
                    day_score += self.db["subjects"].get(s, 0)
            
            # Подсветка перегруза
            limit = self.day_limits[day].value()
            header_item = self.table.horizontalHeaderItem(col)
            if header_item:
                color = "#ff4444" if day_score > limit else "#a0a0a0"
                header_item.setForeground(Qt.GlobalColor.white if day_score > limit else Qt.GlobalColor.lightGray)

    # --- ЛОГИКА РЕДАКТИРОВАНИЯ И КОНФЛИКТОВ ---
    def edit_cell(self, row, col):
        if not self.current_class: return
        days = ["Пн", "Вт", "Ср", "Чт", "Пт"]
        day = days[col]
        
        diag = QDialog(self)
        diag.setWindowTitle(f"Урок {row+1}, {day}")
        fl = QFormLayout(diag)
        
        # Режим 1: Профиль
        cb_prof = QComboBox(); cb_prof.addItems(["- Выбрать профиль -"] + list(self.db["profiles"].keys()))
        
        # Режим 2: Ручной ввод
        cb_t = QComboBox(); cb_t.addItems(self.db["teachers"])
        cb_s = QComboBox(); cb_s.addItems(self.db["subjects"].keys())
        cb_r = QComboBox(); cb_r.addItems(self.db["rooms"])
        
        btn = QPushButton("Сохранить")
        btn.clicked.connect(diag.accept)
        btn_del = QPushButton("Очистить урок")
        btn_del.setStyleSheet("background: #ff4444;")
        btn_del.clicked.connect(lambda: diag.done(2))
        
        fl.addRow("Готовый профиль:", cb_prof)
        fl.addRow(QLabel("ИЛИ ВРУЧНУЮ:"))
        fl.addRow("Учитель:", cb_t)
        fl.addRow("Предмет:", cb_s)
        fl.addRow("Кабинет:", cb_r)
        fl.addRow(btn_del); fl.addRow(btn)
        
        res = diag.exec()
        if res == 2: # Удаление
            if self.current_class in self.db["schedule"]:
                if str(row) in self.db["schedule"][self.current_class].get(day, {}):
                    del self.db["schedule"][self.current_class][day][str(row)]
                    save_db(self.db)
                    self.render_table()
            return
            
        if res == 1: # Сохранение
            if cb_prof.currentIndex() > 0:
                p_data = self.db["profiles"][cb_prof.currentText()]
                t, s, r = p_data["t"], p_data["s"], p_data["r"]
            else:
                t, s, r = cb_t.currentText(), cb_s.currentText(), cb_r.currentText()
            
            # ВАЛИДАЦИЯ КОНФЛИКТОВ
            conflict = self.check_conflicts(day, str(row), t, r)
            if conflict:
                QMessageBox.critical(self, "Конфликт в расписании!", conflict)
                return
                
            # Сохранение
            if self.current_class not in self.db["schedule"]: self.db["schedule"][self.current_class] = {}
            if day not in self.db["schedule"][self.current_class]: self.db["schedule"][self.current_class][day] = {}
            
            self.db["schedule"][self.current_class][day][str(row)] = {"t": t, "s": s, "r": r}
            save_db(self.db)
            self.render_table()

    def check_conflicts(self, day, lesson_row, teacher, room):
        # Проверяем все классы
        for c_name, schedule in self.db["schedule"].items():
            if c_name == self.current_class: continue # Себя пропускаем
            
            lesson = schedule.get(day, {}).get(lesson_row)
            if lesson:
                if lesson["t"] == teacher:
                    return f"Учитель '{teacher}' в это время уже ведет урок в классе {c_name}."
                if lesson["r"] == room and room != "":
                    return f"Кабинет {room} в это время занят классом {c_name}."
        return None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MinimalAdmin()
    window.show()
    sys.exit(app.exec())