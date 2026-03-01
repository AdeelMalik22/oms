from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
import csv
from accounts.models import Department
from .models import Employee, Designation
from .forms import EmployeeForm, DesignationForm, DepartmentForm
from audit.services import log_action


@login_required
def employee_list(request):
    qs = Employee.objects.select_related('user', 'department', 'designation').filter(user__is_active=True)
    q = request.GET.get('q', '')
    dept = request.GET.get('dept', '')
    if q:
        qs = qs.filter(Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) | Q(user__email__icontains=q))
    if dept:
        qs = qs.filter(department_id=dept)
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))
    departments = Department.objects.all()
    return render(request, 'employees/list.html', {'page_obj': page, 'departments': departments, 'q': q, 'dept': dept})


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, 'employees/detail.html', {'employee': employee})


@login_required
def employee_add(request):
    form = EmployeeForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        employee = form.save()
        log_action(request.user, 'Created', 'Employee', str(employee.pk), request)
        messages.success(request, f'Employee {employee.full_name} added.')
        return redirect('employees:detail', pk=employee.pk)
    return render(request, 'employees/form.html', {'form': form, 'title': 'Add Employee'})


@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    form = EmployeeForm(request.POST or None, request.FILES or None, instance=employee)
    if form.is_valid():
        form.save()
        log_action(request.user, 'Updated', 'Employee', str(pk), request)
        messages.success(request, 'Employee updated.')
        return redirect('employees:detail', pk=pk)
    return render(request, 'employees/form.html', {'form': form, 'title': 'Edit Employee'})


@login_required
def employee_deactivate(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    employee.user.is_active = False
    employee.user.save()
    log_action(request.user, 'Deactivated', 'Employee', str(pk), request)
    messages.success(request, f'{employee.full_name} deactivated.')
    return redirect('employees:list')


@login_required
def employee_export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="employees.csv"'
    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Department', 'Designation', 'Hire Date', 'Salary'])
    for e in Employee.objects.select_related('user', 'department', 'designation').filter(user__is_active=True):
        writer.writerow([e.full_name, e.user.email, e.department, e.designation, e.hire_date, e.salary])
    return response


@login_required
def department_list(request):
    departments = Department.objects.prefetch_related('designations').all()
    form = DepartmentForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Department added.')
        return redirect('employees:departments')
    return render(request, 'employees/departments.html', {'departments': departments, 'form': form})
