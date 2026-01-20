# app/reports/statistical_report.py — ПОЛНАЯ РАБОЧАЯ ВЕРСИЯ (график отображается!)
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib import rcParams
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import tempfile

# === Кириллица ===
FONT_NAME = "DejaVu"
FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "fonts", "DejaVuSans.ttf")
if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
else:
    FONT_NAME = "Helvetica"

rcParams['font.family'] = 'DejaVu Sans'

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='MyBigTitle',   fontName=FONT_NAME, fontSize=26, alignment=TA_CENTER, spaceAfter=20, textColor=colors.HexColor("#1e40af")))
styles.add(ParagraphStyle(name='MySubTitle',   fontName=FONT_NAME, fontSize=16, alignment=TA_CENTER, spaceAfter=40))
styles.add(ParagraphStyle(name='MySection',    fontName=FONT_NAME, fontSize=16, spaceAfter=15, textColor=colors.HexColor("#1e293b")))
styles.add(ParagraphStyle(name='MyCenter',     fontName=FONT_NAME, alignment=TA_CENTER, fontSize=11))

class StatsReport:
    def __init__(self):
        self.filename = f"Статистический_отчет_{datetime.now().strftime('%Y-%m-%d')}.pdf"
        self.doc = SimpleDocTemplate(self.filename, pagesize=A4, topMargin=60, bottomMargin=60, leftMargin=50, rightMargin=50)

    def generate(self):
        story = []
        temp_files = []  # ← Собираем все временные файлы, чтобы удалить ПОСЛЕ сборки PDF

        story.append(Paragraph("СТАТИСТИЧЕСКИЙ ОТЧЁТ", styles['MyBigTitle']))
        story.append(Paragraph("и рейтинг участников", styles['MySubTitle']))
        story.append(Paragraph(f"Сформирован: {datetime.now().strftime('%d %B %Y')}", styles['MyCenter']))
        story.append(Spacer(1, 40))

        try:
            import mysql.connector
            conn = mysql.connector.connect(host='pma.morohin.info', user='phpmyadmin', password='0907', database='phpmyadmin')
            cur = conn.cursor()

            # === Статистика ===
            cur.execute("SELECT COUNT(*) FROM competition"); comp = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users"); users = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM programming_tasks"); tasks = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM decisions"); decisions = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM decisions WHERE status = 'OK'"); ok_solutions = cur.fetchone()[0]

            data = [
                ["Показатель", "Значение"],
                ["Соревнований", str(comp)],
                ["Участников", str(users)],
                ["Задач", str(tasks)],
                ["Всего решений", str(decisions)],
                ["Успешных решений", f"{ok_solutions}"]
            ]

            table = Table(data, colWidths=[300, 180])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
                ('FONTSIZE', (0,0), (-1,-1), 14),
                ('GRID', (0,0), (-1,-1), 1, colors.grey),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
            ]))
            story.append(table)
            story.append(Spacer(1, 50))

            # === ТОП-10 ===
            story.append(Paragraph("ТОП-10 УЧАСТНИКОВ ПО РЕШЁННЫМ ЗАДАЧАМ", styles['MySection']))
            story.append(Spacer(1, 15))

            cur.execute("""
                SELECT u.FCs, COUNT(d.id) as solved
                FROM users u
                LEFT JOIN decisions d ON u.id = d.id_users AND d.status = 'OK'
                GROUP BY u.id, u.FCs
                HAVING u.FCs IS NOT NULL
                ORDER BY solved DESC, u.FCs
                LIMIT 10
            """)
            top = cur.fetchall()

            if top and top[0][1] > 0:
                data = [["№", "Участник", "Решено задач"]]
                for i, (name, solved) in enumerate(top, 1):
                    data.append([str(i), name or "Без имени", str(solved)])

                table = Table(data, colWidths=[70, 320, 120])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
                    ('FONTSIZE', (0,0), (-1,0), 13),
                    ('FONTSIZE', (0,1), (-1,-1), 11),
                    ('GRID', (0,0), (-1,-1), 1, colors.lightgrey),
                    ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#fef3c7")),
                    ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#e5e7eb")),
                    ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#fed7aa")),
                ]))
                story.append(table)
            else:
                story.append(Paragraph("Решений с статусом OK пока нет", styles['MyCenter']))

            story.append(Spacer(1, 50))

            # === График — теперь БЕЗ ОШИБОК! ===
            story.append(Paragraph("РАСПРЕДЕЛЕНИЕ РЕШЕНИЙ ПО УЧАСТНИКАМ", styles['MySection']))
            story.append(Spacer(1, 15))

            cur.execute("""
                SELECT u.FCs, COUNT(d.id) as cnt
                FROM users u
                LEFT JOIN decisions d ON u.id = d.id_users AND d.status = 'OK'
                WHERE u.FCs IS NOT NULL
                GROUP BY u.id, u.FCs
                ORDER BY cnt DESC
                LIMIT 15
            """)
            data = cur.fetchall()

            if data and any(row[1] > 0 for row in data):
                names = [row[0][:25] + "..." if len(row[0]) > 25 else row[0] for row in data]
                counts = [row[1] for row in data]

                plt.figure(figsize=(10, 6))
                bars = plt.barh(names, counts, color='#3b82f6')
                plt.title("Топ участников по количеству решений", fontsize=16, pad=20)
                plt.xlabel("Количество решений")
                plt.grid(True, axis='x', alpha=0.3)

                for i, bar in enumerate(bars):
                    width = int(bar.get_width())
                    if width > 0:
                        plt.text(width + 0.1, bar.get_y() + bar.get_height()/2, str(width), va='center')

                plt.tight_layout()

                # ← КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: используем tempfile + не удаляем сразу!
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                tmp_path = tmp.name
                tmp.close()
                temp_files.append(tmp_path)  # запоминаем для удаления ПОСЛЕ сборки

                plt.savefig(tmp_path, dpi=180, bbox_inches='tight')
                plt.close()

                story.append(Image(tmp_path, width=520, height=340))
            else:
                story.append(Paragraph("Нет успешных решений для графика", styles['MyCenter']))

            conn.close()

        except Exception as e:
            story.append(Paragraph(f"Ошибка: {str(e)}", styles['MyCenter']))

        # === Сборка PDF ===
        self.doc.build(story)

        # === Удаляем временные файлы ТОЛЬКО ПОСЛЕ сборки PDF ===
        for path in temp_files:
            try:
                os.remove(path)
            except:
                pass

        print(f"Статистический отчёт успешно создан: {self.filename}")
