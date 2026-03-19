# 🏢 Office Management System (OMS)

A full-featured, role-based Office Management System built with **Django 4.2+**, **Jinja2 templates**, **PostgreSQL**, **Celery**, and **Bootstrap 5**. Covers HR, attendance, payroll, projects, assets, documents, announcements, and notifications — all in one system.

---

## 📑 Table of Contents

1. [Features Overview](#features-overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Roles & Permissions](#roles--permissions)
5. [Setup & Installation](#setup--installation)
6. [Environment Variables](#environment-variables)
7. [Database Setup](#database-setup)
8. [Running the Project](#running-the-project)
9. [Seed Demo Data](#seed-demo-data)
10. [All URL Routes](#all-url-routes)
11. [Module Breakdown](#module-breakdown)
12. [Celery & Background Tasks](#celery--background-tasks)
13. [Security Features](#security-features)
14. [Audit Logging](#audit-logging)
15. [Static & Media Files](#static--media-files)
16. [Production Deployment](#production-deployment)
17. [Demo Login Accounts](#demo-login-accounts)
18. [Common Management Commands](#common-management-commands)
19. [Jinja2 Environment Reference](#jinja2-environment-reference)

---

## Features Overview

| Module | Features |
|---|---|
| **Authentication** | Login, logout, profile settings, password change, brute-force protection |
| **Dashboard** | Role-specific dashboards (Admin/HR/Manager/Employee), live clock, check-in widget, stat cards |
| **Employees** | Add/edit/deactivate employees, departments, designations, CSV export |
| **Attendance** | Daily check-in/check-out for all roles, attendance history, weekly bar chart, **resignations with HR approval & auto-deactivation on last working date** |
| **Leaves** | Apply for leave, HR/Manager approval & rejection, per-type leave balance tracking |
| **Payroll** | Generate payslips, allowances, deductions, PDF download, employee payslip portal |
| **Projects** | Create projects, assign managers, add/remove team members, progress tracking |
| **Tasks** | Assign tasks to project members only, priority levels, inline status updates |
| **Announcements** | Company-wide or department-targeted announcements, pin/unpin, email notification |
| **Documents** | Upload & version-control documents, department-level categorisation |
| **Assets** | Track company assets, assign to employees, condition & status management |
| **Notifications** | In-app notifications, unread badge, mark as read / mark all as read |
| **Audit Log** | Auto-log all create/update/delete actions with user identity and IP address |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Django 4.2, Python 3.10+ |
| **Templates** | Jinja2 (via django-jinja), Bootstrap 5.3, Bootstrap Icons |
| **Database** | PostgreSQL 14+ |
| **Task Queue** | Celery + Redis |
| **Brute-Force Protection** | django-axes |
| **Static Files** | WhiteNoise |
| **PDF Generation** | ReportLab |
| **Email** | Django SMTP (Gmail / SendGrid) |
| **Error Monitoring** | Sentry SDK |
| **Dev Tools** | Flower (Celery UI), django-extensions |
| **Config Management** | python-decouple (.env based) |
| **Image Handling** | Pillow |

---

## Project Structure

```
oms/
├── manage.py
├── .env                          # Environment variables — never commit this
├── README.md
├── pytest.ini
│
├── requirements/
│   ├── base.txt                  # Core production dependencies
│   ├── dev.txt                   # Dev extras: flower, django-extensions
│   └── prod.txt                  # Production-only extras
│
├── oms_project/                  # Django project configuration
│   ├── settings/
│   │   ├── __init__.py           # Imports dev.py by default
│   │   ├── base.py               # Shared settings for all environments
│   │   ├── dev.py                # Development: DEBUG=True, eager Celery
│   │   └── prod.py               # Production overrides
│   ├── urls.py                   # Root URL config
│   ├── jinja2.py                 # Jinja2 environment: globals, filters, csrf
│   ├── celery.py                 # Celery application config
│   ├── asgi.py
│   └── wsgi.py
│
├── accounts/                     # Custom user model, roles, departments
├── employees/                    # Employee profiles, designations
├── attendance/                   # Check-in/out, leaves, leave balances
├── payroll/                      # Payroll generation, payslips
├── projects/                     # Projects, tasks, team members
├── announcements/                # Announcements with department targeting
├── assets/                       # Company asset inventory
├── documents/                    # Document upload & versioning
├── notifications/                # In-app notification system
├── audit/                        # Audit trail for all user actions
├── dashboard/                    # Role-specific dashboard aggregation views
│
├── templates/
│   └── jinja2/                   # All Jinja2 HTML templates
│       ├── base.html             # Master layout: sidebar, topbar, flash messages
│       ├── accounts/
│       ├── attendance/
│       ├── employees/
│       ├── projects/
│       ├── payroll/
│       ├── announcements/
│       ├── assets/
│       ├── documents/
│       ├── notifications/
│       └── dashboard/
│
├── static/                       # Source static files (CSS, JS, images)
├── staticfiles/                  # Collected static files — auto-generated, do not edit
├── media/                        # User-uploaded files (profile pics, documents)
└── logs/
    └── django.log                # Application error log
```

---

## Roles & Permissions

The system has **4 roles**. Every user must have exactly one role. Django superusers are automatically treated as Admin.

### 🔴 Admin
- Full access to all modules and data
- Access to Django `/admin/` panel
- Sees all employees, all projects, all payroll, all leave requests, full audit log
- Can add, edit, and deactivate employees; manage departments and designations
- Can generate payroll for any employee
- Has personal check-in/check-out widget on dashboard

### 🟠 HR
- Sees all employees, attendance records, and leave requests
- Can approve or reject leave requests for any employee
- Can create announcements — company-wide or targeted to a specific department
- Can upload and manage documents
- Can view payroll for all employees
- Has personal check-in/check-out widget on dashboard

### 🟡 Manager
- Sees only projects they manage **or** are a member of
- Can add and remove team members from their own projects
- Can create tasks — the "Assign To" dropdown only shows current project members
- Sees leave requests for all employees in their managed projects (dashboard + leave page)
- Can approve or reject leave requests for their team
- Has personal check-in/check-out widget on dashboard

### 🟢 Employee
- Sees only projects they are explicitly added to as a `ProjectMember`
- Can check in and check out every day (all roles can check in — no restriction)
- Can apply for leave; sees their own leave history and remaining balances
- Sees only announcements targeted to their department, or company-wide ones
- Sees their own attendance history, weekly bar chart, days-in-company counter
- Sees their own payslips
- Sees tasks assigned to them

---

## Setup & Installation

### Prerequisites

- Python 3.10 or higher
- PostgreSQL 14 or higher
- Redis (for Celery; not needed in dev mode — see [Celery section](#celery--background-tasks))
- Git

### Step 1 — Clone the repository

```bash
git clone https://github.com/your-username/oms.git
cd oms
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Step 3 — Install dependencies

```bash
# Development (recommended)
pip install -r requirements/dev.txt

# Production
pip install -r requirements/prod.txt
```

### Step 4 — Create the `.env` file

```bash
cp .env.example .env   # or create manually — see Environment Variables section below
```

### Step 5 — Create the PostgreSQL database

```bash
psql -U postgres
```

```sql
CREATE DATABASE oms_db;
CREATE USER oms_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE oms_db TO oms_user;
\q
```

### Step 6 — Run migrations

```bash
python manage.py migrate
```

### Step 7 — Seed demo data

```bash
python manage.py seed_data
```

This creates 10 users across all 4 roles, 5 projects, 30 days of attendance records, payroll for 3 months, announcements, assets, documents, and notifications.

### Step 8 — Start the server

```bash
python manage.py runserver
```

Open your browser: **http://127.0.0.1:8000**
Log in with: **`admin`** / **`admin123`**

---

## Environment Variables

Create `/oms/.env` with the following content:

```env
# ── Django Core ───────────────────────────────────────────────────
SECRET_KEY=your-very-long-random-secret-key-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# ── PostgreSQL Database ───────────────────────────────────────────
DB_NAME=oms_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432

# ── Email (Gmail SMTP) ────────────────────────────────────────────
# Generate a Gmail App Password at: myaccount.google.com/apppasswords
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
DEFAULT_FROM_EMAIL=OMS System <your-email@gmail.com>

# ── Celery / Redis ────────────────────────────────────────────────
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# ── Sentry (production error tracking — leave blank in development) ──
SENTRY_DSN=
```

> ⚠️ **Never commit `.env` to version control.** Add it to `.gitignore`.

---

## Database Setup

Every app manages its own tables through Django migrations:

| App | Models |
|---|---|
| `accounts` | `CustomUser`, `Role`, `Department` |
| `employees` | `Employee`, `Designation` |
| `attendance` | `Attendance`, `LeaveType`, `LeaveBalance`, `LeaveRequest` |
| `payroll` | `Payroll` |
| `projects` | `Project`, `ProjectMember`, `Task` |
| `announcements` | `Announcement` |
| `assets` | `AssetCategory`, `Asset` |
| `documents` | `DocumentCategory`, `Document`, `DocumentVersion` |
| `notifications` | `Notification` |
| `audit` | `AuditLog` |

```bash
# Apply all migrations
python manage.py migrate

# After changing a model
python manage.py makemigrations <app_name>
python manage.py migrate
```

---

## Running the Project

### Development server

```bash
source venv/bin/activate
python manage.py runserver
```

### Accessible on your local network

```bash
python manage.py runserver 0.0.0.0:8000
```

### Celery worker (needed for emails in production)

```bash
# New terminal
celery -A oms_project worker --loglevel=info
```

### Celery beat (needed for scheduled tasks)

```bash
# Another terminal
celery -A oms_project beat --loglevel=info
```

### Flower — Celery monitoring UI

```bash
celery -A oms_project flower --port=5555
# Visit: http://localhost:5555
```

---

## Seed Demo Data

The `seed_data` management command populates the entire database with realistic demo data.
It is **fully idempotent** — running it multiple times will not create duplicates.

```bash
# Normal seed (safe to run multiple times)
python manage.py seed_data

# Wipe everything and start completely fresh
python manage.py seed_data --flush
```

### What gets created

| Model | Count |
|---|---|
| Roles | 4 |
| Departments | 5 |
| Designations | 8 |
| Leave Types | 5 |
| Asset Categories | 6 |
| Document Categories | 5 |
| Users + Employee Profiles | 10 |
| Leave Balances | 50 (10 employees × 5 types) |
| Attendance Records | ~200 (30 weekdays × 10 employees) |
| Leave Requests | 10 (mix of Pending / Approved / Rejected) |
| Payroll Records | 30 (3 months × 10 employees) |
| Projects | 5 |
| Project Members | ~15 |
| Tasks | 25 (5 per project) |
| Announcements | 5 (3 pinned) |
| Assets | 7 |
| Documents | 5 |
| Notifications | 25 |

---

## All URL Routes

### Accounts — `/accounts/`

| URL | Name | Description |
|---|---|---|
| `/accounts/login/` | `accounts:login` | Login page |
| `/accounts/logout/` | `accounts:logout` | Logout |
| `/accounts/settings/` | `accounts:settings` | Profile & password update |

### Dashboard — `/dashboard/`

| URL | Name | Description |
|---|---|---|
| `/dashboard/` | `dashboard:index` | Role-specific home dashboard |
| `/dashboard/audit/` | `dashboard:audit_log` | Full audit log (Admin only) |

### Employees — `/employees/`

| URL | Name | Description |
|---|---|---|
| `/employees/` | `employees:list` | Employee list with search & filter |
| `/employees/add/` | `employees:add` | Add new employee |
| `/employees/<pk>/` | `employees:detail` | Employee detail profile |
| `/employees/<pk>/edit/` | `employees:edit` | Edit employee |
| `/employees/<pk>/deactivate/` | `employees:deactivate` | Deactivate employee |
| `/employees/export/csv/` | `employees:export_csv` | Export as CSV |
| `/employees/departments/` | `employees:departments` | Manage departments |

### Attendance — `/attendance/`

| URL | Name | Description |
|---|---|---|
| `/attendance/` | `attendance:list` | Today's attendance (HR/Admin) |
| `/attendance/me/` | `attendance:my` | My attendance history |
| `/attendance/checkin/` | `attendance:checkin` | POST: Check in |
| `/attendance/checkout/` | `attendance:checkout` | POST: Check out |
| `/attendance/leaves/` | `attendance:leaves` | Leave requests (HR = all, Manager = team) |
| `/attendance/leaves/apply/` | `attendance:apply_leave` | Apply for leave |
| `/attendance/leaves/<pk>/approve/` | `attendance:approve_leave` | POST: Approve |
| `/attendance/leaves/<pk>/reject/` | `attendance:reject_leave` | POST: Reject |

### Payroll — `/payroll/`

| URL | Name | Description |
|---|---|---|
| `/payroll/` | `payroll:list` | All payroll records |
| `/payroll/generate/` | `payroll:generate` | Generate payroll |
| `/payroll/<pk>/` | `payroll:payslip` | View payslip |
| `/payroll/my/` | `payroll:my_payslips` | My payslips |

### Projects — `/projects/`

| URL | Name | Description |
|---|---|---|
| `/projects/` | `projects:list` | Project list (role-filtered) |
| `/projects/add/` | `projects:add` | Create new project |
| `/projects/<pk>/` | `projects:detail` | Project detail: tasks & team |
| `/projects/<pk>/edit/` | `projects:edit` | Edit project |
| `/projects/<pk>/members/add/` | `projects:add_member` | POST: Add team member (Manager/HR/Admin) |
| `/projects/<pk>/members/<mpk>/remove/` | `projects:remove_member` | POST: Remove team member |
| `/projects/<pk>/tasks/add/` | `projects:task_add` | Add task (Assign To = project members only) |
| `/projects/tasks/<pk>/status/` | `projects:task_status` | POST: Update task status inline |

### Announcements — `/announcements/`

| URL | Name | Description |
|---|---|---|
| `/announcements/` | `announcements:list` | List (department-filtered) |
| `/announcements/add/` | `announcements:add` | Create announcement (HR/Admin) |
| `/announcements/<pk>/pin/` | `announcements:pin` | Toggle pin |
| `/announcements/<pk>/delete/` | `announcements:delete` | Soft-delete |

### Assets — `/assets/`

| URL | Name | Description |
|---|---|---|
| `/assets/` | `assets:list` | Asset list |
| `/assets/add/` | `assets:add` | Add asset |
| `/assets/<pk>/` | `assets:detail` | Asset detail |
| `/assets/<pk>/edit/` | `assets:edit` | Edit asset |

### Documents — `/documents/`

| URL | Name | Description |
|---|---|---|
| `/documents/` | `documents:list` | Document list |
| `/documents/upload/` | `documents:upload` | Upload document |
| `/documents/<pk>/` | `documents:detail` | Document + version history |

### Notifications — `/notifications/`

| URL | Name | Description |
|---|---|---|
| `/notifications/` | `notifications:list` | All notifications |
| `/notifications/<pk>/read/` | `notifications:mark_read` | Mark single as read |
| `/notifications/read-all/` | `notifications:read_all` | Mark all as read |

---

## Module Breakdown

### `accounts` — Custom User & Roles
- **Models:** `CustomUser` (extends `AbstractUser`), `Role`, `Department`
- `CustomUser.role` → ForeignKey to `Role` (Admin / HR / Manager / Employee)
- **Properties:** `is_admin`, `is_hr`, `is_manager`, `is_employee`, `role_display`
- Django superusers → `is_admin` always returns `True` regardless of role field
- Users with no role assigned → treated as Employee (safe fallback)

### `employees` — Employee Profiles
- **Models:** `Employee`, `Designation`
- `Employee` → one-to-one with `CustomUser` via `user.employee_profile`
- `Employee.full_name` → `user.get_full_name()`
- `Designation` has a ForeignKey to `Department`

### `attendance` — Check-in / Out & Leaves
- **Models:** `Attendance`, `LeaveType`, `LeaveBalance`, `LeaveRequest`
- Check-in/out auto-creates an `Employee` profile if the user doesn't have one (all roles can check in)
- `Attendance.status` choices: `Present`, `Absent`, `Late`, `Half-Day`
- `LeaveBalance` tracks `total_days` and `used_days` per employee, per leave type, per year
- `LeaveRequest.duration_days` → calculated property

### `payroll` — Payroll & Payslips
- **Model:** `Payroll`
- Fields: `basic_salary`, `total_allowances`, `total_deductions`, `net_salary`, `status`, `month`, `year`
- Status flow: `Draft` → `Generated` → `Paid`

### `projects` — Projects, Tasks & Teams
- **Models:** `Project`, `ProjectMember`, `Task`
- `Project.progress` → calculated: `(done_tasks / total_tasks) * 100`
- `TaskForm` dynamically filters `assigned_to` to only project members
- Access: employees can only view projects they are a `ProjectMember` of
- Managers can only manage (add/remove members, add tasks) their own projects

### `announcements` — Targeted Announcements
- **Model:** `Announcement`
- `target_department = NULL` → visible to everyone (company-wide)
- `target_department = X` → only employees in department X see it
- Admin and HR always see all announcements

### `assets` — Company Asset Tracking
- **Models:** `AssetCategory`, `Asset`
- `Asset.status` choices: `Available`, `Assigned`, `Under Repair`, `Disposed`

### `documents` — Document Management
- **Models:** `DocumentCategory`, `Document`, `DocumentVersion`
- Each new file upload creates a new `DocumentVersion` record

### `notifications` — In-App Notifications
- **Model:** `Notification`
- Types: `info`, `warning`, `success`, `error`
- Unread count badge shown in topbar and sidebar
- Created automatically: task assigned, leave decision, added to project

### `audit` — Audit Trail
- **Model:** `AuditLog`
- Fields: `user`, `action`, `model_name`, `object_id`, `timestamp`, `ip_address`
- Call `from audit.services import log_action` in any view to record an event

### `dashboard` — Role-Based Home Page
No models — pure view layer aggregating data from other apps:

| Role | Dashboard Content |
|---|---|
| **Admin / HR** | Stat cards (employees, present today, absent today, pending leaves, active projects, overdue tasks), attendance rate progress bar, today's attendance table, pending leave approval table, own check-in widget |
| **Manager** | My projects with progress bars, team leave requests with approve/reject buttons, overdue tasks count, own check-in widget |
| **Employee** | Live clock, check-in/out widget, days-in-company counter, monthly & weekly present days, weekly attendance bar chart (Mon–Sun with colour-coded status), leave balances with progress bars, pending leave requests, active tasks |

---

## Celery & Background Tasks

### Registered Tasks

| Task | Location | Trigger | What it does |
|---|---|---|---|
| `send_announcement_email` | `announcements/tasks.py` | New announcement posted | Emails all employees in the target department (or all staff for company-wide) |
| `send_leave_decision_email` | `attendance/tasks.py` | Leave approved or rejected | Emails the employee with the HR decision |
| `deactivate_resigned_users` | `attendance/tasks.py` | Celery Beat — daily (optional) | Deactivates users whose approved resignation last working date has passed |
| `check_task_deadlines` | `projects/tasks.py` | Celery Beat — daily | Creates in-app notifications for overdue tasks |

### Development mode — no Redis required

In `settings/dev.py` tasks run **synchronously in the same process**:

```python
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
```

No Celery worker or Redis needed during development.

### Production mode

```bash
# Worker processes tasks from the queue
celery -A oms_project worker --loglevel=info

# Beat sends periodic tasks on schedule
celery -A oms_project beat --loglevel=info
```

---

## Security Features

| Feature | Implementation |
|---|---|
| **Brute-force protection** | `django-axes` — locks account after 5 failed login attempts for 1 hour |
| **CSRF protection** | Django built-in + custom `csrf_input()` Jinja2 global renders the hidden token in every form |
| **Password hashing** | Django PBKDF2 with SHA256 |
| **Role-based access** | Every view checks `user.is_admin`, `user.is_hr`, `user.is_manager`, `user.is_employee` |
| **Project access control** | Employees attempting to access a project they don't belong to are redirected with an error |
| **Announcement filtering** | Employees never see announcements targeted to other departments |
| **Login required** | All views decorated with `@login_required` — unauthenticated requests redirect to login |
| **Resignation enforcement** | Approved resignations deactivate accounts on/after the last working date; optional daily task `deactivate_resigned_users` to auto-enforce |
| **Clickjacking protection** | `XFrameOptionsMiddleware` prevents iframe embedding |
| **Secret key isolation** | `SECRET_KEY` loaded from `.env` via python-decouple — never hardcoded |

---

## Audit Logging

### Log an action in any view

```python
from audit.services import log_action

log_action(request.user, 'Created',     'Employee', str(employee.pk), request)
log_action(request.user, 'Updated',     'Employee', str(pk),          request)
log_action(request.user, 'Deactivated', 'Employee', str(pk),          request)
log_action(request.user, 'Generated',   'Payroll',  str(payroll.pk),  request)
```

### AuditLog model fields

| Field | Description |
|---|---|
| `user` | FK → CustomUser who performed the action |
| `action` | e.g. `Created`, `Updated`, `Deleted`, `Approved`, `Rejected`, `Deactivated` |
| `model_name` | e.g. `Employee`, `Payroll`, `Project`, `LeaveRequest` |
| `object_id` | Primary key of the affected object (stored as string) |
| `timestamp` | Auto-set datetime of when the event occurred |
| `ip_address` | Client IP address extracted from the HTTP request |

View the full searchable audit log at: **`/dashboard/audit/`** (Admin only)

---

## Static & Media Files

### Development
- `static/` files are served automatically by Django's dev server
- `media/` (uploaded files) served via Django's `MEDIA_URL`

### Production
Static files via WhiteNoise (no Nginx required for static):

```bash
python manage.py collectstatic --noinput
# Outputs to: staticfiles/
```

Media files via Nginx:

```nginx
location /media/ {
    alias /path/to/oms/media/;
}
```

---

## Production Deployment

### 1. Set production environment variables

```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECRET_KEY=very-long-random-string-minimum-50-characters
```

### 2. Apply migrations & collect static

```bash
DJANGO_SETTINGS_MODULE=oms_project.settings.prod python manage.py migrate
DJANGO_SETTINGS_MODULE=oms_project.settings.prod python manage.py collectstatic --noinput
```

### 3. Run with Gunicorn

```bash
pip install gunicorn
gunicorn oms_project.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### 4. Nginx reverse proxy config

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /path/to/oms/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /path/to/oms/media/;
    }

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

### 5. Systemd service for Gunicorn

Create `/etc/systemd/system/oms.service`:

```ini
[Unit]
Description=OMS Django Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/oms
EnvironmentFile=/path/to/oms/.env
ExecStart=/path/to/oms/venv/bin/gunicorn \
    oms_project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable oms
sudo systemctl start oms
```

---

## Demo Login Accounts

After running `python manage.py seed_data`:

| Username | Password | Role | Department |
|---|---|---|---|
| `admin` | `admin123` | **Admin / Superuser** | Engineering |
| `sarah_hr` | `pass1234` | **HR** | Human Resources |
| `mike_hr` | `pass1234` | **HR** | Human Resources |
| `ali_mgr` | `pass1234` | **Manager** | Engineering |
| `emma_mgr` | `pass1234` | **Manager** | Marketing |
| `john_emp` | `pass1234` | **Employee** | Engineering |
| `anna_emp` | `pass1234` | **Employee** | Engineering |
| `james_emp` | `pass1234` | **Employee** | Finance |
| `lucy_emp` | `pass1234` | **Employee** | Marketing |
| `omar_emp` | `pass1234` | **Employee** | Operations |

---

## Common Management Commands

```bash
# ── Server ────────────────────────────────────────────────────────
python manage.py runserver                     # Start dev server
python manage.py runserver 0.0.0.0:8000        # Expose to local network

# ── Database ──────────────────────────────────────────────────────
python manage.py migrate                       # Apply all migrations
python manage.py makemigrations <app>          # Create migration for an app
python manage.py showmigrations                # Show migration status

# ── Seed Data ─────────────────────────────────────────────────────
python manage.py seed_data                     # Seed demo data (idempotent)
python manage.py seed_data --flush             # Wipe + reseed from scratch

# ── Users ─────────────────────────────────────────────────────────
python manage.py createsuperuser               # Create superuser manually

# ── Static Files ──────────────────────────────────────────────────
python manage.py collectstatic --noinput       # Collect to staticfiles/

# ── Debugging ─────────────────────────────────────────────────────
python manage.py check                         # Check for configuration errors
python manage.py shell                         # Open Django interactive shell
python manage.py show_urls                     # List all URLs (django-extensions)

# ── Celery ────────────────────────────────────────────────────────
celery -A oms_project worker --loglevel=info   # Start task worker
celery -A oms_project beat   --loglevel=info   # Start beat scheduler
celery -A oms_project flower --port=5555       # Monitoring UI → localhost:5555
```

---

## Jinja2 Environment Reference

Defined in `oms_project/jinja2.py` — available in **every template** without importing.

### Global Functions

| Function | Description | Example |
|---|---|---|
| `url('name', pk=1)` | Reverse a Django URL | `{{ url('employees:detail', pk=emp.pk) }}` |
| `static('path')` | Get static file URL | `{{ static('css/main.css') }}` |
| `get_messages(request)` | Get flash messages | Used in `base.html` |
| `csrf_input()` | Render hidden CSRF input | `{{ csrf_input() }}` inside every `<form>` |
| `csrf_token()` | Get raw CSRF token string | `{{ csrf_token() }}` |

### Custom Filters

| Filter | Description | Example |
|---|---|---|
| `\|currency` | Format as currency | `{{ 70000\|currency }}` → `$70,000.00` |
| `\|date_fmt` | Format a date | `{{ hire_date\|date_fmt }}` → `01 Mar 2026` |
| `\|status_badge` | Render a Bootstrap badge | `{{ task.status\|status_badge\|safe }}` |

### Status Badge Colour Map

| Status Values | Colour |
|---|---|
| `Present`, `Active`, `Approved`, `Paid`, `Done`, `Available` | 🟢 Green |
| `Late`, `Pending`, `On Hold`, `Generated`, `Review`, `High` | 🟡 Yellow |
| `Absent`, `Rejected`, `Cancelled`, `Critical` | 🔴 Red |
| `Planning`, `In Progress`, `Assigned` | 🔵 Blue |
| `Draft`, `To-Do`, `Disposed` | ⚫ Grey |
| `Half-Day`, `Completed` | 🩵 Cyan |

---

## .gitignore Recommendations

```gitignore
# Environment
.env
.env.*

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/

# Virtual environment
venv/
env/

# Django generated
staticfiles/
media/
logs/
*.log

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

---

*Built with ❤️ using Django · PostgreSQL · Bootstrap 5 · Celery · Redis*
*© 2026 Office Management System*
