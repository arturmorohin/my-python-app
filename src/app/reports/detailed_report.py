# app/reports/detailed_report.py — ФИНАЛЬНАЯ РАБОЧАЯ ВЕРСИЯ (без конфликтов стилей)
import os
import tempfile
from datetime import datetime
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# === Шрифты ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
FONT_DIR = os.path.join(BASE_DIR, "fonts")
FONT_NAME = "DejaVu"
BOLD_FONT_NAME = "DejaVu-Bold"

if os.path.exists(os.path.join(FONT_DIR, "DejaVuSans.ttf")):
    pdfmetrics.registerFont(TTFont(FONT_NAME, os.path.join(FONT_DIR, "DejaVuSans.ttf")))
if os.path.exists(os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")):
    pdfmetrics.registerFont(TTFont(BOLD_FONT_NAME, os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")))
else:
    BOLD_FONT_NAME = FONT_NAME

# === Стили с УНИКАЛЬНЫМИ именами ===
styles = getSampleStyleSheet()

styles.add(ParagraphStyle(name='DW_Title',      fontName=BOLD_FONT_NAME, fontSize=36, alignment=TA_CENTER, spaceAfter=30, textColor=colors.HexColor("#1e40af")))
styles.add(ParagraphStyle(name='DW_SubTitle',   fontName=FONT_NAME,      fontSize=18, alignment=TA_CENTER, spaceAfter=20))
styles.add(ParagraphStyle(name='DW_DateTime',   fontName=FONT_NAME,      fontSize=14, alignment=TA_CENTER, spaceAfter=50))
styles.add(ParagraphStyle(name='DW_Desc',       fontName=FONT_NAME,      fontSize=12, alignment=TA_JUSTIFY, spaceAfter=30, leading=16))
styles.add(ParagraphStyle(name='DW_TOC_Title',  fontName=BOLD_FONT_NAME, fontSize=24, alignment=TA_CENTER, spaceAfter=30, textColor=colors.HexColor("#1e40af")))
styles.add(ParagraphStyle(name='DW_TOC_Item',   fontName=FONT_NAME,      fontSize=14, leftIndent=20, spaceAfter=8))
styles.add(ParagraphStyle(name='DW_CompTitle',  fontName=BOLD_FONT_NAME, fontSize=22, spaceBefore=20, spaceAfter=15, textColor=colors.HexColor("#1e40af")))
styles.add(ParagraphStyle(name='DW_Section',    fontName=BOLD_FONT_NAME, fontSize=16, spaceBefore=20, spaceAfter=10))
styles.add(ParagraphStyle(name='DW_Center',     fontName=FONT_NAME,      alignment=TA_CENTER, fontSize=12))

class DetailedReport:
    def __init__(self):
        now = datetime.now()
        self.generated_at = now.strftime("%d %B %Y в %H:%M")
        self.filename = f"Подробный_отчет_{now.strftime('%Y-%m-%d_%H-%M')}.pdf"
        self.doc = SimpleDocTemplate(self.filename, pagesize=A4,
                                     topMargin=2*cm, bottomMargin=2*cm,
                                     leftMargin=2*cm, rightMargin=2*cm)
        self.story = []
        self.temp_files = []

    def generate(self):
        from database.database import get_connection
        conn = get_connection()
        if not conn:
            self.story.append(Paragraph("Ошибка подключения к БД", styles['DW_Center']))
            self.doc.build(self.story)
            return
        cur = conn.cursor(dictionary=True)

        # === Титульная страница ===
        self.story.append(Spacer(1, 6*cm))
        self.story.append(Paragraph("ПОДРОБНЫЙ ОТЧЁТ", styles['DW_Title']))
        self.story.append(Paragraph("по всем соревнованиям по программированию", styles['DW_SubTitle']))
        self.story.append(Paragraph(f"Сформирован: {self.generated_at}", styles['DW_DateTime']))
        self.story.append(Paragraph(
            "Данный отчёт содержит полную информацию о проведённых соревнованиях, список участников, "
            "статистику по задачам, результаты решений и общий рейтинг лидеров. "
            "Все данные актуальны на момент генерации отчёта.",
            styles['DW_Desc']
        ))
        self.story.append(Paragraph("Система DataWise © 2025", styles['DW_Center']))
        self.story.append(PageBreak())

        # === Содержание ===
        self.story.append(Paragraph("СОДЕРЖАНИЕ", styles['DW_TOC_Title']))
        self.story.append(Spacer(1, 20))

        cur.execute("SELECT id, title FROM competition ORDER BY date_of_the_event DESC")
        competitions = cur.fetchall()

        for comp in competitions:
            title = comp['title'] or f"Соревнование #{comp['id']}"
            self.story.append(Paragraph(
                f"• <a href=\"#comp_{comp['id']}\" color=\"#1e40af\"><b>{title}</b></a>",
                styles['DW_TOC_Item']
            ))
        self.story.append(Paragraph(
            "• <a href=\"#final_stats\" color=\"#1e40af\"><b>Итоговая статистика и рейтинг</b></a>",
            styles['DW_TOC_Item']
        ))
        self.story.append(PageBreak())

        # === По каждому соревнованию ===
        for comp in competitions:
            comp_id = comp['id']
            title = comp['title'] or "Без названия"

            self.story.append(Paragraph(f"<a name=\"comp_{comp_id}\"/>", styles['DW_Center']))
            self.story.append(Paragraph(title, styles['DW_CompTitle']))
            self.story.append(Spacer(1, 12))

            cur.execute("SELECT * FROM competition WHERE id = %s", (comp_id,))
            c = cur.fetchone()
            info = [
                ["Дата начала", c['date_of_the_event'].strftime('%d.%m.%Y')],
                ["Дата окончания", c['end_date'].strftime('%d.%m.%Y') if c['end_date'] else "—"],
                ["Количество задач", str(c['number_of_tasks'])],
                ["Описание", c['description'] or "—"],
            ]
            t = Table(info, colWidths=[150, 350])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0f9ff")),
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#94a3b8")),
                ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
                ('LEFTPADDING', (0,0), (-1,-1), 12),
                ('FONTSIZE', (0,0), (-1,-1), 12),
            ]))
            self.story.append(t)
            self.story.append(Spacer(1, 30))

            # Участники
            cur.execute("""
                SELECT u.FCs, u.Specialization, p.Place_in_the_leaderboard
                FROM participation p
                JOIN users u ON p.id_users = u.id
                WHERE p.id_competition = %s
                ORDER BY COALESCE(p.Place_in_the_leaderboard, 9999)
            """, (comp_id,))
            self.story.append(Paragraph("УЧАСТНИКИ", styles['DW_Section']))
            participants = cur.fetchall()
            if participants:
                data = [["Место", "ФИО", "Специализация"]]
                for p in participants:
                    place = p['Place_in_the_leaderboard'] or "—"
                    data.append([place, p['FCs'], p['Specialization'] or "—"])
                pt = Table(data, colWidths=[80, 280, 140])
                pt.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('GRID', (0,0), (-1,-1), 0.8, colors.grey),
                    ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
                ]))
                self.story.append(pt)
            else:
                self.story.append(Paragraph("Участников нет", styles['DW_Center']))
            self.story.append(Spacer(1, 30))

            # Задачи и статистика
            self.story.append(Paragraph("ЗАДАЧИ И СТАТИСТИКА РЕШЕНИЙ", styles['DW_Section']))
            cur.execute("""
                SELECT pt.id, pt.points, pt.complexity, ct.letter,
                       COUNT(CASE WHEN d.status = 'OK' THEN 1 END) AS ok,
                       COUNT(CASE WHEN d.status != 'OK' AND d.status IS NOT NULL THEN 1 END) AS err
                FROM competition_tasks ct
                JOIN programming_tasks pt ON ct.task_id = pt.id
                LEFT JOIN decisions d ON pt.id = d.id_programminng_tasks
                    AND d.id_users IN (SELECT id_users FROM participation WHERE id_competition = %s)
                WHERE ct.competition_id = %s
                GROUP BY pt.id, ct.letter
                ORDER BY ct.letter
            """, (comp_id, comp_id))
            tasks = cur.fetchall()

            if tasks:
                data = [["Буква", "Задача", "Баллы", "Сложность", "OK", "Ошибка", "Всего"]]
                oks = []
                for t in tasks:
                    ok = t['ok'] or 0
                    err = t['err'] or 0
                    total = ok + err
                    data.append([t['letter'] or "—", str(t['id']), str(t['points']), str(t['complexity']), str(ok), str(err), str(total)])
                    oks.append(ok)
                table = Table(data, colWidths=[60, 80, 70, 90, 70, 80, 80])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e40af")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('GRID', (0,0), (-1,-1), 1, colors.lightgrey),
                    ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
                ]))
                self.story.append(table)

                if oks and sum(oks) > 0:
                    plt.figure(figsize=(10, max(4, len(oks)*0.6)))
                    plt.barh(range(len(oks)), oks, color='#10b981')
                    plt.yticks(range(len(oks)), [t['letter'] or f"Задача {i+1}" for i, t in enumerate(tasks)])
                    plt.title(f"Решённые задачи — {title}")
                    plt.xlabel("Количество участников")
                    plt.grid(axis='x', alpha=0.3)
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    plt.savefig(tmp.name, dpi=200, bbox_inches='tight')
                    plt.close()
                    self.temp_files.append(tmp.name)
                    self.story.append(Spacer(1, 20))
                    self.story.append(Image(tmp.name, width=500, height=300))
            else:
                self.story.append(Paragraph("Задачи не назначены", styles['DW_Center']))
            self.story.append(PageBreak())

        # === Итоговая статистика ===
        self.story.append(Paragraph("<a name=\"final_stats\"/>", styles['DW_Center']))
        self.story.append(Paragraph("ИТОГОВАЯ СТАТИСТИКА И РЕЙТИНГ", styles['DW_CompTitle']))
        self.story.append(Spacer(1, 30))

        cur.execute("""
            SELECT u.FCs, COUNT(*) as solved
            FROM decisions d
            JOIN users u ON d.id_users = u.id
            WHERE d.status = 'OK'
            GROUP BY u.id, u.FCs
            ORDER BY solved DESC LIMIT 15
        """)
        top15 = cur.fetchall()
        if top15:
            data = [["№", "Участник", "Решено задач"]]
            for i, row in enumerate(top15, 1):
                data.append([str(i), row['FCs'], str(row['solved'])])
            t = Table(data, colWidths=[60, 350, 120])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 1, colors.grey),
                ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
            ]))
            self.story.append(t)

        self.story.append(Spacer(1, 40))
        self.story.append(Paragraph(f"Отчёт сформирован {self.generated_at}", styles['DW_Center']))
        self.story.append(Paragraph("© DataWise 2025", styles['DW_Center']))

        self.doc.build(self.story)

        for f in self.temp_files:
            try: os.remove(f)
            except: pass

        cur.close()
        conn.close()
        print(f"Подробный отчёт успешно создан: {os.path.abspath(self.filename)}")
