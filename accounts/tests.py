from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser, Role, Department


def make_role(name):
    role, _ = Role.objects.get_or_create(name=name)
    return role


def make_dept(name='Engineering'):
    dept, _ = Department.objects.get_or_create(name=name)
    return dept


def make_user(username, role_name='Admin', password='testpass123', **kwargs):
    role = make_role(role_name)
    dept = make_dept()
    user = CustomUser.objects.create_user(
        username=username, password=password,
        email=f'{username}@test.com',
        first_name='Test', last_name='User',
        role=role, department=dept, **kwargs
    )
    return user


# ─── Model Tests ─────────────────────────────────────────────────────────────

class RoleModelTest(TestCase):
    def test_all_roles_created(self):
        for name in ['Admin', 'HR', 'Manager', 'Employee']:
            role = Role.objects.create(name=f'{name}_unique')
            self.assertIn(name, str(role))

    def test_role_name_unique(self):
        Role.objects.create(name='AdminUniq')
        with self.assertRaises(Exception):
            Role.objects.create(name='AdminUniq')


class DepartmentModelTest(TestCase):
    def test_department_str(self):
        dept = make_dept('Finance')
        self.assertEqual(str(dept), 'Finance')

    def test_department_unique(self):
        make_dept('HRDept')
        with self.assertRaises(Exception):
            Department.objects.create(name='HRDept')


class CustomUserModelTest(TestCase):
    def test_user_str_returns_full_name(self):
        user = make_user('john_doe')
        user.first_name = 'John'
        user.last_name = 'Doe'
        user.save()
        self.assertEqual(str(user), 'John Doe')

    def test_user_str_fallback_to_username(self):
        user = CustomUser.objects.create_user(username='jane', password='pass')
        self.assertEqual(str(user), 'jane')

    def test_is_admin_property(self):
        user = make_user('admin_user', role_name='Admin')
        self.assertTrue(user.is_admin)
        self.assertFalse(user.is_hr)

    def test_is_hr_property(self):
        user = make_user('hr_user', role_name='HR')
        self.assertTrue(user.is_hr)
        self.assertFalse(user.is_admin)

    def test_is_manager_property(self):
        user = make_user('mgr_user', role_name='Manager')
        self.assertTrue(user.is_manager)

    def test_is_employee_property(self):
        user = make_user('emp_user', role_name='Employee')
        self.assertTrue(user.is_employee)

    def test_role_none_returns_false(self):
        user = CustomUser.objects.create_user(username='norole', password='pass')
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_hr)


# ─── View Tests ───────────────────────────────────────────────────────────────

class LoginViewTest(TestCase):
    def setUp(self):
        self.user = make_user('loginuser')
        self.url = reverse('accounts:login')

    def test_login_page_loads(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_login_with_valid_credentials_redirects(self):
        r = self.client.post(self.url, {'username': 'loginuser', 'password': 'testpass123'})
        self.assertRedirects(r, reverse('dashboard:index'), fetch_redirect_response=False)

    def test_login_with_wrong_password_shows_error(self):
        r = self.client.post(self.url, {'username': 'loginuser', 'password': 'wrongpass'})
        self.assertEqual(r.status_code, 200)

    def test_login_with_empty_fields_shows_form(self):
        r = self.client.post(self.url, {})
        self.assertEqual(r.status_code, 200)

    def test_already_logged_in_redirects_to_dashboard(self):
        self.client.force_login(self.user)
        r = self.client.get(self.url)
        self.assertRedirects(r, reverse('dashboard:index'), fetch_redirect_response=False)


class LogoutViewTest(TestCase):
    def setUp(self):
        self.user = make_user('logoutuser')
        self.client.force_login(self.user)

    def test_logout_redirects_to_login(self):
        r = self.client.get(reverse('accounts:logout'))
        self.assertRedirects(r, reverse('accounts:login'), fetch_redirect_response=False)

    def test_logout_clears_session(self):
        self.client.get(reverse('accounts:logout'))
        r = self.client.get(reverse('dashboard:index'))
        self.assertRedirects(r, f"{reverse('accounts:login')}?next={reverse('dashboard:index')}",
                             fetch_redirect_response=False)


class ProfileSettingsViewTest(TestCase):
    def setUp(self):
        self.user = make_user('settingsuser')
        self.client.force_login(self.user)
        self.url = reverse('accounts:settings')

    def test_settings_page_requires_login(self):
        self.client.logout()
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)

    def test_settings_page_loads_for_authenticated_user(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_update_profile_saves_name(self):
        self.client.post(self.url, {
            'update_profile': '1',
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'settingsuser@test.com',
            'phone': '1234567890',
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
