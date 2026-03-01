# Office Management System (OMS) - Project Plan

## Project Overview
A full-stack, end-to-end Office Management System built with:
- **Backend:** Django (Python)
- **Frontend:** Jinja2 Templating Engine
- **Database:** PostgreSQL (user-provided, existing schema)
- **Styling:** Bootstrap 5 + Custom CSS

---

## ⚠️ Critical Pre-Start Decisions

Before writing any code, the following must be decided and acted on:

1. **Existing PostgreSQL Schema** — Since the database is user-provided:
   - Run `python manage.py inspectdb` to auto-generate models from existing schema
   - Use `managed = False` on models mapping to existing tables OR use `--fake-initial` on first migration
   - Never run `migrate` blindly on a production database

2. **`AUTH_USER_MODEL` must be set FIRST** — Set `AUTH_USER_MODEL = 'accounts.CustomUser'` in `settings.py` before the very first migration. Changing it later breaks everything.

3. **Dual Template Backends** — Django Admin uses its own template engine. Jinja2 must be added as a **second** backend, NOT a replacement, to avoid breaking the admin panel:
   ```python
   TEMPLATES = [
       {
           "BACKEND": "django.template.backends.jinja2.Jinja2",
           "DIRS": [BASE_DIR / "templates/jinja2"],
           "APP_DIRS": True,
           "OPTIONS": {"environment": "oms_project.jinja2.environment"},
       },
       {
           "BACKEND": "django.template.backends.django.DjangoTemplates",
           "DIRS": [],
           "APP_DIRS": True,
           "OPTIONS": {"context_processors": [...]},
       },
   ]
   ```

4. **PDF Library** — Use **ReportLab only**. WeasyPrint requires heavy system-level dependencies (Cairo, Pango, GLib) that complicate deployment. ReportLab is pure Python.

5. **Async Tasks** — Use **Celery + Redis** for deadline notifications, bulk payroll, and all email sending.

6. **Email Backend** — Password reset and notifications require SMTP. Configure SendGrid (production) or Gmail (dev) before testing auth flows.

---

## Phase 1: Project Setup & Configuration

### 1.1 Environment Setup
- [ ] Create virtual environment (`venv`)
- [ ] Install required packages:
  - `django>=4.2`
  - `psycopg2-binary` (PostgreSQL adapter)
  - `django-jinja` (Jinja2 backend integration)
  - `Pillow` (image handling)
  - `python-decouple` (environment variables)
  - `django-crispy-forms` + `crispy-bootstrap5`
  - `whitenoise` (static files)
  - `reportlab` (PDF generation — pure Python, no system deps)
  - `celery` (async task queue)
  - `redis` (Celery broker)
  - `django-axes` (login rate limiting / brute force protection)
  - `sentry-sdk` (error monitoring in production)
- [ ] Create `requirements/base.txt`, `requirements/dev.txt`, `requirements/prod.txt`
- [ ] Setup `.env` file for secrets (never commit to git)
- [ ] Add `.gitignore` covering `.env`, `__pycache__`, `media/`, `*.pyc`

### 1.2 Django Project Initialization
- [ ] Create Django project: `oms_project`
- [ ] Set `AUTH_USER_MODEL = 'accounts.CustomUser'` in `settings.py` **immediately — before first migration**
- [ ] Configure `settings/base.py`:
  - Dual template backends: Jinja2 (app templates) + Django (admin) — see Critical Pre-Start section
  - Connect **PostgreSQL** database via `.env`
  - Configure static & media file paths
  - Set `TIME_ZONE` and `LANGUAGE_CODE`
  - Configure `EMAIL_BACKEND` with SMTP (SendGrid / Gmail)
  - Configure `CELERY_BROKER_URL = 'redis://localhost:6379/0'`
  - Configure `django-axes` for brute force protection (lock after 5 failed attempts)
  - Configure `LOGGING` for file-based error logging (`logs/django.log`)
- [ ] Split settings into `settings/base.py`, `settings/dev.py`, `settings/prod.py`
- [ ] Create `oms_project/jinja2.py` — custom Jinja2 environment (globals: `url`, `static`, `csrf_input`; filters: `date_format`, `currency_format`)
- [ ] Create `oms_project/celery.py` and import in `__init__.py`

