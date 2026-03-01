import datetime
from django.test import TestCase
from django.urls import reverse
from accounts.tests import make_user
from employees.tests import make_employee
from attendance.models import Attendance
from projects.models import Project
from announcements.models import Announcement
from attendance.tests import make_leave_type
from attendance.models import LeaveRequest


class DashboardViewTest(TestCase):

    def test_dashboard_requires_login(self):
        r = self.client.get(reverse('dashboard:index'))
        self.assertEqual(r.status_code, 302)

    def test_dashboard_loads_for_admin(self):
        admin = make_user('dash_admin', role_name='Admin')
        self.client.force_login(admin)
        r = self.client.get(reverse('dashboard:index'))
        self.assertEqual(r.status_code, 200)

    def test_dashboard_shows_employee_count_for_admin(self):
        admin = make_user('dash_admin2', role_name='Admin')
        self.client.force_login(admin)
        make_employee('dash_emp1')
        make_employee('dash_emp2')
        r = self.client.get(reverse('dashboard:index'))
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Total Employees', r.content)

    def test_dashboard_shows_present_today_for_admin(self):
        admin = make_user('dash_admin3', role_name='Admin')
        self.client.force_login(admin)
        emp = make_employee('dash_present_emp')
        Attendance.objects.create(employee=emp, date=datetime.date.today(), status='Present')
        r = self.client.get(reverse('dashboard:index'))
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Present Today', r.content)

    def test_dashboard_shows_pending_leaves_for_admin(self):
        admin = make_user('dash_admin4', role_name='Admin')
        self.client.force_login(admin)
        emp = make_employee('dash_leave_emp')
        lt = make_leave_type()
        LeaveRequest.objects.create(
            employee=emp, leave_type=lt,
            start_date=datetime.date(2026, 4, 1),
            end_date=datetime.date(2026, 4, 2),
            reason='Test', status='Pending'
        )
        r = self.client.get(reverse('dashboard:index'))
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Pending Leaves', r.content)

    def test_dashboard_shows_active_projects_for_admin(self):
        admin = make_user('dash_admin5', role_name='Admin')
        self.client.force_login(admin)
        Project.objects.create(name='Active Proj', status='Active', budget=0)
        r = self.client.get(reverse('dashboard:index'))
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Active Projects', r.content)

    def test_dashboard_loads_for_employee(self):
        emp = make_employee('dash_emp_role', role_name='Employee')
        self.client.force_login(emp.user)
        r = self.client.get(reverse('dashboard:index'))
        self.assertEqual(r.status_code, 200)

    def test_dashboard_employee_sees_checkin_status(self):
        emp = make_employee('dash_checkin_emp', role_name='Employee')
        self.client.force_login(emp.user)
        Attendance.objects.create(employee=emp, date=datetime.date.today(), status='Present')
        r = self.client.get(reverse('dashboard:index'))
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Present', r.content)

    def test_dashboard_loads_for_manager(self):
        mgr = make_user('dash_mgr', role_name='Manager')
        self.client.force_login(mgr)
        r = self.client.get(reverse('dashboard:index'))
        self.assertEqual(r.status_code, 200)

    def test_dashboard_shows_pinned_announcements(self):
        admin = make_user('dash_ann_admin', role_name='Admin')
        Announcement.objects.create(
            title='Pinned Ann', content='Content',
            created_by=admin, is_active=True, is_pinned=True
        )
        self.client.force_login(admin)
        r = self.client.get(reverse('dashboard:index'))
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Pinned Ann', r.content)
