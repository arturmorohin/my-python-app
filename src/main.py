# main.py — Полностью рабочая финальная версия DataWise (ноябрь 2025)
import sys
from datetime import datetime
import mysql.connector
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QListWidget, QMessageBox,
    QTextEdit, QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
    QLineEdit, QComboBox, QHeaderView, QFrame
)
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QFont, QAction

# ============================= ОТЧЁТЫ =============================
try:
    from app.reports import DetailedReport, StatsReport
    REPORTS_AVAILABLE = True
except ImportError as e:
    REPORTS_AVAILABLE = False
    DetailedReport = StatsReport = None
    print("Модуль отчётов не найден:", e)

# ============================= ЛОГИРОВАНИЕ В UI =============================
class UILogger(QObject):
    log_signal = Signal(str, str)  # сообщение, тип

    def __init__(self):
        super().__init__()
        self.history = []

    def info(self, msg):    self._emit(msg, "info")
    def add(self, msg):     self._emit(msg, "add")
    def edit(self, msg):    self._emit(msg, "edit")
    def delete(self, msg): self._emit(msg, "delete")

    def _emit(self, msg, action):
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {msg}"
        self.history.append((full_msg, action))
        self.log_signal.emit(full_msg, action)

ui_logger = UILogger()

# ============================= ГЛАВНАЯ ПАНЕЛЬ =============================
class HomePanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("DataWise")
        title.setFont(QFont("Segoe UI", 36, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c5282;")

        subtitle = QLabel("Система управления соревнованиями по программированию")
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #4a5568; margin-bottom: 30px;")

        # Статистика карточками
        stats_layout = QHBoxLayout()
        stats = [
            ("Участников", "SELECT COUNT(*) FROM users"),
            ("Соревнований", "SELECT COUNT(*) FROM competition"),
            ("Задач", "SELECT COUNT(*) FROM programming_tasks"),
            ("Решений", "SELECT COUNT(*) FROM decisions")
        ]

        for text, query in stats:
            frame = QFrame()
            frame.setFixedSize(200, 130)
            frame.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ffffff, stop:1 #edf2f7);
                border-radius: 16px;
                border: 2px solid #e2e8f0;
            """)
            vbox = QVBoxLayout(frame)

            lbl_text = QLabel(text)
            lbl_text.setFont(QFont("Segoe UI", 11))
            lbl_text.setAlignment(Qt.AlignCenter)

            lbl_val = QLabel("—")
            lbl_val.setFont(QFont("Segoe UI", 28, QFont.Bold))
            lbl_val.setAlignment(Qt.AlignCenter)
            lbl_val.setStyleSheet("color: #2c5282;")

            vbox.addWidget(lbl_text)
            vbox.addWidget(lbl_val)
            stats_layout.addWidget(frame)

            # Загрузка данных
            try:
                conn = mysql.connector.connect(
                    host='pma.morohin.info',
                    user='phpmyadmin',
                    password='0907',
                    database='phpmyadmin'
                )
                cur = conn.cursor()
                cur.execute(query)
                value = cur.fetchone()[0]
                lbl_val.setText(str(value))
                cur.close()
                conn.close()
            except Exception as e:
                lbl_val.setText("Err")
                print("Ошибка статистики:", e)

        # Журнал
        log_label = QLabel("Журнал операций")
        log_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        log_label.setStyleSheet("color: #2d3748; margin-top: 20px;")

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(220)
        self.log_view.setStyleSheet("""
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px;
            font-family: Consolas;
            font-size: 11pt;
        """)

        ui_logger.log_signal.connect(lambda msg, typ: self.log_view.append(
            f"<span style='color:{'#27ae60' if typ=='add' else '#3498db' if typ=='edit' else '#e74c3c' if typ=='delete' else '#7f8c8d'}'>{msg}</span>"
        ))

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(stats_layout)
        layout.addWidget(log_label)
        layout.addWidget(self.log_view)
        layout.addStretch()

# ============================= ДАШБОРД =============================
class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Дашборд")
        title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        title.setStyleSheet("color: #1a365d; margin-bottom: 20px;")

        self.canvas = FigureCanvas(Figure(figsize=(10, 6)))
        self.ax = self.canvas.figure.add_subplot(111)

        layout.addWidget(title)
        layout.addWidget(self.canvas)

        self.refresh_plot()

    def refresh_plot(self):
        try:
            conn = mysql.connector.connect(host='pma.morohin.info', user='phpmyadmin',
                                         password='0907', database='phpmyadmin')
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT YEAR(date_of_the_event) as year, COUNT(*) as cnt FROM competition GROUP BY year ORDER BY year")
            data = cur.fetchall()

            years = [row['year'] for row in data]
            counts = [row['cnt'] for row in data]

            self.ax.clear()
            self.ax.bar(years, counts, color='#4299e1', edgecolor='white')
            self.ax.set_title("Количество соревнований по годам", fontsize=16, pad=20)
            self.ax.set_xlabel("Год")
            self.ax.set_ylabel("Кол-во")
            self.ax.grid(True, axis='y', alpha=0.3)
            self.canvas.draw()
        except Exception as e:
            self.ax.text(0.5, 0.5, f"Ошибка: {e}", transform=self.ax.transAxes,
                        ha='center', va='center', fontsize=14, color='red')
            self.canvas.draw()

# ============================= ДИАЛОГИ =============================
class DynamicAddDataForm(QDialog):
    def __init__(self, table_name, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Добавление — {table_name}")
        self.table_name = table_name
        self.columns = columns
        self.fields = {}

        form = QFormLayout()
        for col in columns:
            le = QLineEdit()
            le.setPlaceholderText(f"Введите {col}...")
            form.addRow(f"{col}:", le)
            self.fields[col] = le

        btn = QPushButton("Сохранить")
        btn.clicked.connect(self.save_data)
        form.addRow(btn)
        self.setLayout(form)

    def save_data(self):
        values = [self.fields[col].text().strip() for col in self.columns]
        if not all(values):
            QMessageBox.warning(self, "Ошибка", "Все поля обязательны")
            return

        try:
            conn = mysql.connector.connect(host='pma.morohin.info', user='phpmyadmin',
                                         password='0907', database='phpmyadmin')
            cur = conn.cursor()
            ph = ', '.join(['%s'] * len(self.columns))
            cols = ', '.join(self.columns)
            cur.execute(f"INSERT INTO `{self.table_name}` ({cols}) VALUES ({ph})", values)
            conn.commit()
            ui_logger.add(f"Добавлена запись в {self.table_name}")
            QMessageBox.information(self, "Успех", "Запись добавлена")
            self.accept()
            if self.parent():
                self.parent().refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

class DynamicEditDataForm(QDialog):
    def __init__(self, table_name, columns, initial_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Редактирование — {table_name}")
        self.table_name = table_name
        self.columns = columns
        self.id_val = initial_data['id']
        self.fields = {}

        form = QFormLayout()
        for col in columns:
            le = QLineEdit(str(initial_data.get(col, '')) if initial_data.get(col) is not None else '')
            form.addRow(f"{col}:", le)
            self.fields[col] = le

        btn = QPushButton("Сохранить изменения")
        btn.clicked.connect(self.save_data)
        form.addRow(btn)
        self.setLayout(form)

    def save_data(self):
        values = [self.fields[col].text().strip() for col in self.columns]
        if not all(values):
            QMessageBox.warning(self, "Ошибка", "Все поля обязательны")
            return

        try:
            conn = mysql.connector.connect(host='pma.morohin.info', user='phpmyadmin',
                                         password='0907', database='phpmyadmin')
            cur = conn.cursor()
            set_clause = ', '.join([f"`{c}`=%s" for c in self.columns])
            cur.execute(f"UPDATE `{self.table_name}` SET {set_clause} WHERE id=%s", (*values, self.id_val))
            conn.commit()
            ui_logger.edit(f"Обновлена запись id={self.id_val} в {self.table_name}")
            QMessageBox.information(self, "Успех", "Изменения сохранены")
            self.accept()
            if self.parent():
                self.parent().refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

# ============================= УПРАВЛЕНИЕ ДАННЫМИ =============================
class DataManagementView(QWidget):
    def __init__(self):
        super().__init__()
        self.current_table = None
        self.selected_row = -1

        layout = QHBoxLayout(self)

        # Левая панель
        left = QVBoxLayout()
        left.addWidget(QLabel("<b>Выберите таблицу:</b>"))
        self.combo = QComboBox()
        self.combo.currentTextChanged.connect(self.table_selected)
        left.addWidget(self.combo)

        btns = QVBoxLayout()
        self.btn_add = QPushButton("Добавить запись")
        self.btn_edit = QPushButton("Редактировать")
        self.btn_del = QPushButton("Удалить")
        self.btn_refresh = QPushButton("Обновить")

        for btn in (self.btn_add, self.btn_edit, self.btn_del, self.btn_refresh):
            btn.setStyleSheet("padding: 10px; margin: 3px 0;")
        self.btn_edit.setEnabled(False)
        self.btn_del.setEnabled(False)

        self.btn_add.clicked.connect(self.add_record)
        self.btn_edit.clicked.connect(self.edit_selected)
        self.btn_del.clicked.connect(self.delete_selected)
        self.btn_refresh.clicked.connect(self.refresh_table)

        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_edit)
        btns.addWidget(self.btn_del)
        btns.addWidget(self.btn_refresh)
        btns.addStretch()
        left.addLayout(btns)
        layout.addLayout(left, 1)

        # Таблица
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.selectionModel().selectionChanged.connect(self.selection_changed)
        layout.addWidget(self.table, 4)

        self.load_tables()

    def db_connect(self):
        return mysql.connector.connect(
            host='pma.morohin.info', user='phpmyadmin',
            password='0907', database='phpmyadmin'
        )

    def load_tables(self):
        try:
            conn = self.db_connect()
            cur = conn.cursor()
            cur.execute("SHOW TABLES")
            tables = [row[0] for row in cur.fetchall()]
            self.combo.addItems(tables)
            if tables:
                self.combo.setCurrentIndex(0)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def table_selected(self, name):
        if name:
            self.current_table = name
            self.refresh_table()

    def refresh_table(self):
        if not self.current_table: return
        try:
            conn = self.db_connect()
            cur = conn.cursor()
            cur.execute(f"SHOW COLUMNS FROM `{self.current_table}`")
            cols = [row[0] for row in cur.fetchall() if row[0].lower() != 'id']

            placeholders = ', '.join([f"`{c}`" for c in cols])
            cur.execute(f"SELECT {placeholders} FROM `{self.current_table}` ORDER BY id")
            rows = cur.fetchall()

            self.table.setRowCount(len(rows))
            self.table.setColumnCount(len(cols))
            self.table.setHorizontalHeaderLabels(cols)

            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    item = QTableWidgetItem(str(val) if val is not None else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(r, c, item)

            self.table.resizeColumnsToContents()
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        finally:
            if 'conn' in locals(): conn.close()

    def selection_changed(self):
        rows = self.table.selectionModel().selectedRows()
        self.selected_row = rows[0].row() if rows else -1
        self.btn_edit.setEnabled(self.selected_row >= 0)
        self.btn_del.setEnabled(self.selected_row >= 0)

    def edit_selected(self):
        if self.selected_row >= 0:
            self.edit_record(self.selected_row)

    def delete_selected(self):
        if self.selected_row >= 0:
            self.delete_record(self.selected_row)

    def add_record(self):
        if not self.current_table: return
        cols = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        dlg = DynamicAddDataForm(self.current_table, cols, self)
        dlg.exec()

    def edit_record(self, row):
        record = self.get_record_by_row(row)
        if record:
            cols = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            dlg = DynamicEditDataForm(self.current_table, cols, record, self)
            dlg.exec()

    def delete_record(self, row):
        record = self.get_record_by_row(row)
        if not record: return
        if QMessageBox.question(self, "Удалить?", f"Удалить запись id={record['id']}?") == QMessageBox.Yes:
            try:
                conn = self.db_connect()
                cur = conn.cursor()
                cur.execute(f"DELETE FROM `{self.current_table}` WHERE id=%s", (record['id'],))
                conn.commit()
                ui_logger.delete(f"Удалена запись id={record['id']} из {self.current_table}")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def get_record_by_row(self, row):
        try:
            conn = self.db_connect()
            cur = conn.cursor(dictionary=True)
            cur.execute(f"SELECT id FROM `{self.current_table}` ORDER BY id LIMIT 1 OFFSET %s", (row,))
            res = cur.fetchone()
            if not res: return None
            cur.execute(f"SELECT * FROM `{self.current_table}` WHERE id=%s", (res['id'],))
            return cur.fetchone()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return None

# ============================= ВКЛАДКА ОТЧЁТЫ =============================
class ReportsPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60,60,60)
        layout.setSpacing(30)

        title = QLabel("Генерация отчётов")
        title.setFont(QFont("Segoe UI", 32, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1a365d;")

        desc = QLabel("Нажмите кнопку — PDF будет создан мгновенно")
        desc.setFont(QFont("Segoe UI", 14))
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #4a5568; margin-bottom: 40px;")

        btn1 = QPushButton("📄 Подробный отчёт по соревнованиям")
        btn2 = QPushButton("📊 Статистический отчёт и рейтинг")

        for btn in (btn1, btn2):
            btn.setFont(QFont("Segoe UI", 16))
            btn.setFixedHeight(80)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4299e1;
                    color: white;
                    border-radius: 16px;
                    padding: 20px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #3182ce; }
                QPushButton:pressed { background-color: #2b6cb0; }
            """)

        if REPORTS_AVAILABLE:
            btn1.clicked.connect(lambda: self.generate(DetailedReport, "Подробный отчёт"))
            btn2.clicked.connect(lambda: self.generate(StatsReport, "Статистический отчёт"))
        else:
            btn1.setEnabled(False)
            btn2.setEnabled(False)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(btn1)
        layout.addWidget(btn2)
        layout.addStretch()

    def generate(self, report_class, name):
        try:
            report_class().generate()
            ui_logger.info(f"{name} успешно создан!")
            QMessageBox.information(self, "Готово", f"{name} сохранён в корне проекта")
        except Exception as e:
            ui_logger.delete(f"Ошибка генерации отчёта: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))

# ============================= ГЛАВНОЕ ОКНО =============================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DataWise — Система управления соревнованиями")
        self.resize(1280, 720)

        self.setStyleSheet("""
            QMainWindow { background-color: #f7fafc; }
            QListWidget { background-color: #2d3748; color: white; font-size: 15px; border: none; }
            QListWidget::item { padding: 18px; border-bottom: 1px solid #4a5568; }
            QListWidget::item:selected { background-color: #4299e1; }
            QPushButton { background-color: #4299e1; color: white; border-radius: 8px; padding: 12px; font-weight: bold; }
            QPushButton:hover { background-color: #3182ce; }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        # Боковая панель
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(280)
        self.sidebar.addItems([
            "🏠 Главная",
            "📊 Дашборд",
            "👥 Управление данными",
            "📄 Отчёты",
            "❓ Справка"
        ])

        # Стек страниц
        self.stack = QStackedWidget()
        self.stack.addWidget(HomePanel())
        self.stack.addWidget(DashboardView())
        self.stack.addWidget(DataManagementView())
        self.stack.addWidget(ReportsPanel())
        self.stack.addWidget(QLabel("<h2>Справка и поддержка</h2><p>Скоро здесь будет документация :)</p>"))

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)

        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

        # Меню → Отчёты
        menu = self.menuBar()
        reports_menu = menu.addMenu("Отчёты")
        if REPORTS_AVAILABLE:
            act1 = QAction("Подробный отчёт (PDF)", self)
            act2 = QAction("Статистический отчёт (PDF)", self)
            act1.triggered.connect(lambda: DetailedReport().generate())
            act2.triggered.connect(lambda: StatsReport().generate())
            reports_menu.addAction(act1)
            reports_menu.addAction(act2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("QLabel { font-family: Segoe UI; }")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