### 1.3 Email Backend Configuration
- [ ] Configure SMTP in `.env`: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`
- [ ] Use **SendGrid** for production, Gmail for development only
- [ ] Test with Django's `send_mail` before wiring into views

### 1.4 Seed Data & Superuser Strategy
- [ ] Create superuser via `python manage.py createsuperuser`
- [ ] Create `management/commands/seed_data.py` to populate:
  - Default roles (Admin, HR, Manager, Employee)
  - Default leave types (Annual, Sick, Casual)
  - Default asset & document categories
  - Sample department(s)
- [ ] Document in `README.md` under "Getting Started"

---

## Phase 2: Database Design (PostgreSQL)

### 2.1 Existing Database Strategy
- [ ] Run `python manage.py inspectdb > models_dump.py` to inspect existing schema
- [ ] Review and clean up auto-generated models
- [ ] Decide per table: `managed = True` (Django controls) or `managed = False` (existing table, no migrations)
- [ ] Run `python manage.py migrate --fake-initial` for tables that already exist
- [ ] Document which tables are Django-managed vs pre-existing

### 2.2 Core Models

#### `accounts` App
| Model | Fields |
|-------|--------|
| `CustomUser` | id, username, email, password, role (FK), department (FK), profile_picture, phone, is_active, date_joined |
| `Role` | id, name (choices: Admin / HR / Manager / Employee) |
| `Department` | id, name, manager (FK→Employee), created_at |

> ⚠️ `CustomUser` must extend `AbstractBaseUser` or `AbstractUser`. Set `AUTH_USER_MODEL` before first migration.

#### `employees` App
| Model | Fields |
|-------|--------|
| `Employee` | id, user (OneToOne→CustomUser), department (FK), designation (FK), hire_date, salary, address, NIC, emergency_contact_name, emergency_contact_phone |
| `Designation` | id, title, department (FK), level |

#### `attendance` App
| Model | Fields |
|-------|--------|
| `Attendance` | id, employee (FK), date, check_in, check_out, status (Present/Absent/Late/Half-Day), notes — **unique constraint: employee + date** |
| `LeaveRequest` | id, employee (FK), leave_type (FK), start_date, end_date, reason, status (Pending/Approved/Rejected), approved_by (FK→CustomUser), applied_at |
| `LeaveType` | id, name, max_days_per_year, is_paid |
| `LeaveBalance` | id, employee (FK), leave_type (FK), year, total_days, used_days, remaining_days |

#### `payroll` App
| Model | Fields |
|-------|--------|
| `Payroll` | id, employee (FK), month, year, basic_salary, total_allowances, total_deductions, net_salary, status (Draft/Generated/Paid), generated_by (FK), generated_at — **unique constraint: employee + month + year** |
| `Allowance` | id, payroll (FK), name, amount |
| `Deduction` | id, payroll (FK), name, amount |
| `PayrollTemplate` | id, employee (FK), default_allowances (JSON), default_deductions (JSON) |

#### `projects` App
| Model | Fields |
|-------|--------|
| `Project` | id, name, description, start_date, end_date, status (Planning/Active/On Hold/Completed), manager (FK→Employee), budget, created_at |
| `Task` | id, project (FK), assigned_to (FK→Employee), title, description, priority (Low/Medium/High/Critical), status (To-Do/In Progress/Review/Done), due_date, completed_at |
| `ProjectMember` | id, project (FK), employee (FK), role |

#### `notifications` App *(required for deadline alerts & in-app events)*
| Model | Fields |
|-------|--------|
| `Notification` | id, recipient (FK→CustomUser), title, message, type (info/warning/alert), is_read, created_at, link |

#### `announcements` App
| Model | Fields |
|-------|--------|
| `Announcement` | id, title, content, created_by (FK), target_department (FK, nullable = company-wide), created_at, is_active, is_pinned |

#### `assets` App
| Model | Fields |
|-------|--------|
| `Asset` | id, name, category (FK), serial_number, assigned_to (FK→Employee, nullable), purchase_date, status (Available/Assigned/Under Repair/Disposed), condition, value |
| `AssetCategory` | id, name |
| `AssetHistory` | id, asset (FK), employee (FK), assigned_at, returned_at, notes |

#### `documents` App
| Model | Fields |
|-------|--------|
| `Document` | id, title, file, uploaded_by (FK), department (FK, nullable), category (FK), version (int, default=1), created_at, updated_at |
| `DocumentVersion` | id, document (FK), file, version, uploaded_by (FK), uploaded_at, notes |
| `DocumentCategory` | id, name |

#### `audit` App *(new — tracks all important actions)*
| Model | Fields |
|-------|--------|
| `AuditLog` | id, user (FK), action, model_name, object_id, timestamp, ip_address |

---

## Phase 3: Application Architecture

### 3.1 Django Apps Structure
```
oms_project/
│
├── manage.py
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── .env                          # Never commit to git
├── .gitignore
├── plan.md
│
├── oms_project/                  # Main project config
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── jinja2.py                 # Custom Jinja2 environment & globals
│   ├── celery.py                 # Celery app config
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── accounts/                     # Auth & User Management
├── employees/                    # Employee Records
├── attendance/                   # Attendance & Leaves
├── payroll/                      # Salary & Payroll
├── projects/                     # Projects & Tasks
├── notifications/                # In-app Notifications
├── announcements/                # Company Announcements
├── assets/                       # Asset Management
├── documents/                    # Document Management
├── audit/                        # Audit Log
├── dashboard/                    # Central Dashboard
│
├── static/                       # CSS, JS, Images
│   ├── css/
│   ├── js/
│   └── images/
│
├── media/                        # Uploaded files (local dev only)
│
├── logs/                         # Django log files
│   └── django.log
│
└── templates/
    └── jinja2/                   # All Jinja2 templates go here
        ├── base.html
        ├── base_auth.html        # Minimal layout for login/reset pages
        ├── dashboard/
        ├── accounts/
        ├── employees/
        ├── attendance/
        ├── payroll/
        ├── projects/
        ├── notifications/
        ├── announcements/
        ├── assets/
        └── documents/
