import requests

BASE_URL = "http://127.0.0.1:8080"
se1_headers = {"Host": "se1.localhost"}
se2_headers = {"Host": "se2.localhost"}

# ===============================
# se1: create first report
# ===============================
se1_create_resp = requests.post(
    f"{BASE_URL}/report/",
    headers=se1_headers,
    data={
        "version": "0.9.0",
        "title": "Unable to search (DR0)",
        "description": "Search button unresponsive after completing an initial search",
        "reproduce_steps": "1. Complete a search\n2. Modify search criteria\n3. Click Search button",
        "product": 1,
        "tester_id": "Tester_1",
        "tester_email": "icyreward@gmail.com ",
    },
)
print("[se1] created first report", se1_create_resp.status_code, se1_create_resp.text)

# login as se1 PO user1
se1_po_session = requests.Session()
se1_po_bootstrap_resp = se1_po_session.get(
    f"{BASE_URL}/admin/login/",
    headers=se1_headers,
 )
print("[se1] PO csrf bootstrap", se1_po_bootstrap_resp.status_code)
se1_po_login_resp = se1_po_session.post(
    f"{BASE_URL}/login/",
    headers=se1_headers,
    data={"email": "u1@t1", "password": "pw"},
)
print("[se1] PO login", se1_po_login_resp.status_code)
se1_po_csrf = se1_po_session.cookies.get("csrftoken")
print("[se1] PO csrf", se1_po_csrf)
se1_po_auth_headers = {
    "Host": "se1.localhost",
    "X-CSRFToken": se1_po_csrf,
    "Referer": "http://se1.localhost:8080/",
}

# get report for checking
se1_list_resp = se1_po_session.get(
    f"{BASE_URL}/report/",
    headers=se1_headers,
 )
print("[se1] list reports", se1_list_resp.status_code, se1_list_resp.json())

# open as PO with MAJOR/HIGH
se1_open_resp = se1_po_session.patch(
    f"{BASE_URL}/report/1/",
    headers=se1_po_auth_headers,
    json={"action": "OPEN", "severity": "MAJOR", "priority": "HIGH"},
)
print("[se1] open report", se1_open_resp.status_code, se1_open_resp.text)


# login as se1 dev user2
se1_dev_session = requests.Session()
se1_dev_bootstrap_resp = se1_dev_session.get(
    f"{BASE_URL}/admin/login/",
    headers=se1_headers,
 )
print("[se1] DEV csrf bootstrap", se1_dev_bootstrap_resp.status_code)
se1_dev_login_resp = se1_dev_session.post(
    f"{BASE_URL}/login/",
    headers=se1_headers,
    data={"email": "u2@t1", "password": "pw"},
)
print("[se1] DEV login", se1_dev_login_resp.status_code)
se1_dev_csrf = se1_dev_session.cookies.get("csrftoken")
print("[se1] DEV csrf", se1_dev_csrf)
se1_dev_auth_headers = {
    "Host": "se1.localhost",
    "X-CSRFToken": se1_dev_csrf,
    "Referer": "http://se1.localhost:8080/",
}

# assign to himself
se1_assign_resp = se1_dev_session.patch(
    f"{BASE_URL}/report/1/",
    headers=se1_dev_auth_headers,
    json={"action": "ASSIGN"},
)
print("[se1] assign report", se1_assign_resp.status_code, se1_assign_resp.text)

# get report content for checking
se1_get_report_resp = se1_dev_session.get(
    f"{BASE_URL}/report/1/",
    headers=se1_headers,
 )
print("[se1] report content", se1_get_report_resp.status_code, se1_get_report_resp.json())

# ===============================
# se1: create 2nd/3rd/4th report
# ===============================
se1_create_resp = requests.post(
    f"{BASE_URL}/report/",
    headers=se1_headers,
    data={
        "version": "0.9.0",
        "title": "DR1",
        "description": "Desc",
        "reproduce_steps": "Step",
        "product": 1,
        "tester_id": "Tester_2",
        "tester_email": "betatraxusers@gmail.com",
    },
)
print("[se1] created 2nd report", se1_create_resp.status_code, se1_create_resp.text)

se1_create_resp = requests.post(
    f"{BASE_URL}/report/",
    headers=se1_headers,
    data={
        "version": "0.9.0",
        "title": "DR2",
        "description": "Desc",
        "reproduce_steps": "Step",
        "product": 2,
        "tester_id": "Tester_1",
        "tester_email": "icyreward@gmail.com",
    },
)
print("[se1] created 3rd report", se1_create_resp.status_code, se1_create_resp.text)

se1_create_resp = requests.post(
    f"{BASE_URL}/report/",
    headers=se1_headers,
    data={
        "version": "0.9.0",
        "title": "DR3",
        "description": "Desc",
        "reproduce_steps": "Step",
        "product": 2,
        "tester_id": "Tester_2",
        "tester_email": "betatraxusers@gmail.com",
    },
)
print("[se1] created 4th report", se1_create_resp.status_code, se1_create_resp.text)
