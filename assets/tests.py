from django.test import TestCase
from django.urls import reverse
from accounts.tests import make_user
from employees.tests import make_employee
from assets.models import Asset, AssetCategory, AssetHistory


def make_category(name='Laptop'):
    cat, _ = AssetCategory.objects.get_or_create(name=name)
    return cat


def make_asset(name='ThinkPad X1', serial='SN-001', status='Available'):
    cat = make_category()
    return Asset.objects.create(
        name=name, category=cat,
        serial_number=serial, status=status,
        condition='Good', value=150000
    )


# ─── Model Tests ─────────────────────────────────────────────────────────────

class AssetModelTest(TestCase):
    def test_asset_str(self):
        a = make_asset()
        self.assertIn('ThinkPad X1', str(a))

    def test_asset_category_str(self):
        cat = make_category('Monitor')
        self.assertEqual(str(cat), 'Monitor')

    def test_asset_history_str(self):
        emp = make_employee('hist_emp')
        a = make_asset(serial='SN-HIST')
        h = AssetHistory.objects.create(asset=a, employee=emp)
        self.assertIn('ThinkPad X1', str(h))


# ─── View Tests ───────────────────────────────────────────────────────────────

class AssetListViewTest(TestCase):
    def setUp(self):
        self.admin = make_user('asset_admin', role_name='Admin')
        self.client.force_login(self.admin)

    def test_list_loads(self):
        r = self.client.get(reverse('assets:list'))
        self.assertEqual(r.status_code, 200)

    def test_list_requires_login(self):
        self.client.logout()
        r = self.client.get(reverse('assets:list'))
        self.assertEqual(r.status_code, 302)


class AssetAddViewTest(TestCase):
    def setUp(self):
        self.admin = make_user('asset_add_admin', role_name='Admin')
        self.client.force_login(self.admin)
        self.cat = make_category()

    def test_add_page_loads(self):
        r = self.client.get(reverse('assets:add'))
        self.assertEqual(r.status_code, 200)

    def test_add_creates_asset(self):
        before = Asset.objects.count()
        self.client.post(reverse('assets:add'), {
            'name': 'Dell Monitor',
            'category': self.cat.pk,
            'serial_number': 'SN-DELL-001',
            'status': 'Available',
            'condition': 'New',
            'value': 50000,
        })
        self.assertEqual(Asset.objects.count(), before + 1)


class AssetDetailViewTest(TestCase):
    def setUp(self):
        self.admin = make_user('asset_det_admin', role_name='Admin')
        self.client.force_login(self.admin)
        self.asset = make_asset(serial='SN-DET')

    def test_detail_loads(self):
        r = self.client.get(reverse('assets:detail', kwargs={'pk': self.asset.pk}))
        self.assertEqual(r.status_code, 200)

    def test_detail_404_invalid_pk(self):
        r = self.client.get(reverse('assets:detail', kwargs={'pk': 99999}))
        self.assertEqual(r.status_code, 404)


class AssetAssignReturnTest(TestCase):
    def setUp(self):
        self.admin = make_user('asset_assign_admin', role_name='Admin')
        self.client.force_login(self.admin)
        self.emp = make_employee('assign_emp')
        self.asset = make_asset(serial='SN-ASSIGN')

    def test_assign_asset_to_employee(self):
        self.client.post(
            reverse('assets:assign', kwargs={'pk': self.asset.pk}),
            {'employee_id': self.emp.pk}
        )
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, 'Assigned')
        self.assertEqual(self.asset.assigned_to, self.emp)

    def test_assign_creates_history_record(self):
        self.client.post(
            reverse('assets:assign', kwargs={'pk': self.asset.pk}),
            {'employee_id': self.emp.pk}
        )
        self.assertTrue(AssetHistory.objects.filter(asset=self.asset, employee=self.emp).exists())

    def test_return_asset_sets_available(self):
        self.asset.assigned_to = self.emp
        self.asset.status = 'Assigned'
        self.asset.save()
        AssetHistory.objects.create(asset=self.asset, employee=self.emp)
        self.client.post(reverse('assets:return', kwargs={'pk': self.asset.pk}))
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, 'Available')
        self.assertIsNone(self.asset.assigned_to)

    def test_return_sets_returned_at_on_history(self):
        self.asset.assigned_to = self.emp
        self.asset.status = 'Assigned'
        self.asset.save()
        history = AssetHistory.objects.create(asset=self.asset, employee=self.emp)
        self.client.post(reverse('assets:return', kwargs={'pk': self.asset.pk}))
        history.refresh_from_db()
        self.assertIsNotNone(history.returned_at)
