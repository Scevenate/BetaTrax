# BetaTrax Defect Report Management System

## 1. Quick Start

> [!WARNING]
> The default configuration is meant for development environment or internal use. When deployed in production, make sure:
> 1. Replace `SECRET_KEY`, disable `DEBUG`, configure `ALLOWED_HOSTS` in `project/settings.py`.
> 2. Setup static path `STATIC_ROOT` in `project/settings.py`, deploy static files collected from `uv run manage.py collectstatic` separately.
> 3. Configure a reverse proxy server with proper rate limiting protections on sensitive interfaces, like `admin/` and `login/`.

### Docker

`docker compose up`

This spins up the app with a postgres service. Please refer to `docker-compose.yml` for common configurations.

### Manual

The app also supports manual deployment. It falls back to sqlite (in repo root dir) when postgres config is not provided.

0. `git clone`, navigate to repository root directory.
1. Install dependencies by `uv sync`.
2. Setup database by `uv run manage.py makemigrations BetaTrax && uv run manage.py makemigrations && uv run migrate`
3. Start server by `uv run gunicorn project.wsgi:application`

## 2. Environment / Components

- Web framework: Django 6.x with gunicorn wsgi
- Database: PostgreSQL 18 (sqlite3 can be used for local unit tests)
- Docker image: `ghcr.io/astral-sh/uv:python3.13-bookworm-slim`
- Authentication: Django custom user model (`Employee` with roles: `PRODUCT_OWNER`, `DEVELOPER`)
- Email-notification helper: `BetaTrax/email.py` (`notify_tester_status` called on status transitions)
- API endpoints are defined in `BetaTrax/views.py` and `project/urls.py`.
- CSRF: currently disabled until frontend is connected.

## 3. Supported Functionality (Required Slice)

### Actors
- `Product Owner` (role `PRODUCT_OWNER`)
- `Developer` (role `DEVELOPER`)
- `Tester` (report creator via `/report/` POST)

### Core defect lifecycle
- NEW -> OPENED -> ASSIGNED -> FIXED -> RESOLVED
- Additional dead states: `REJECTED`, `DUPLICATED`, `COULDNT_REPRODUCE`, and `REOPENED`.

### Report creation (Tester)
- Endpoint: `POST /report/`
- Required fields: `title`, `description`, `reproduce_steps`, `product`, `tester_id`.
- Optional: `tester_email`.
- Initial status: `NEW`.

### Product Owner actions (via `PATCH /report/<id>/`)
- `OPEN`: on `NEW` -> sets `severity`, `priority`, status `OPENED`.
- `REJECT`: on `NEW` -> status `REJECTED`.
- `DUPLICATE`: on `NEW` -> sets `duplicate_of`, status `DUPLICATED`.
- `REOPEN`: on `FIXED` -> status `REOPENED`.
- `RESOLVE`: on `FIXED` -> status `RESOLVED`.

### Developer actions (via `PATCH /report/<id>/`)
- `ASSIGN`: on `OPENED` / `REOPENED` -> clears `OPENED`/`REOPENED`, status `ASSIGNED`.
- `FIX`: on `ASSIGNED` -> clears `assigned_to`, status `FIXED`.
- `CANNOT_REPRODUCE`: on `ASSIGNED` -> clears `assigned_to`, status `COULDNT_REPRODUCE`.

### Reporting and filtering
- `GET /report/` with query params:
  - `status` (any `ReportStatus` value or omitted)
  - `search` (title contains)
  - `sort` (`-updated_at`, `-severity`, `-priority`)
  - `page` (1-based, 20 items/page)
- `GET /report/<id>/` returns full report details.

### Comments
- `GET /report/<id>/comments/` returns comments for report.
- `POST /report/<id>/comments/` adds comment as current authenticated user.

### Authentication
- `POST /login/` with `email`, `password`.
- `POST /logout/`.
- All report and comment endpoints require logged-in users (403 otherwise), except report creation.

## 3.1 Additional functions
- Report CRUD coverage in views:
  - `GET /report/` list (with search/paging/sort/status filters)
  - `GET /report/<id>/` detail
  - `POST /report/` create (NEW)
  - `PATCH /report/<id>/` update/report transition
- Comment CRUD:
  - `GET /report/<id>/comments/` list
  - `POST /report/<id>/comments/` create
- Status transition validation is enforced in `ReportView.patch` via `ReportAction` and `ReportStatus`.
- People management via `Employee` model with role guard in report access (owners see product reports; developers only assigned reports).

