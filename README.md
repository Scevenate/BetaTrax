# BetaTrax Defect Report Management System

## 1. Quick Start

### Docker
1. Build and start services:
   - `docker compose up --build`
2. The Django app will listen on `http://localhost:8000`.
3. Data persists in `./data/postgres` (PostgreSQL) and `./data/migrations` (Django migrations).

### Local (Python manage.py)
1. Create a virtual environment with Python 3.13+, activate it.
2. Install dependencies:
   - `pip install django psycopg[binary]`
3. Run migrations:
   - `python manage.py makemigrations BetaTrax`
   - `python manage.py migrate`
4. Start server:
   - `python manage.py runserver`
5. Data persists in `./db.sqlite3`

## 2. Environment / Components
- Web framework: Django 6.x
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
- `ASSIGN`: on `OPENED`/`REOPENED` -> sets `assigned_to`, status `ASSIGNED`.
- `REOPEN`: on `FIXED` -> status `REOPENED`.
- `RESOLVE`: on `FIXED` -> status `RESOLVED`.

### Developer actions (via `PATCH /report/<id>/`)
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

## 3.1. Additional functions
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

### Django tests
- test modules:
  - `tests/test_crud.py`: life-cycle transitions and permission checks.
  - `tests/test_view.py`: product owner filters, status querying, pagination, report details.
  - `tests/test_comment.py`: comment creation/listing behavior.

### Manual smoke tests
1. Create product/user via shell or admin.
2. Create report via `POST /report/`.
3. Log in as owner and run a state transition (OPEN, ASSIGN, etc.) using `PATCH /report/<id>/`.
4. Log in as developer and run developer actions (FIX/CANNOT_REPRODUCE).
5. Confirm `GET /report/` results and `/report/<id>/comments/`.

## 4.1. Examples Usage

### Creating users (Product Owner and Developer)
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

### Running tests
- Run all tests:
    - `python manage.py test tests`
- For specific module:
  - `python manage.py test tests.test_crud`
  - `python manage.py test tests.test_view`
  - `python manage.py test tests.test_comment`

(These confirm life-cycle transitions, role-based access, report filtering, and comment behavior.)
