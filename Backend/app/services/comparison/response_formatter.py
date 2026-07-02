from app.services.comparison.models import ComparisonReport


def format_response(report: ComparisonReport) -> dict:
    return report.to_dict()