## 4. Verification / Testing

### Django automated test
- Run all tests:
    - `python manage.py test tests`
- For specific module:
  - `python manage.py test tests.test_crud`    : life-cycle transitions and permission checks.
  - `python manage.py test tests.test_view`    : filters, status querying, pagination, report details.
  - `python manage.py test tests.test_comment` : comment creation/listing behavior.

(These confirm life-cycle transitions, role-based access, report filtering, and comment behavior.)

### Manual smoke tests
1. Create product/user via shell or admin.
2. Create report via `POST /report/`.
3. Log in as owner and run a state transition (OPEN, ASSIGN, etc.) using `PATCH /report/<id>/`.
4. Log in as developer and run developer actions (FIX/CANNOT_REPRODUCE).
5. Confirm `GET /report/` results and `/report/<id>/comments/`.


## 4.1 Example API usage (Python requests)
Install requests: `pip install requests`

Use the same host to run the server and store it as BASE_URL:
```python
BASE_URL = 'http://127.0.0.1:8000'
```

### 4.1.1 Creating users (Product Owner and Developer)
1. Start Django shell:
   - `python manage.py shell`
2. In shell:
   ```python
   from BetaTrax.models import Product, Employee

   product = Product.objects.create(name='Example Product')

   owner = Employee.objects.create_user(
       email='owner@example.com',
       password='ownerpassword',
       role='PRODUCT_OWNER',
       product=product.id,
   )

   developer = Employee.objects.create_user(
       email='developer@example.com',
       password='developerpassword',
       role='DEVELOPER',
       product=product.id,
   )
   ```
3. Exit shell with `exit()`.

### 4.1.2 Tester create report
```python
import requests

resp = requests.post(
    f'{BASE_URL}/report/',
    data={
        'title': 'Sample bug',
        'description': 'App crashes on save',
        'reproduce_steps': 'Open app, click Save, crash',
        'product': 1,
        'tester_id': 'tester1',
        'tester_email': 'tester@example.com',
    },
)
print('Create report', resp.status_code, resp.text)
```

### 4.1.3 Owner login
```python
owner_session = requests.Session()
owner_resp = owner_session.post(
    f'{BASE_URL}/login/',
    data={'email': 'owner@example.com', 'password': 'ownerpassword'},
)
print('Owner login', owner_resp.status_code)
```

### 4.1.4 Fetch reports (owner)
```python
list_resp = owner_session.get(f'{BASE_URL}/report/?status=NEW')
print('NEW reports', list_resp.status_code, list_resp.json())
```

### 4.1.5 Open report (owner action)
```python
open_resp = owner_session.patch(
    f'{BASE_URL}/report/1/',
    json={'action': 'OPEN', 'severity': 3, 'priority': 2},
)
print('Open report', open_resp.status_code)

list_resp = owner_session.get(f'{BASE_URL}/report/?status=OPENED')
print('Opened reports', list_resp.status_code, list_resp.json())
```

### 4.1.6 Developer login + assign + fix report
```python
dev_session = requests.Session()

dev_login = dev_session.post(
    f'{BASE_URL}/login/',
    data={'email': 'developer@example.com', 'password': 'developerpassword'},
)
print('Developer login', dev_login.status_code)

list_resp = dev_session.get(f'{BASE_URL}/report/?status=OPENED')
print('Opened reports', list_resp.status_code, list_resp.json())

assign_resp = dev_session.patch(
    f'{BASE_URL}/report/1/',
    json={'action': 'ASSIGN'},
)
print('Assign report', assign_resp.status_code)

list_resp = dev_session.get(f'{BASE_URL}/report/?status=ASSIGNED')
print('Assigned reports', list_resp.status_code, list_resp.json())

fix_resp = dev_session.patch(
    f'{BASE_URL}/report/1/',
    json={'action': 'FIX'},
)
print('Fix report', fix_resp.status_code)

list_resp = dev_session.get(f'{BASE_URL}/report/?status=FIXED')
print('Fixed reports', list_resp.status_code, list_resp.json())
```

### 4.1.7 Resolve report (owner)
```python
resolve_resp = owner_session.patch(
    f'{BASE_URL}/report/1/',
    json={'action': 'RESOLVE'},
)
print('Resolve report', resolve_resp.status_code)

list_resp = owner_session.get(f'{BASE_URL}/report/')
print('All reports', list_resp.status_code, list_resp.json())
```
