from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import date, timedelta, time
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with realistic demo data. Safe to run multiple times.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Wipe all existing seed data before reseeding (clean slate).',
        )

    def handle(self, *args, **options):
        from accounts.models import Role, Department
        from employees.models import Employee, Designation
        from attendance.models import LeaveType, LeaveBalance, LeaveRequest, Attendance
        from payroll.models import Payroll
        from projects.models import Project, ProjectMember, Task
        from announcements.models import Announcement
        from assets.models import Asset, AssetCategory
        from documents.models import Document, DocumentCategory
        from notifications.models import Notification

        today = date.today()

        # ── Optional flush ─────────────────────────────────────────────
        if options['flush']:
            self.stdout.write(self.style.WARNING('⚠ Flushing existing seed data...'))
            Notification.objects.all().delete()
            Document.objects.all().delete()
            Asset.objects.all().delete()
            Announcement.objects.all().delete()
            Task.objects.all().delete()
            ProjectMember.objects.all().delete()
            Project.objects.all().delete()
            Payroll.objects.all().delete()
            LeaveRequest.objects.all().delete()
            LeaveBalance.objects.all().delete()
            Attendance.objects.all().delete()
            Employee.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            User.objects.filter(username='admin').delete()
            self.stdout.write(self.style.WARNING('✔ Flush complete.\n'))

        # ── Roles ──────────────────────────────────────────────────────
        for name in ['Admin', 'HR', 'Manager', 'Employee']:
            Role.objects.get_or_create(name=name)
        role_admin    = Role.objects.get(name='Admin')
        role_hr       = Role.objects.get(name='HR')
        role_manager  = Role.objects.get(name='Manager')
        role_employee = Role.objects.get(name='Employee')
        self.stdout.write(self.style.SUCCESS('✔ Roles'))

        # ── Departments ────────────────────────────────────────────────
        for name in ['Engineering', 'Human Resources', 'Finance', 'Marketing', 'Operations']:
            Department.objects.get_or_create(name=name)
        dept_eng = Department.objects.get(name='Engineering')
        dept_hr  = Department.objects.get(name='Human Resources')
        dept_fin = Department.objects.get(name='Finance')
        dept_mkt = Department.objects.get(name='Marketing')
        dept_ops = Department.objects.get(name='Operations')
        self.stdout.write(self.style.SUCCESS('✔ Departments'))

        # ── Designations ───────────────────────────────────────────────
        desig_map = [
            ('Software Engineer',  dept_eng),
            ('Senior Developer',   dept_eng),
            ('HR Manager',         dept_hr),
            ('HR Executive',       dept_hr),
            ('Finance Manager',    dept_fin),
            ('Accountant',         dept_fin),
            ('Marketing Manager',  dept_mkt),
            ('Operations Head',    dept_ops),
        ]
        for title, dept in desig_map:
            Designation.objects.get_or_create(title=title, department=dept)
        self.stdout.write(self.style.SUCCESS('✔ Designations'))

        # ── Leave Types ────────────────────────────────────────────────
        leave_types_config = [
            ('Exams',          25,  True,  'info',    'bi-book'),
            ('Sick Leave',     5,   True,  'danger',  'bi-hospital'),
            ('Casual',         10,  True,  'warning', 'bi-calendar-x'),
            ('Short',          5,   True,  'success', 'bi-clock'),
            ('Emergency',      5,   True,  'danger',  'bi-exclamation-triangle'),
        ]
        for name, days, paid, color, icon in leave_types_config:
            LeaveType.objects.get_or_create(
                name=name,
                defaults={'max_days_per_year': days, 'is_paid': paid, 'color': color, 'icon': icon}
            )
        self.stdout.write(self.style.SUCCESS('✔ Leave Types'))

        # ── Asset & Document Categories ────────────────────────────────
        for name in ['Laptop', 'Mobile', 'Monitor', 'Furniture', 'Vehicle', 'Other']:
            AssetCategory.objects.get_or_create(name=name)
        for name in ['HR Policy', 'Contract', 'Invoice', 'Report', 'Other']:
            DocumentCategory.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS('✔ Asset & Document Categories'))

        # ── Users & Employees ──────────────────────────────────────────
        # Format: username, password, first, last, email, role, dept, designation, salary, hire_days_ago
        users_config = [
            ('admin',     'admin123', 'Admin',  'User',    'admin@oms.com',     role_admin,    dept_eng, 'Software Engineer',  0,      365*3),
            ('sarah_hr',  'pass1234', 'Sarah',  'Johnson', 'sarah@oms.com',     role_hr,       dept_hr,  'HR Manager',         85000,  365*2),
            ('mike_hr',   'pass1234', 'Mike',   'Wilson',  'mike@oms.com',      role_hr,       dept_hr,  'HR Executive',       65000,  365*1),
            ('ali_mgr',   'pass1234', 'Ali',    'Hassan',  'ali@oms.com',       role_manager,  dept_eng, 'Senior Developer',   120000, 365*4),
            ('emma_mgr',  'pass1234', 'Emma',   'Davis',   'emma@oms.com',      role_manager,  dept_mkt, 'Marketing Manager',  110000, 365*3),
            ('john_emp',  'pass1234', 'John',   'Smith',   'john@oms.com',      role_employee, dept_eng, 'Software Engineer',  70000,  365*1),
            ('anna_emp',  'pass1234', 'Anna',   'Brown',   'anna@oms.com',      role_employee, dept_eng, 'Software Engineer',  72000,  200),
            ('james_emp', 'pass1234', 'James',  'Miller',  'james@oms.com',     role_employee, dept_fin, 'Accountant',         68000,  300),
            ('lucy_emp',  'pass1234', 'Lucy',   'Taylor',  'lucy@oms.com',      role_employee, dept_mkt, 'Marketing Manager',  75000,  400),
            ('omar_emp',  'pass1234', 'Omar',   'Khan',    'omar@oms.com',      role_employee, dept_ops, 'Operations Head',    78000,  500),
        ]

        created_employees = []
        for uname, pwd, first, last, email, role, dept, desig_title, salary, hire_delta in users_config:
            user, created = User.objects.get_or_create(username=uname)
            if created or not user.has_usable_password():
                user.first_name  = first
                user.last_name   = last
                user.email       = email
                user.role        = role
                user.department  = dept
                user.is_staff    = (role == role_admin)
                user.is_superuser = (uname == 'admin')
                user.set_password(pwd)
                user.save()
            # Always ensure role/dept is set even if user pre-existed (e.g. old superuser)
            if not user.role:
                user.role = role
                user.department = dept
                user.is_staff = (role == role_admin)
                user.is_superuser = (uname == 'admin')
                user.save()

            desig = Designation.objects.filter(title=desig_title, department=dept).first()
            hire_date = today - timedelta(days=hire_delta) if hire_delta else today
            emp, _ = Employee.objects.get_or_create(
                user=user,
                defaults={
                    'department': dept,
                    'designation': desig,
                    'salary': salary,
                    'hire_date': hire_date,
                    'nic': f'3520{random.randint(1000000, 9999999)}1',
                    'address': f'{random.randint(1, 999)} Main Street, Lahore',
                    'emergency_contact_name': f'Emergency Contact of {first}',
                    'emergency_contact_phone': f'0300-{random.randint(1000000, 9999999)}',
                }
            )
            created_employees.append(emp)

        self.stdout.write(self.style.SUCCESS('✔ Users & Employees (10)'))

        # ── Leave Balances ─────────────────────────────────────────────
        leave_types = list(LeaveType.objects.all())
        for emp in created_employees:
            for lt in leave_types:
                LeaveBalance.objects.get_or_create(
                    employee=emp, leave_type=lt, year=today.year,
                    defaults={
                        'total_days': lt.max_days_per_year,
                        'used_days': random.randint(0, min(5, lt.max_days_per_year)),
                    }
                )
        self.stdout.write(self.style.SUCCESS('✔ Leave Balances'))

        # ── Attendance — last 30 weekdays ──────────────────────────────
        statuses = ['Present', 'Present', 'Present', 'Present', 'Late', 'Absent']
        for emp in created_employees:
            for i in range(30):
                day = today - timedelta(days=i)
                if day.weekday() >= 5:          # skip Saturday & Sunday
                    continue
                if Attendance.objects.filter(employee=emp, date=day).exists():
                    continue
                status = random.choice(statuses)
                check_in = check_out = None
                if status in ('Present', 'Late'):
                    h_in  = 9 if status == 'Present' else random.randint(10, 11)
                    check_in  = time(h_in,  random.randint(0, 59))
                    check_out = time(random.randint(17, 18), random.randint(0, 59))
                Attendance.objects.create(
                    employee=emp, date=day, status=status,
                    check_in=check_in, check_out=check_out,
                )
        self.stdout.write(self.style.SUCCESS('✔ Attendance (30 days × 10 employees)'))

        # ── Leave Requests ─────────────────────────────────────────────
        hr_user  = User.objects.filter(role=role_hr).first()
        statuses_leave = ['Pending', 'Approved', 'Rejected', 'Pending', 'Approved',
                          'Approved', 'Pending', 'Rejected', 'Approved', 'Pending']
        for i, emp in enumerate(created_employees):
            lt     = random.choice(leave_types)
            start  = today - timedelta(days=random.randint(5, 20))
            end    = start + timedelta(days=random.randint(1, 3))
            status = statuses_leave[i % len(statuses_leave)]
            LeaveRequest.objects.get_or_create(
                employee=emp, start_date=start, leave_type=lt,
                defaults={
                    'end_date':     end,
                    'reason':       random.choice([
                        'Family event', 'Medical appointment', 'Personal work',
                        'Annual vacation', 'Home emergency',
                    ]),
                    'status':       status,
                    'approved_by':  hr_user if status != 'Pending' else None,
                }
            )
        self.stdout.write(self.style.SUCCESS('✔ Leave Requests'))

        # ── Payroll — last 3 months ────────────────────────────────────
        for emp in created_employees:
            for months_back in range(3):
                m = today.month - months_back
                y = today.year
                if m <= 0:
                    m += 12
                    y -= 1
                basic      = float(emp.salary) if emp.salary else 50000
                allowances = round(basic * 0.20, 2)
                deductions = round(basic * 0.05, 2)
                Payroll.objects.get_or_create(
                    employee=emp, month=m, year=y,
                    defaults={
                        'basic_salary':      basic,
                        'total_allowances':  allowances,
                        'total_deductions':  deductions,
                        'net_salary':        basic + allowances - deductions,
                        'status':            'Paid' if months_back > 0 else 'Generated',
                    }
                )
        self.stdout.write(self.style.SUCCESS('✔ Payroll (3 months × 10 employees)'))

        # ── Projects ───────────────────────────────────────────────────
        mgr_emp  = Employee.objects.filter(user__role=role_manager).first()
        emp_pool = list(Employee.objects.filter(user__role=role_employee))

        projects_config = [
            ('ERP System Upgrade',    'Upgrading the core ERP modules to the latest version.',  'Active',   today-timedelta(60),  today+timedelta(90),  500000),
            ('Website Redesign',      'Full redesign of the company website and mobile app.',    'Active',   today-timedelta(30),  today+timedelta(60),  150000),
            ('HR Automation',         'Automating HR workflows, approvals and reporting.',       'Planning', today+timedelta(10),  today+timedelta(120), 200000),
            ('Marketing Campaign Q2', 'Digital marketing campaign for Q2 2026.',                'Active',   today-timedelta(15),  today+timedelta(45),  300000),
            ('Office Move',           'Relocation of head office to the new business park.',    'On Hold',  today-timedelta(90),  today+timedelta(30),  100000),
        ]
        projects = []
        for name, desc, status, start, end, budget in projects_config:
            p, _ = Project.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc, 'status': status,
                    'start_date':  start, 'end_date': end,
                    'budget':      budget, 'manager': mgr_emp,
                }
            )
            projects.append(p)

        for p in projects:
            sample_size = min(3, len(emp_pool))
            for emp in random.sample(emp_pool, sample_size):
                ProjectMember.objects.get_or_create(
                    project=p, employee=emp,
                    defaults={'role': random.choice(['Developer', 'Designer', 'Tester', 'Analyst'])},
                )
        self.stdout.write(self.style.SUCCESS('✔ Projects (5) + Members'))

        # ── Tasks — 5 per project ──────────────────────────────────────
        task_titles = [
            'Setup environment',       'Write unit tests',      'Deploy to staging',
            'Code review',             'Fix critical bug',      'Update documentation',
            'Design mockups',          'Client presentation',   'Database optimisation',
            'Security audit',          'Performance testing',   'Feature implementation',
            'API integration',         'Data migration',        'User acceptance testing',
        ]
        for p in projects:
            members = list(ProjectMember.objects.filter(project=p).select_related('employee'))
            for i in range(5):
                assigned = members[i % len(members)].employee if members else (emp_pool[0] if emp_pool else None)
                title    = random.choice(task_titles) + f' #{i+1}'
                Task.objects.get_or_create(
                    project=p, title=title,
                    defaults={
                        'assigned_to': assigned,
                        'priority':    random.choice(['Low', 'Medium', 'High', 'Critical']),
                        'status':      random.choice(['To-Do', 'In Progress', 'Review', 'Done']),
                        'due_date':    today + timedelta(days=random.randint(1, 30)),
                        'description': 'Complete this task as per project requirements.',
                    }
                )
        self.stdout.write(self.style.SUCCESS('✔ Tasks (25)'))

        # ── Announcements ──────────────────────────────────────────────
        poster = hr_user or User.objects.filter(is_superuser=True).first()
        for title, content, pinned in [
            ('Welcome to OMS!',
             'We are excited to launch the new Office Management System. Explore all features.',
             True),
            ('Q1 2026 Performance Reviews',
             'Annual performance reviews will run March 10–20. Managers please prepare.',
             True),
            ('New Leave Policy',
             'Updated leave policy effective April 1, 2026. Annual leave increased to 21 days.',
             False),
            ('Office Closure – Eid',
             'Office closed March 31 & April 1 for Eid holidays.',
             True),
            ('IT Security Reminder',
             'Please update your passwords and enable 2FA on all work accounts immediately.',
             False),
        ]:
            Announcement.objects.get_or_create(
                title=title,
                defaults={
                    'content':    content,
                    'is_pinned':  pinned,
                    'is_active':  True,
                    'created_by': poster,
                }
            )
        self.stdout.write(self.style.SUCCESS('✔ Announcements (5)'))

        # ── Assets ─────────────────────────────────────────────────────
        def acat(name):
            return AssetCategory.objects.get(name=name)

        assets_config = [
            ('MacBook Pro 14"',  'Laptop',    'MBP-2024-001',  'Assigned',     350000, emp_pool[0] if len(emp_pool) > 0 else None),
            ('Dell Monitor 27"', 'Monitor',   'DM-27-002',     'Assigned',     45000,  emp_pool[1] if len(emp_pool) > 1 else None),
            ('iPhone 15 Pro',    'Mobile',    'IP15-003',      'Assigned',     280000, emp_pool[2] if len(emp_pool) > 2 else None),
            ('HP Laptop',        'Laptop',    'HP-2023-004',   'Available',    120000, None),
            ('Office Chair',     'Furniture', 'CHAIR-005',     'Available',    25000,  None),
            ('Samsung Monitor',  'Monitor',   'SAM-24-006',    'Assigned',     38000,  emp_pool[3] if len(emp_pool) > 3 else None),
            ('iPad Air',         'Mobile',    'IPAD-007',      'Under Repair', 95000,  None),
        ]
        for name, cat_name, serial, status, value, assigned_emp in assets_config:
            Asset.objects.get_or_create(
                serial_number=serial,
                defaults={
                    'name':          name,
                    'category':      acat(cat_name),
                    'status':        status,
                    'value':         value,
                    'assigned_to':   assigned_emp,
                    'purchase_date': today - timedelta(days=random.randint(30, 730)),
                    'condition':     random.choice(['Good', 'Excellent', 'Fair']),
                }
            )
        self.stdout.write(self.style.SUCCESS('✔ Assets (7)'))

        # ── Documents (no real file needed — seed path only) ───────────
        def dcat(name):
            return DocumentCategory.objects.get(name=name)

        for title, cat_name, dept in [
            ('Employee Handbook 2026',  'HR Policy', dept_hr),
            ('Q1 Financial Report',     'Report',    dept_fin),
            ('Marketing Strategy 2026', 'Report',    dept_mkt),
            ('NDA Template',            'Contract',  dept_hr),
            ('IT Security Policy',      'HR Policy', dept_eng),
        ]:
            if not Document.objects.filter(title=title).exists():
                doc          = Document()
                doc.title    = title
                doc.category = dcat(cat_name)
                doc.department  = dept
                doc.uploaded_by = poster
                doc.version  = 1
                # Store a placeholder path — no actual file needed for demo
                doc.file.name = f'documents/seed_{title.lower().replace(" ", "_").replace("/","_")}.pdf'
                doc.save()
        self.stdout.write(self.style.SUCCESS('✔ Documents (5)'))

        # ── Notifications ──────────────────────────────────────────────
        notif_messages = [
            ('Leave Approved',          'Your annual leave request has been approved.',              'info'),
            ('Payslip Ready',           'Your March 2026 payslip is now available to download.',     'info'),
            ('Task Assigned',           'You have been assigned a new task: Deploy to staging.',     'info'),
            ('Performance Review Due',  'Your Q1 performance review is due by March 20, 2026.',      'warning'),
            ('Password Expiry',         'Your password will expire in 7 days. Please update it.',    'warning'),
        ]
        for emp in created_employees[:5]:
            for title, msg, ntype in notif_messages:
                Notification.objects.get_or_create(
                    recipient=emp.user, title=title,
                    defaults={
                        'message': msg,
                        'type':    ntype,
                        'is_read': random.choice([True, False]),
                    }
                )
        self.stdout.write(self.style.SUCCESS('✔ Notifications'))

        # ── Summary ────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS('\n🎉  Seed data ready!'))
        self.stdout.write('')
        self.stdout.write('  Username     Password    Role')
        self.stdout.write('  ─────────────────────────────────────')
        self.stdout.write('  admin        admin123    Admin / Superuser')
        self.stdout.write('  sarah_hr     pass1234    HR Manager')
        self.stdout.write('  mike_hr      pass1234    HR Executive')
        self.stdout.write('  ali_mgr      pass1234    Manager')
        self.stdout.write('  emma_mgr     pass1234    Manager')
        self.stdout.write('  john_emp     pass1234    Employee')
        self.stdout.write('  anna_emp     pass1234    Employee')
        self.stdout.write('  james_emp    pass1234    Employee')
        self.stdout.write('  lucy_emp     pass1234    Employee')
        self.stdout.write('  omar_emp     pass1234    Employee')
