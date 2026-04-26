# BetaTrax Defect Report Management System

## 1. Quick Start

> [!WARNING]
> The default configuration is meant for development environment or internal use. When deployed in production, make sure:
> 1. Replace `SECRET_KEY`, disable `DEBUG`, configure `ALLOWED_HOSTS` and CSRF settings in `project/settings.py`.
> 2. Configure proper insulation / rate limiting for nginx gateway on sensitive interfaces, like `admin/`, `login/`, `docs/`.

### Docker

`docker compose up`

This spins up the app with a postgres service. Please refer to `docker-compose.yml` for common configurations.

> [!NOTE]
> BASE_URL is http://localhost:8080/ (localhost is the default tenant domain)

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

## 3.1 Supported Functionality (Sprint 1)

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
- `GET /report/` with query params (return all filtered reports):
  - `status` (any `ReportStatus` value or omitted)
  - `search` (title contains)
  - `sort` (`-updated_at`, `-severity`, `-priority`)
  - `page` (1-based, 20 items/page)
- `GET /report/<id>/` returns full report details.

### Comments
- `GET /report/<id>/comments/` returns comments for report (ordered by newest first).
- `POST /report/<id>/comments/` adds comment as current authenticated user.
  - Required field: `content`
- (Updated in Sprint 2 with ordering and required field validation)

### Authentication
- `POST /login/` with `email`, `password`.
- `POST /logout/`.
- All report and comment endpoints require logged-in users (403 otherwise), except report creation.

### Implementation Details
- Status transition validation is enforced in `ReportView.patch` via `ReportAction` and `ReportStatus`.
- People management via `Employee` model with role guard in report access (owners see product reports; developers only assigned reports).

## 3.2 Supported Functionality (Sprint 2)

### Employee Management
- `GET /employee/<id>/` returns employee details (id, email, role, product) for authenticated users.
- `PATCH /employee/<id>/` allows employees to assign themselves to a product (requires self-access, product must not have an owner).
  - Required field in JSON body: `product` (product ID)

### Products
- `GET /product/` list products with query param:
  - `page` (1-based, 20 items/page, requires login)
  - Returns fields: `id`, `name`, `owner`, `created_at`, `updated_at`
- `POST /product/` create product (requires PRODUCT_OWNER role)
  - Required field: `name`

## 4. Verification / Testing (Sprint 3)

### Django automated test
- Run all tests:
    - `docker compose exec betatrax uv run manage.py test tests`
- For specific module:
  - `docker compose exec betatrax uv run manage.py test tests.test_crud`    : life-cycle transitions and permission checks.
  - `docker compose exec betatrax uv run manage.py test tests.test_view`    : filters, status querying, pagination, report details, developer effectiveness metric.
  - `docker compose exec betatrax uv run manage.py test tests.test_comment` : comment creation/listing behavior.
  - `docker compose exec betatrax uv run manage.py test tests.test_product` : product creation/listing/assignment behavior.

(These confirm life-cycle transitions, role-based access, report filtering, and comment behavior.)

### API documentation
Access swagger-ui by `http://localhost:8080/docs/`