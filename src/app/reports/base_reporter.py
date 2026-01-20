# app/reports/base_reporter.py
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os


class BasePDFReporter:
    def __init__(self, filename="report.pdf"):
        self.filename = filename
        self.doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            leftMargin=0.8*inch,
            rightMargin=0.8*inch,
            topMargin=1*inch,
            bottomMargin=0.8*inch
        )
        self.story = []
        self._register_fonts()

    def _register_fonts(self):
        # Пытаемся подключить Arial (Windows путь — на Linux упадёт в except)
        try:
            pdfmetrics.registerFont(TTFont('Arial-Russian', '/usr/share/fonts/truetype/msttcorefonts/arial.ttf'))
            pdfmetrics.registerFont(TTFont('Arial-Russian-Bold', '/usr/share/fonts/truetype/msttcorefonts/arialbd.ttf'))
            self.font_normal = 'Arial-Russian'
            self.font_bold = 'Arial-Russian-Bold'
        except:
            # Если Arial нет — пробуем DejaVu (обычно есть на Linux и т.д.)
            try:
                pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
                self.font_normal = 'DejaVuSans'
                self.font_bold = 'DejaVuSans-Bold'
            except:
                self.font_normal = 'Helvetica'
                self.font_bold = 'Helvetica-Bold'
                print("Warning: Используется Helvetica — кириллица может отображаться квадратами")

    def add_title(self, text):
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            name='TitleRU',
            fontName=self.font_bold,
            fontSize=22,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1a365d')
        )
        self.story.append(Paragraph(text, title_style))
        self.story.append(Spacer(1, 20))
        self.story.append(Paragraph(f"Сформирован: {datetime.now().strftime('%d.%m.%Y в %H:%M')}", styles['Normal']))
        self.story.append(Spacer(1, 40))

    def add_heading(self, text):
        h_style = ParagraphStyle(
            name='H1RU',
            fontName=self.font_bold,
            fontSize=16,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.HexColor('#2c5282')
        )
        self.story.append(Paragraph(text, h_style))

    def build(self):
        self.doc.build(self.story)
        print(f"PDF успешно создан: {os.path.abspath(self.filename)}")
