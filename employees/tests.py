from django.test import TestCase
from django.urls import reverse
from accounts.tests import make_user, make_dept
from employees.models import Employee, Designation


def make_employee(username='emp1', role_name='Employee'):
    dept = make_dept()
    user = make_user(username, role_name=role_name)
    desig, _ = Designation.objects.get_or_create(title='Developer', department=dept, defaults={'level': 1})
    emp = Employee.objects.create(
        user=user, department=dept, designation=desig,
        salary=50000, nic='12345-6789012-3',
        emergency_contact_name='Jane Doe', emergency_contact_phone='0300-1234567'
    )
    return emp


# ─── Model Tests ─────────────────────────────────────────────────────────────

class EmployeeModelTest(TestCase):
    def test_employee_str(self):
        emp = make_employee('emp_str')
        self.assertEqual(str(emp), emp.full_name)

    def test_full_name_property(self):
        emp = make_employee('emp_fn')
        emp.user.first_name = 'Alice'
        emp.user.last_name = 'Smith'
        emp.user.save()
        self.assertEqual(emp.full_name, 'Alice Smith')

    def test_full_name_fallback_to_username(self):
        dept = make_dept()
        user = make_user('noname_emp')
        user.first_name = ''
        user.last_name = ''
        user.save()
        emp = Employee.objects.create(user=user, department=dept, salary=0)
        self.assertEqual(emp.full_name, 'noname_emp')

    def test_designation_str(self):
        dept = make_dept()
        desig = Designation.objects.create(title='Manager', department=dept, level=2)
        self.assertIn('Manager', str(desig))


# ─── View Tests ───────────────────────────────────────────────────────────────

class EmployeeListViewTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin_emp', role_name='Admin')
        self.client.force_login(self.admin)
        self.url = reverse('employees:list')

    def test_list_requires_login(self):
        self.client.logout()
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)

    def test_list_loads_for_admin(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_list_search_by_name(self):
        make_employee('searchable_emp')
        r = self.client.get(self.url + '?q=Test')
        self.assertEqual(r.status_code, 200)

    def test_list_filter_by_department(self):
        dept = make_dept()
        r = self.client.get(self.url + f'?dept={dept.pk}')
        self.assertEqual(r.status_code, 200)


class EmployeeAddViewTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin_add', role_name='Admin')
        self.client.force_login(self.admin)
        self.dept = make_dept()
        self.url = reverse('employees:add')

    def test_add_page_loads(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_add_creates_employee(self):
        before = Employee.objects.count()
        self.client.post(self.url, {
            'first_name': 'New', 'last_name': 'Hire',
            'email': 'newhire@test.com',
            'department': self.dept.pk, 'salary': 40000,
        })
        self.assertEqual(Employee.objects.count(), before + 1)

    def test_add_invalid_data_rerenders_form(self):
        r = self.client.post(self.url, {})
        self.assertEqual(r.status_code, 200)


class EmployeeDetailViewTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin_det', role_name='Admin')
        self.client.force_login(self.admin)
        self.emp = make_employee('detail_emp')

    def test_detail_loads(self):
        r = self.client.get(reverse('employees:detail', kwargs={'pk': self.emp.pk}))
        self.assertEqual(r.status_code, 200)

    def test_detail_404_for_invalid_pk(self):
        r = self.client.get(reverse('employees:detail', kwargs={'pk': 99999}))
        self.assertEqual(r.status_code, 404)


class EmployeeEditViewTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin_edit', role_name='Admin')
        self.client.force_login(self.admin)
        self.emp = make_employee('edit_emp')
        self.url = reverse('employees:edit', kwargs={'pk': self.emp.pk})

    def test_edit_page_loads(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_edit_updates_salary(self):
        dept = make_dept()
        self.client.post(self.url, {
            'first_name': 'Edit', 'last_name': 'Emp',
            'email': 'edit_emp@test.com',
            'department': dept.pk, 'salary': 99000,
        })
        self.emp.refresh_from_db()
        self.assertEqual(int(self.emp.salary), 99000)


class EmployeeDeactivateViewTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin_deact', role_name='Admin')
        self.client.force_login(self.admin)
        self.emp = make_employee('deact_emp')

    def test_deactivate_sets_is_active_false(self):
        self.client.post(reverse('employees:deactivate', kwargs={'pk': self.emp.pk}))
        self.emp.user.refresh_from_db()
        self.assertFalse(self.emp.user.is_active)


class EmployeeCSVExportTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin_csv', role_name='Admin')
        self.client.force_login(self.admin)

    def test_csv_export_returns_csv_content_type(self):
        r = self.client.get(reverse('employees:export_csv'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'text/csv')

    def test_csv_has_header_row(self):
        r = self.client.get(reverse('employees:export_csv'))
        content = r.content.decode()
        self.assertIn('Name', content)
        self.assertIn('Email', content)


class DepartmentViewTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin_dept', role_name='Admin')
        self.client.force_login(self.admin)
        self.url = reverse('employees:departments')

    def test_departments_page_loads(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_add_department_via_post(self):
        from accounts.models import Department
        before = Department.objects.count()
        self.client.post(self.url, {'name': 'NewDept_Unique'})
        self.assertEqual(Department.objects.count(), before + 1)
