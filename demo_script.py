#!/usr/bin/env python3
import requests
import json

# docker compose up
# docker compose exec betatrax uv run python setup_demo.py 
# docker compose exec betatrax uv run python demo_script.py

BASE_URL = "http://betatrax:8000"
session = requests.Session()

def login(email, password):
    session.post(f"{BASE_URL}/login/", data={"email": email, "password": password})

def logout():
    session.post(f"{BASE_URL}/logout/")

def submit_report(title, description, reproduce_steps, product_id, tester_email, version):
    r = session.post(f"{BASE_URL}/report/", data={
        "title": title, "description": description, "reproduce_steps": reproduce_steps,
        "product": product_id, "tester_email": tester_email, "version": version
    })
    if r.status_code == 201:
        r2 = session.get(f"{BASE_URL}/report/?search={title}")
        if r2.status_code == 200:
            reports = r2.json()
            for report in reports.get("reports", []):
                if report["title"] == title:
                    return report["id"]
    return None

def list_reports(status=None):
    params = {"status": status} if status else {}
    r = session.get(f"{BASE_URL}/report/", params=params)
    if r.status_code == 200:
        return r.json().get("reports", [])
    return []

def view_report(report_id):
    r = session.get(f"{BASE_URL}/report/{report_id}/")
    if r.status_code == 200:
        return r.json()
    return None

def action(report_id, action_name, **kwargs):
    payload = {"action": action_name, **kwargs}
    return session.patch(f"{BASE_URL}/report/{report_id}/", 
                        data=json.dumps(payload), headers={"Content-Type": "application/json"})

PO_EMAIL, PO_PASSWORD = "po@betatrax.com", "password"
DEV_EMAIL, DEV_PASSWORD = "dev@betatrax.com", "password"
PRODUCT_ID = "1"
TARGET_TITLE = "Hit count incorrect"

print("Step 1: Submit defect report")
login(PO_EMAIL, PO_PASSWORD)
report_id = submit_report(
    TARGET_TITLE,
    "Following a successful search, the hit count is different to the number of matches displayed.",
    "1. Enter search criteria that ensure at least one match\n2. Search\n3. Compare matches displayed with the number of hits reported.",
    PRODUCT_ID, "icyreward@gmail.com", "0.9.0")
if not report_id:
    reports = list_reports('NEW')
    for r in reports:
        if r['title'] == TARGET_TITLE:
            report_id = r['id']
            break
print(f"Report ID: {report_id}")

print("\nStep 2: List reports (Product Owner - NEW status)")
reports = list_reports('NEW')
print(json.dumps(reports, indent=2))

print("\nStep 3: View details of target report")
report = view_report(report_id)
print(json.dumps(report, indent=2))

print("\nStep 4: Accept report (Severity: Minor, Priority: High)")
action(report_id, "OPEN", severity=1, priority=2)

print("\nStep 5: List reports (Developer - OPENED status)")
logout()
login(DEV_EMAIL, DEV_PASSWORD)
reports = list_reports('OPENED')
print(json.dumps(reports, indent=2))

print("\nStep 6: View details of target report")
report = view_report(report_id)
print(json.dumps(report, indent=2))

print("\nStep 7: Assign report (Developer takes responsibility)")
action(report_id, "ASSIGN")

print("\nStep 8: List reports (Developer - ASSIGNED status)")
reports = list_reports('ASSIGNED')
print(json.dumps(reports, indent=2))

print("\nStep 9: Mark report as Fixed")
action(report_id, "FIX")

print("\nStep 10: List reports (Product Owner - FIXED status)")
logout()
login(PO_EMAIL, PO_PASSWORD)
reports = list_reports('FIXED')
print(json.dumps(reports, indent=2))

print("\nStep 11: Close report as Resolved")
action(report_id, "RESOLVE")

logout()
print("\nDemo complete")
