from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from .models import Payroll, Allowance, Deduction, PayrollTemplate
from .forms import PayrollForm, AllowanceFormSet, DeductionFormSet
from employees.models import Employee
from audit.services import log_action
from .services import generate_payslip_pdf


@login_required
def payroll_list(request):
    qs = Payroll.objects.select_related('employee__user').order_by('-year', '-month')
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'payroll/list.html', {'page_obj': page})


@login_required
def generate_payroll(request):
    form = PayrollForm(request.POST or None)
    if form.is_valid():
        payroll = form.save(commit=False)
        payroll.generated_by = request.user
        payroll.net_salary = payroll.basic_salary + payroll.total_allowances - payroll.total_deductions
        payroll.save()
        log_action(request.user, 'Generated Payroll', 'Payroll', str(payroll.pk), request)
        messages.success(request, 'Payroll generated.')
        return redirect('payroll:list')
    return render(request, 'payroll/generate.html', {'form': form})


@login_required
def payslip_detail(request, pk):
    payroll = get_object_or_404(Payroll, pk=pk)
    return render(request, 'payroll/payslip.html', {'payroll': payroll})


@login_required
def payslip_pdf(request, pk):
    payroll = get_object_or_404(Payroll, pk=pk)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="payslip_{pk}.pdf"'
    generate_payslip_pdf(payroll, response)
    return response


@login_required
def my_payslips(request):
    employee = get_object_or_404(Employee, user=request.user)
    payrolls = Payroll.objects.filter(employee=employee).order_by('-year', '-month')
    return render(request, 'payroll/my_payslips.html', {'payrolls': payrolls})


@login_required
def mark_paid(request, pk):
    payroll = get_object_or_404(Payroll, pk=pk)
    payroll.status = 'Paid'
    payroll.save()
    log_action(request.user, 'Marked Paid', 'Payroll', str(pk), request)
    messages.success(request, 'Marked as Paid.')
    return redirect('payroll:list')