```

### 3.2 Per-App File Structure (each app follows this pattern)
```
app_name/
├── models.py
├── views.py
├── urls.py
├── forms.py
├── admin.py
├── services.py        # Business logic — keep views thin
├── tasks.py           # Celery async tasks
├── signals.py         # Django signals (use sparingly)
└── tests/
    ├── test_models.py
    ├── test_views.py
    └── test_forms.py
```

---

## Phase 4: Features & Modules

### 4.1 Authentication & Authorization
- [ ] Custom login / logout pages (Jinja2)
- [ ] `AUTH_USER_MODEL` set to `accounts.CustomUser` before first migration
- [ ] Role-Based Access Control (RBAC) using Django permissions + custom decorators:
  - **Super Admin** → Full access to everything
  - **HR Manager** → Employees, payroll, attendance, leave approvals
  - **Project Manager** → Projects, tasks, team members
  - **Employee** → Own profile, own attendance, own tasks, own payslips
- [ ] Password reset via email (SMTP configured)
- [ ] `django-axes` rate limiting: lock after 5 failed login attempts
- [ ] Session expiry configuration
- [ ] First superuser created via `createsuperuser` + documented in README

### 4.2 Dashboard
- [ ] Role-specific dashboard views (one view, context varies by role)
- [ ] Summary widgets:
  - Total employees / active employees
  - Present today / Absent today / On Leave today
  - Pending leave requests (HR view)
  - Active projects / overdue tasks
  - Upcoming deadlines (next 7 days)
- [ ] Charts (Chart.js):
  - Attendance trends (last 30 days)
  - Department headcount (doughnut)
  - Project status distribution (bar)
  - Monthly payroll summary (line)
- [ ] Unread notifications badge in navbar

### 4.3 Employee Management
- [ ] Add / Edit / Soft-deactivate employees (set `is_active=False` — never hard delete)
- [ ] Employee profiles with photo upload (validate file type & size with Pillow)
- [ ] Department & designation CRUD
- [ ] Employee directory with server-side search & filter (by dept, designation, status)
- [ ] Server-side paginated list (Django `Paginator`) — not just DataTables
- [ ] Export employee data (CSV via Python `csv` module, PDF via ReportLab)

### 4.4 Attendance Management
- [ ] Mark daily attendance (Admin / HR bulk mark)
- [ ] Employee self check-in / check-out (time-stamped, one per day enforced by unique constraint)
- [ ] Prevent duplicate attendance entries (`unique_together: employee + date`)
- [ ] Attendance calendar view per employee (FullCalendar.js)
- [ ] Leave request submission by employee
- [ ] Leave balance tracking per employee per leave type (`LeaveBalance` model)
- [ ] Leave approval / rejection workflow with email notification (Celery async)
- [ ] Monthly & weekly attendance reports (exportable CSV / PDF)

### 4.5 Payroll Management
- [ ] Payroll template per employee (default allowances / deductions stored in `PayrollTemplate`)
- [ ] Generate monthly payroll (uses template as base, editable before finalizing)
- [ ] Auto-calculate: `net_salary = basic_salary + total_allowances - total_deductions`
- [ ] Prevent duplicate payroll: `unique_together: employee + month + year`
- [ ] Payroll status workflow: Draft → Generated → Paid
- [ ] Payslip PDF generation via ReportLab
- [ ] Bulk payroll generation via Celery async task (avoids request timeout)
- [ ] Payroll history per employee (paginated)

### 4.6 Project & Task Management
- [ ] Create / edit / archive projects
- [ ] Assign team members to projects (`ProjectMember`)
- [ ] Task creation with priority (Low / Medium / High / Critical)
- [ ] Task status workflow: To-Do → In Progress → Review → Done
- [ ] Project progress = `(completed tasks / total tasks) × 100`
- [ ] Deadline notifications via Celery beat (daily scheduled scan)
- [ ] In-app `Notification` created when task is assigned or deadline is within 3 days

### 4.7 Notifications (In-App)
- [ ] `Notification` model per user
- [ ] Notification bell in navbar with unread count badge
- [ ] Mark as read (single + mark all as read)
- [ ] Notification triggers: task assigned, leave approved/rejected, deadline alert, new announcement
- [ ] Celery beat task: daily scan for upcoming deadlines → auto-create notifications

### 4.8 Announcements
- [ ] Post company-wide or department-specific announcements
- [ ] Pin / unpin announcements
- [ ] Announcement visible on employee dashboard
- [ ] Email blast to target department on post (Celery async)
- [ ] Paginated announcement history

### 4.9 Asset Management
- [ ] Add / edit / track office assets
- [ ] Assign assets to employees (creates `AssetHistory` record)
- [ ] Asset return workflow (updates `AssetHistory` with return date)
- [ ] Asset condition & status tracking
- [ ] Full asset history per asset (who had it and when)

### 4.10 Document Management
- [ ] Upload & categorize documents (validate MIME type server-side: PDF, DOCX, XLSX, PNG, JPG)
- [ ] Enforce max file size (e.g., 10MB)
- [ ] Department-wise access control
- [ ] Document search by title / category / department
- [ ] Document versioning — upload new version, keep full history in `DocumentVersion` (not optional)
- [ ] Files stored outside web root; served via Django in dev, nginx in prod

---

## Phase 5: Frontend (Jinja2 Templates)

### 5.1 Jinja2 Configuration
- [ ] Place all app templates in `templates/jinja2/` directory
- [ ] Create `oms_project/jinja2.py` with custom environment:
  - Global functions: `url()`, `static()`, `csrf_input()`
  - Custom filters: `date_format`, `currency_format`, `status_badge`
  - Global context: `request`, `user`, `unread_notifications_count`
- [ ] Django Admin templates remain in default Django template backend (no conflict)

### 5.2 Template Architecture
- [ ] `base.html` → Master layout (topbar, sidebar, main content, footer)
- [ ] `base_auth.html` → Minimal layout for login / password reset pages
- [ ] Role-based sidebar: links shown/hidden based on `user.role`
- [ ] Toast / flash message component (Bootstrap toasts)
- [ ] Reusable Jinja2 macros: form fields, stat cards, pagination, status badges

### 5.3 UI Components
- [ ] Responsive collapsible sidebar
- [ ] Server-side paginated lists + DataTables.js for client-side sort/search
- [ ] Modal dialogs for quick create / edit actions
- [ ] Form validation: HTML5 + Django form errors displayed inline
- [ ] Loading spinners on async actions
- [ ] FullCalendar.js for attendance calendar
- [ ] Chart.js for all analytics charts
- [ ] Notification bell dropdown in topbar with unread badge

### 5.4 Pages List
| Page | URL Pattern | Access |
|------|-------------|--------|
| Login | `/login/` | Public |
| Logout | `/logout/` | Authenticated |
| Password Reset | `/password-reset/` | Public |
| Dashboard | `/dashboard/` | All roles |
| Employee List | `/employees/` | Admin, HR |
| Employee Detail | `/employees/<id>/` | Admin, HR, self |
| Add Employee | `/employees/add/` | Admin, HR |
| Edit Employee | `/employees/<id>/edit/` | Admin, HR |
| Departments | `/employees/departments/` | Admin, HR |
| Attendance | `/attendance/` | Admin, HR |
| My Attendance | `/attendance/me/` | Employee |
| Leave Requests | `/attendance/leaves/` | Admin, HR |
| Apply Leave | `/attendance/leaves/apply/` | Employee |
| Payroll List | `/payroll/` | Admin, HR |
| Generate Payroll | `/payroll/generate/` | Admin, HR |
| Payslip Detail | `/payroll/payslip/<id>/` | Admin, HR, self |
| My Payslips | `/payroll/my-payslips/` | Employee |
| Projects | `/projects/` | Admin, Manager |
| Project Detail | `/projects/<id>/` | Team members |
| Add Project | `/projects/add/` | Admin, Manager |
| Tasks | `/projects/<id>/tasks/` | Team members |
| Announcements | `/announcements/` | All roles |
| Add Announcement | `/announcements/add/` | Admin, HR |
| Assets | `/assets/` | Admin |
| Asset Detail | `/assets/<id>/` | Admin |
| Documents | `/documents/` | All roles (filtered) |
| Upload Document | `/documents/upload/` | Admin, HR, Manager |
| Notifications | `/notifications/` | All roles |
| User Settings | `/settings/` | All roles |

---

## Phase 6: Security Implementation

- [ ] CSRF protection on all POST forms (Django default + Jinja2 `csrf_input()`)
- [ ] Role-based access decorators on every view (`@login_required` + custom `@role_required`)
- [ ] Object-level permission checks (employees can only see their own data)
- [ ] Input validation & sanitization on all forms (Django Forms / ModelForms)
- [ ] Django ORM used everywhere — no raw SQL
- [ ] Secure file uploads: validate MIME type server-side (not just extension), limit file size, store outside web root
- [ ] All secrets in `.env` via `python-decouple` (DB password, secret key, email credentials)
- [ ] `django-axes` rate limiting: lock account after 5 failed login attempts
- [ ] `SECURE_BROWSER_XSS_FILTER`, `X_FRAME_OPTIONS = 'DENY'`, `SECURE_CONTENT_TYPE_NOSNIFF` in prod settings
- [ ] `SECURE_SSL_REDIRECT = True` in production
- [ ] `SESSION_COOKIE_SECURE = True`, `SESSION_COOKIE_HTTPONLY = True`
- [ ] `CSRF_COOKIE_SECURE = True` in production

---

## Phase 7: Async Tasks (Celery + Redis)

- [ ] Configure `oms_project/celery.py` and import in `__init__.py`
- [ ] Redis running as Celery broker (also used for caching)
- [ ] Celery beat scheduler for periodic tasks:
  - **Daily at 8am** — scan tasks with due dates in next 3 days → create notifications
  - **Monthly** — reminder to generate payroll
- [ ] Async tasks:
  - Bulk payroll generation
  - Email sending (leave approval/rejection, announcements, password reset)
  - PDF generation for large reports
- [ ] Monitor Celery tasks with **Flower** (dev only)

---

## Phase 8: Logging & Monitoring

- [ ] Configure Django `LOGGING` in `settings/base.py`:
  - Log `ERROR` and above to file (`logs/django.log`)
  - Log `WARNING` and above to console in dev
- [ ] Integrate **Sentry** (`sentry-sdk`) for production error tracking
- [ ] Log all payroll generation and approval actions to `AuditLog`
- [ ] `AuditLog` model: `user, action, model_name, object_id, timestamp, ip_address`

---

## Phase 9: Testing

### 9.1 Unit Tests
- [ ] Model tests (field validation, `__str__`, computed properties)
- [ ] View tests (status codes, redirects, context data)
- [ ] Form validation tests (valid & invalid data)
- [ ] Permission / RBAC tests (each role accessing each URL)
- [ ] Service layer tests (payroll calculation, leave balance)

### 9.2 Integration Tests
- [ ] Full user login → dashboard flow
- [ ] Payroll generation flow (template → generate → PDF)
- [ ] Leave request → approval → balance update flow
- [ ] Task assignment → notification creation flow
- [ ] Document upload → version update flow

### 9.3 Test Configuration
- [ ] Use a separate test PostgreSQL database
- [ ] Use Django's `TestCase` and `Client`
- [ ] Aim for >80% code coverage (`coverage.py`)

---

## Phase 10: Deployment Preparation

- [ ] Configure `whitenoise` for static files
- [ ] Setup `gunicorn` as WSGI server (`gunicorn oms_project.wsgi:application`)
- [ ] Configure `nginx` as reverse proxy (SSL termination, media file serving)
- [ ] PostgreSQL production configuration (use connection pooling via `pgbouncer` if needed)
- [ ] Redis running as a service (Celery broker)
- [ ] Celery worker running as a `systemd` service
- [ ] Celery beat running as a `systemd` service
- [ ] `prod.py` settings: `DEBUG=False`, `ALLOWED_HOSTS`, `SECURE_SSL_REDIRECT=True`
- [ ] Media files: local nginx serving (small scale) or migrate to **AWS S3 / Cloudflare R2** (production scale)
- [ ] `Dockerfile` + `docker-compose.yml` (web, db, redis, celery services)
- [ ] Automated database backups (`pg_dump` via cron or managed DB service)
- [ ] Document all deployment steps in `README.md`

---

## Technology Stack Summary

| Layer | Technology |
|-------|------------|
| Backend Framework | Django 4.x |
| Templating | Jinja2 (`django-jinja`) |
| Database | PostgreSQL |
| ORM | Django ORM |
| Styling | Bootstrap 5 |
| Charts | Chart.js |
| Tables | DataTables.js |
| Calendar | FullCalendar.js |
| PDF Generation | ReportLab / WeasyPrint |
| Environment Vars | python-decouple |
| Static Files | WhiteNoise |
| Production Server | Gunicorn + Nginx |

---

## Development Timeline (Estimated)

| Phase | Duration |
|-------|----------|
| Phase 1 - Setup & Configuration | 1 day |
| Phase 2 - Database Models | 2 days |
| Phase 3 - App Structure | 1 day |
| Phase 4 - Core Features | 10–14 days |
| Phase 5 - Frontend / Templates | 5–7 days |
| Phase 6 - Security | 1–2 days |
| Phase 7 - Testing | 2–3 days |
| Phase 8 - Deployment | 1–2 days |
| **Total** | **~4 weeks** |

---

## Notes
- All sensitive credentials must be stored in the `.env` file and never committed to version control
- Follow Django best practices and PEP8 coding standards throughout
- Use Django migrations for all database schema changes
- Keep business logic in models / services, not in views
- Use Django class-based views (CBVs) where applicable
- Jinja2 templates must be placed in the `templates/` directory and configured in `settings.py`
- Static files served via WhiteNoise in production
- Use Django signals for cross-app event handling (e.g., payroll auto-generation on attendance close)

