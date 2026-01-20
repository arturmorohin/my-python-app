# app/reports/__init__.py
from .detailed_report import DetailedReport
from .statistical_report import StatsReport

# Удобные алиасы — можно будет писать просто:
# from app.reports import DetailedReport, StatsReport


# Список всех доступных отчётов (удобно для GUI)
AVAILABLE_REPORTS = {
    "detailed": {
        "name": "Подробный отчёт по соревнованиям",
        "class": DetailedReport,
        "description": "Все соревнования, участники, задачи и решения"
    },
    "statistical": {
        "name": "Статистический отчёт и рейтинг",
        "class": StatsReport,
        "description": "ТОП участников, графики активности, анализ сложности"
    }
}

__all__ = [
    "DetailedReport",
    "StatsReport",
    "DetailedReport",
    "StatsReport",
    "AVAILABLE_REPORTS"
]

# Опционально: можно добавить функцию для запуска по имени
def generate_report(report_type: str):
    """
    Быстро сгенерировать отчёт по его типу.
    
    Пример:
        generate_report("detailed")
        generate_report("statistical")
    """
    report_type = report_type.lower()
    if report_type not in AVAILABLE_REPORTS:
        raise ValueError(f"Неизвестный тип отчёта: {report_type}. Доступно: {', '.join(AVAILABLE_REPORTS.keys())}")
    
    report_class = AVAILABLE_REPORTS[report_type]["class"]
    print(f"Генерация отчёта: {AVAILABLE_REPORTS[report_type]['name']}")
    report_class().generate()
