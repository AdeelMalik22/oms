from django.test import TestCase
from django.urls import reverse
from accounts.tests import make_user
from employees.tests import make_employee
from payroll.models import Payroll, Allowance, Deduction, PayrollTemplate
from payroll.services import generate_payslip_pdf
import io


def make_payroll(emp, month=3, year=2026, basic=60000, allowances=5000, deductions=2000, status='Generated'):
    p = Payroll.objects.create(
        employee=emp, month=month, year=year,
        basic_salary=basic, total_allowances=allowances,
        total_deductions=deductions,
        net_salary=basic + allowances - deductions,
        status=status
    )
    Allowance.objects.create(payroll=p, name='Housing', amount=allowances)
    Deduction.objects.create(payroll=p, name='Tax', amount=deductions)
    return p


# ─── Model Tests ─────────────────────────────────────────────────────────────

class PayrollModelTest(TestCase):
    def test_payroll_str(self):
        emp = make_employee('pay_str_emp')
        p = make_payroll(emp)
        self.assertIn('3/2026', str(p))

    def test_calculate_net_salary(self):
        emp = make_employee('pay_net_emp')
        p = Payroll.objects.create(
            employee=emp, month=4, year=2026,
            basic_salary=50000, total_allowances=10000,
            total_deductions=3000, net_salary=0, status='Draft'
        )
        p.calculate_net()
        self.assertEqual(p.net_salary, 57000)

    def test_unique_payroll_per_employee_month_year(self):
        emp = make_employee('pay_uniq_emp')
        Payroll.objects.create(
            employee=emp, month=1, year=2026,
            basic_salary=40000, total_allowances=0,
            total_deductions=0, net_salary=40000, status='Draft'
        )
        with self.assertRaises(Exception):
            Payroll.objects.create(
                employee=emp, month=1, year=2026,
                basic_salary=40000, total_allowances=0,
                total_deductions=0, net_salary=40000, status='Draft'
            )

    def test_allowance_str(self):
        emp = make_employee('pay_allow_emp')
        p = make_payroll(emp, month=5)
        a = Allowance.objects.get(payroll=p, name='Housing')
        self.assertIn('Housing', str(a))

    def test_deduction_str(self):
        emp = make_employee('pay_ded_emp')
        p = make_payroll(emp, month=6)
        d = Deduction.objects.get(payroll=p, name='Tax')
        self.assertIn('Tax', str(d))

    def test_payroll_template_str(self):
        emp = make_employee('pay_tmpl_emp')
        tmpl = PayrollTemplate.objects.create(
            employee=emp,
            default_allowances=[{'name': 'HRA', 'amount': 5000}],
            default_deductions=[]
        )
        self.assertIn(emp.full_name, str(tmpl))


# ─── PDF Service Test ─────────────────────────────────────────────────────────

class PayslipPDFTest(TestCase):
    def test_pdf_generation_produces_output(self):
        emp = make_employee('pdf_emp')
        p = make_payroll(emp, month=7)
        buf = io.BytesIO()
        generate_payslip_pdf(p, buf)
        buf.seek(0)
        content = buf.read()
        self.assertTrue(len(content) > 100)
        self.assertTrue(content.startswith(b'%PDF'))


# ─── View Tests ───────────────────────────────────────────────────────────────

class PayrollListViewTest(TestCase):
    def setUp(self):
        self.hr = make_user('hr_payroll', role_name='HR')
        self.client.force_login(self.hr)

    def test_payroll_list_loads(self):
        r = self.client.get(reverse('payroll:list'))
        self.assertEqual(r.status_code, 200)

    def test_payroll_list_requires_login(self):
        self.client.logout()
        r = self.client.get(reverse('payroll:list'))
        self.assertEqual(r.status_code, 302)


class GeneratePayrollViewTest(TestCase):
    def setUp(self):
        self.hr = make_user('hr_gen', role_name='HR')
        self.client.force_login(self.hr)
        self.emp = make_employee('gen_emp')

    def test_generate_page_loads(self):
        r = self.client.get(reverse('payroll:generate'))
        self.assertEqual(r.status_code, 200)

    def test_generate_creates_payroll_record(self):
        before = Payroll.objects.count()
        self.client.post(reverse('payroll:generate'), {
            'employee': self.emp.pk,
            'month': 8, 'year': 2026,
            'basic_salary': 55000,
            'total_allowances': 5000,
            'total_deductions': 2000,
            'status': 'Generated',
        })
        self.assertEqual(Payroll.objects.count(), before + 1)


class PayslipDetailViewTest(TestCase):
    def setUp(self):
        self.hr = make_user('hr_slip', role_name='HR')
        self.client.force_login(self.hr)
        self.emp = make_employee('slip_emp')
        self.payroll = make_payroll(self.emp, month=9)

    def test_payslip_detail_loads(self):
        r = self.client.get(reverse('payroll:payslip', kwargs={'pk': self.payroll.pk}))
        self.assertEqual(r.status_code, 200)

    def test_payslip_pdf_download(self):
        r = self.client.get(reverse('payroll:payslip_pdf', kwargs={'pk': self.payroll.pk}))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')

    def test_payslip_404_for_invalid_pk(self):
        r = self.client.get(reverse('payroll:payslip', kwargs={'pk': 99999}))
        self.assertEqual(r.status_code, 404)


class MarkPaidViewTest(TestCase):
    def setUp(self):
        self.hr = make_user('hr_paid', role_name='HR')
        self.client.force_login(self.hr)
        self.emp = make_employee('paid_emp')
        self.payroll = make_payroll(self.emp, month=10, status='Generated')

    def test_mark_paid_updates_status(self):
        self.client.post(reverse('payroll:mark_paid', kwargs={'pk': self.payroll.pk}))
        self.payroll.refresh_from_db()
        self.assertEqual(self.payroll.status, 'Paid')


class MyPayslipsViewTest(TestCase):
    def setUp(self):
        self.emp = make_employee('my_slip_emp', role_name='Employee')
        self.client.force_login(self.emp.user)

    def test_my_payslips_loads(self):
        r = self.client.get(reverse('payroll:my_payslips'))
        self.assertEqual(r.status_code, 200)

    def test_my_payslips_only_shows_own(self):
        make_payroll(self.emp, month=11)
        other_emp = make_employee('other_slip_emp2')
        make_payroll(other_emp, month=11)
        r = self.client.get(reverse('payroll:my_payslips'))
        self.assertEqual(r.status_code, 200)
