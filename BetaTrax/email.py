from .models import Report

def notify_tester_status(report: Report, status: str):
    if report.tester_email is None:
        return
    send(report.tester_email, "Report Updated", f"Your report {report.title} has been updated to {status}.")


def notify_all_testers_status(report: Report, status: str):
    # Notify the current report tester and all duplicate child report testers.
    related_reports = Report.objects.filter(duplicate_of=report)
    notify_tester_status(report, status)
    for child_report in related_reports:
        notify_tester_status(child_report, status)

def send(to: str, subject: str, message: str):
    print(f"[Email] TO: {to}, SUBJECT: {subject}, MESSAGE: {message}")