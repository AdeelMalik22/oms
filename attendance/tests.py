import datetime
from django.test import TestCase
from django.urls import reverse
from accounts.tests import make_user, make_dept
from employees.tests import make_employee
from attendance.models import Attendance, LeaveRequest, LeaveType, LeaveBalance


def make_leave_type(name='Annual Leave', days=21):
    lt, _ = LeaveType.objects.get_or_create(name=name, defaults={'max_days_per_year': days, 'is_paid': True})
    return lt


# ─── Model Tests ─────────────────────────────────────────────────────────────

class AttendanceModelTest(TestCase):
    def test_attendance_str(self):
        emp = make_employee('att_str_emp')
        att = Attendance.objects.create(employee=emp, date=datetime.date.today(), status='Present')
        self.assertIn('Present', str(att))

    def test_unique_attendance_per_employee_per_day(self):
        emp = make_employee('att_uniq_emp')
        today = datetime.date.today()
        Attendance.objects.create(employee=emp, date=today, status='Present')
        with self.assertRaises(Exception):
            Attendance.objects.create(employee=emp, date=today, status='Absent')

    def test_leave_type_str(self):
        lt = make_leave_type('Sick Leave')
        self.assertEqual(str(lt), 'Sick Leave')

    def test_leave_request_duration_days(self):
        emp = make_employee('leave_dur_emp')
        lt = make_leave_type()
        leave = LeaveRequest.objects.create(
            employee=emp, leave_type=lt,
            start_date=datetime.date(2026, 3, 1),
            end_date=datetime.date(2026, 3, 5),
            reason='Vacation'
        )
        self.assertEqual(leave.duration_days, 5)

    def test_leave_balance_remaining_days(self):
        emp = make_employee('bal_emp')
        lt = make_leave_type()
        bal = LeaveBalance.objects.create(employee=emp, leave_type=lt, year=2026, total_days=21, used_days=5)
        self.assertEqual(bal.remaining_days, 16)

    def test_leave_balance_unique_per_employee_type_year(self):
        emp = make_employee('bal_uniq_emp')
        lt = make_leave_type()
        LeaveBalance.objects.create(employee=emp, leave_type=lt, year=2026, total_days=21, used_days=0)
        with self.assertRaises(Exception):
            LeaveBalance.objects.create(employee=emp, leave_type=lt, year=2026, total_days=21, used_days=0)


# ─── View Tests ───────────────────────────────────────────────────────────────

class AttendanceListViewTest(TestCase):
    def setUp(self):
        self.admin = make_user('att_admin', role_name='Admin')
        self.client.force_login(self.admin)

    def test_attendance_list_loads(self):
        r = self.client.get(reverse('attendance:list'))
        self.assertEqual(r.status_code, 200)

    def test_attendance_list_requires_login(self):
        self.client.logout()
        r = self.client.get(reverse('attendance:list'))
        self.assertEqual(r.status_code, 302)


class CheckInCheckOutTest(TestCase):
    def setUp(self):
        self.emp = make_employee('checkin_emp', role_name='Employee')
        self.client.force_login(self.emp.user)

    def test_checkin_creates_attendance_record(self):
        before = Attendance.objects.count()
        self.client.get(reverse('attendance:checkin'))
        self.assertEqual(Attendance.objects.count(), before + 1)

    def test_checkin_sets_check_in_time(self):
        self.client.get(reverse('attendance:checkin'))
        record = Attendance.objects.get(employee=self.emp, date=datetime.date.today())
        self.assertIsNotNone(record.check_in)

    def test_double_checkin_does_not_create_duplicate(self):
        self.client.get(reverse('attendance:checkin'))
        self.client.get(reverse('attendance:checkin'))
        count = Attendance.objects.filter(employee=self.emp, date=datetime.date.today()).count()
        self.assertEqual(count, 1)

    def test_checkout_sets_check_out_time(self):
        Attendance.objects.create(employee=self.emp, date=datetime.date.today(), status='Present')
        self.client.get(reverse('attendance:checkout'))
        record = Attendance.objects.get(employee=self.emp, date=datetime.date.today())
        self.assertIsNotNone(record.check_out)


class MyAttendanceViewTest(TestCase):
    def setUp(self):
        self.emp = make_employee('my_att_emp', role_name='Employee')
        self.client.force_login(self.emp.user)

    def test_my_attendance_loads(self):
        r = self.client.get(reverse('attendance:my'))
        self.assertEqual(r.status_code, 200)


class LeaveRequestFlowTest(TestCase):
    def setUp(self):
        self.hr = make_user('hr_leave', role_name='HR')
        self.emp = make_employee('leave_emp', role_name='Employee')
        self.lt = make_leave_type()
        self.client.force_login(self.emp.user)

    def test_apply_leave_page_loads(self):
        r = self.client.get(reverse('attendance:apply_leave'))
        self.assertEqual(r.status_code, 200)

    def test_apply_leave_creates_request(self):
        before = LeaveRequest.objects.count()
        self.client.post(reverse('attendance:apply_leave'), {
            'leave_type': self.lt.pk,
            'start_date': '2026-04-01',
            'end_date': '2026-04-03',
            'reason': 'Personal work',
        })
        self.assertEqual(LeaveRequest.objects.count(), before + 1)

    def test_apply_leave_defaults_to_pending(self):
        self.client.post(reverse('attendance:apply_leave'), {
            'leave_type': self.lt.pk,
            'start_date': '2026-04-05',
            'end_date': '2026-04-06',
            'reason': 'Medical',
        })
        leave = LeaveRequest.objects.latest('applied_at')
        self.assertEqual(leave.status, 'Pending')

    def test_approve_leave_changes_status(self):
        leave = LeaveRequest.objects.create(
            employee=self.emp, leave_type=self.lt,
            start_date=datetime.date(2026, 5, 1),
            end_date=datetime.date(2026, 5, 2),
            reason='Holiday'
        )
        self.client.force_login(self.hr)
        self.client.post(reverse('attendance:approve_leave', kwargs={'pk': leave.pk}))
        leave.refresh_from_db()
        self.assertEqual(leave.status, 'Approved')

    def test_approve_leave_updates_balance(self):
        leave = LeaveRequest.objects.create(
            employee=self.emp, leave_type=self.lt,
            start_date=datetime.date(2026, 5, 3),
            end_date=datetime.date(2026, 5, 5),
            reason='Rest'
        )
        self.client.force_login(self.hr)
        self.client.post(reverse('attendance:approve_leave', kwargs={'pk': leave.pk}))
        bal = LeaveBalance.objects.get(employee=self.emp, leave_type=self.lt, year=2026)
        self.assertEqual(bal.used_days, 3)

    def test_reject_leave_changes_status(self):
        leave = LeaveRequest.objects.create(
            employee=self.emp, leave_type=self.lt,
            start_date=datetime.date(2026, 6, 1),
            end_date=datetime.date(2026, 6, 1),
            reason='Trip'
        )
        self.client.force_login(self.hr)
        self.client.post(reverse('attendance:reject_leave', kwargs={'pk': leave.pk}))
        leave.refresh_from_db()
        self.assertEqual(leave.status, 'Rejected')

    def test_leaves_list_loads(self):
        self.client.force_login(self.hr)
        r = self.client.get(reverse('attendance:leaves'))
        self.assertEqual(r.status_code, 200)
