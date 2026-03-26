from .models import Report

def notify_tester_status(report: Report, status: str):
    if report.tester_email is None:
        return
    send(report.tester_email, "Report Updated", f"Your report {report.title} has been updated to {status}.")

def send(to: str, subject: str, message: str):
    print(f"[Email] TO: {to}, SUBJECT: {subject}, MESSAGE: {message}")