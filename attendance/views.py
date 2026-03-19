from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Attendance, LeaveRequest, LeaveType, LeaveBalance, ResignationRequest
from .forms import AttendanceForm, LeaveRequestForm, ResignationRequestForm
from .tasks import send_leave_decision_email
from employees.models import Employee
from django.template.response import TemplateResponse
from django.test.signals import template_rendered


@login_required
def attendance_list(request):
    today = timezone.now().date()
    records = Attendance.objects.select_related('employee__user').filter(date=today)
    return render(request, 'attendance/list.html', {'records': records, 'today': today})


def _get_or_create_employee(user):
    """Get or auto-create an Employee profile for any logged-in user."""
    try:
        return user.employee_profile
    except Employee.DoesNotExist:
        from accounts.models import Department
        dept = user.department or Department.objects.first()
        emp = Employee.objects.create(
            user=user,
            department=dept,
            hire_date=timezone.now().date(),
        )
        return emp


@login_required
def my_attendance(request):
    employee = _get_or_create_employee(request.user)
    records = Attendance.objects.filter(employee=employee).order_by('-date')[:60]
    today_record = Attendance.objects.filter(employee=employee, date=timezone.now().date()).first()
    return render(request, 'attendance/my_attendance.html', {'records': records, 'today_record': today_record})


@login_required
def checkin(request):
    if request.method != 'POST':
        return redirect('dashboard:index')
    employee = _get_or_create_employee(request.user)
    today = timezone.now().date()
    record, created = Attendance.objects.get_or_create(employee=employee, date=today, defaults={'status': 'Present'})
    if created or not record.check_in:
        record.check_in = timezone.now().time()
        record.save()
        messages.success(request, 'Checked in successfully.')
    else:
        messages.info(request, 'Already checked in.')
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER', '')
    if next_url and '/checkin' not in next_url and '/checkout' not in next_url:
        return redirect(next_url)
    return redirect('dashboard:index')


@login_required
def checkout(request):
    if request.method != 'POST':
        return redirect('dashboard:index')
    employee = _get_or_create_employee(request.user)
    today = timezone.now().date()
    record = Attendance.objects.filter(employee=employee, date=today).first()
    if record:
        record.check_out = timezone.now().time()
        record.save()
        messages.success(request, 'Checked out successfully.')
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER', '')
    if next_url and '/checkin' not in next_url and '/checkout' not in next_url:
        return redirect(next_url)
    return redirect('dashboard:index')


@login_required
def leave_list(request):
    user = request.user
    employee = _get_or_create_employee(user)
    current_year = timezone.now().year

    my_leaves = LeaveRequest.objects.select_related(
        'leave_type', 'approved_by'
    ).filter(employee=employee).order_by('-applied_at')

    my_leave_balances = []
    for leave_type in LeaveType.objects.all().order_by('name'):
        balance, _ = LeaveBalance.objects.get_or_create(
            employee=employee,
            leave_type=leave_type,
            year=current_year,
            defaults={'total_days': leave_type.max_days_per_year},
        )
        if balance.total_days != leave_type.max_days_per_year:
            balance.total_days = leave_type.max_days_per_year
            balance.save(update_fields=['total_days'])
        my_leave_balances.append(balance)

    if user.is_manager:
        try:
            emp = user.employee_profile
            from projects.models import ProjectMember
            from django.db.models import Q
            team_emp_ids = ProjectMember.objects.filter(
                Q(project__manager=emp)
            ).values_list('employee_id', flat=True).distinct()
            leaves = LeaveRequest.objects.select_related(
                'employee__user', 'leave_type'
            ).filter(employee_id__in=team_emp_ids).order_by('-applied_at')
        except Exception:
            leaves = LeaveRequest.objects.none()
    else:
        leaves = LeaveRequest.objects.select_related(
            'employee__user', 'leave_type'
        ).order_by('-applied_at')

    # Resignation data for the tab in the leave page
    if user.is_admin or user.is_hr:
        resignations = ResignationRequest.objects.select_related(
            'employee__user', 'reviewed_by'
        ).order_by('-applied_at')
        pending_count = ResignationRequest.objects.filter(status='Pending').count()
        approved_count = ResignationRequest.objects.filter(status='Approved').count()
        rejected_count = ResignationRequest.objects.filter(status='Rejected').count()
    else:
        resignations = ResignationRequest.objects.select_related('reviewed_by').filter(
            employee=employee
        ).order_by('-applied_at')
        pending_count = resignations.filter(status='Pending').count()
        approved_count = resignations.filter(status='Approved').count()
        rejected_count = resignations.filter(status='Rejected').count()

    return render(request, 'attendance/leaves.html', {
        'leaves': leaves,
        'my_leaves': my_leaves,
        'my_leave_balances': my_leave_balances,
        'resignations': resignations,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    })


@login_required
def apply_leave(request):
    employee = get_object_or_404(Employee, user=request.user)
    form = LeaveRequestForm(request.POST or None)

    # Get current year
    from django.utils import timezone
    current_year = timezone.now().year

    # Get all leave types with their balances
    leave_types = LeaveType.objects.all()
    leave_balances = {}

    for leave_type in leave_types:
        balance, _ = LeaveBalance.objects.get_or_create(
            employee=employee,
            leave_type=leave_type,
            year=current_year,
            defaults={'total_days': leave_type.max_days_per_year}
        )
        leave_balances[leave_type.id] = {
            'leave_type': leave_type,
            'balance': balance,
            'total': balance.total_days,
            'used': balance.used_days,
            'remaining': balance.remaining_days,
        }

    if form.is_valid():
        leave = form.save(commit=False)
        leave.employee = employee

        # Check if employee has enough balance
        balance = LeaveBalance.objects.get(
            employee=employee,
            leave_type=leave.leave_type,
            year=current_year
        )
        if balance.remaining_days < leave.duration_days:
            messages.error(request, f'Insufficient balance. You have {balance.remaining_days} days remaining.')
            return render(request, 'attendance/apply_leave.html', {
                'form': form,
                'leave_balances': leave_balances,
                'employee': employee,
            })

        leave.save()
        messages.success(request, 'Leave request submitted.')
        return redirect('attendance:leaves')

    return render(request, 'attendance/apply_leave.html', {
        'form': form,
        'leave_balances': leave_balances,
        'employee': employee,
    })


@login_required
def approve_leave(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = 'Approved'
    leave.approved_by = request.user
    leave.save()
    # update leave balance
    year = leave.start_date.year
    balance, _ = LeaveBalance.objects.get_or_create(
        employee=leave.employee, leave_type=leave.leave_type, year=year,
        defaults={'total_days': leave.leave_type.max_days_per_year}
    )
    balance.used_days += leave.duration_days
    balance.save()
    send_leave_decision_email.delay(
        leave.employee.user.email, leave.employee.full_name,
        str(leave.leave_type), 'Approved',
        str(leave.start_date), str(leave.end_date)
    )
    messages.success(request, 'Leave approved.')
    return redirect('attendance:leaves')


@login_required
def reject_leave(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = 'Rejected'
    leave.approved_by = request.user
    leave.save()
    send_leave_decision_email.delay(
        leave.employee.user.email, leave.employee.full_name,
        str(leave.leave_type), 'Rejected',
        str(leave.start_date), str(leave.end_date)
    )
    messages.success(request, 'Leave rejected.')
    return redirect('attendance:leaves')


# ─── Resignation Views ────────────────────────────────────────────────────────


@login_required
def resignation_list(request):
    """List resignations: employees see their own, HR/Admin see all."""
    user = request.user
    employee = _get_or_create_employee(user)

    if user.is_admin or user.is_hr:
        # HR/Admin see all resignations
        resignations = ResignationRequest.objects.select_related(
            'employee__user', 'reviewed_by'
        ).order_by('-applied_at')
    else:
        # Employees see only their own
        resignations = ResignationRequest.objects.select_related(
            'reviewed_by'
        ).filter(employee=employee).order_by('-applied_at')

    # Summary counts for current user
    if user.is_admin or user.is_hr:
        pending_count = ResignationRequest.objects.filter(status='Pending').count()
        approved_count = ResignationRequest.objects.filter(status='Approved').count()
        rejected_count = ResignationRequest.objects.filter(status='Rejected').count()
    else:
        pending_count = resignations.filter(status='Pending').count()
        approved_count = resignations.filter(status='Approved').count()
        rejected_count = resignations.filter(status='Rejected').count()

    context = {
        'resignations': resignations,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    # Fire template_rendered signal so Django's test client captures context when using Jinja2 templates
    template_rendered.send(sender=TemplateResponse, template=None, context=context, request=request)
    return TemplateResponse(request, 'attendance/resignations.html', context)


@login_required
def apply_resignation(request):
    """Employee submits a resignation request."""
    employee = _get_or_create_employee(request.user)

    # Check if employee already has a pending resignation
    pending_resignation = ResignationRequest.objects.filter(
        employee=employee, status='Pending'
    ).first()
    if pending_resignation:
        messages.warning(request, 'You already have a pending resignation request.')
        return redirect('attendance:resignations')

    form = ResignationRequestForm(request.POST or None)

    if form.is_valid():
        resignation = form.save(commit=False)
        resignation.employee = employee
        resignation.save()
        messages.success(request, 'Resignation request submitted successfully.')
        return redirect('attendance:resignations')

    return render(request, 'attendance/apply_resignation.html', {'form': form})


@login_required
def approve_resignation(request, pk):
    """HR/Admin approves a resignation."""
    if not (request.user.is_admin or request.user.is_hr):
        messages.error(request, 'You do not have permission to approve resignations.')
        return redirect('attendance:resignations')

    resignation = get_object_or_404(ResignationRequest, pk=pk)
    resignation.status = 'Approved'
    resignation.reviewed_by = request.user
    resignation.reviewed_at = timezone.now()
    resignation.save()

    # If last working date has arrived/passed, deactivate the account immediately
    if resignation.requested_last_working_date <= timezone.now().date():
        resignation.employee.user.is_active = False
        resignation.employee.user.save(update_fields=['is_active'])

    messages.success(request, f'Resignation for {resignation.employee} approved.')
    return redirect('attendance:resignations')


@login_required
def reject_resignation(request, pk):
    """HR/Admin rejects a resignation."""
    if not (request.user.is_admin or request.user.is_hr):
        messages.error(request, 'You do not have permission to reject resignations.')
        return redirect('attendance:resignations')

    resignation = get_object_or_404(ResignationRequest, pk=pk)
    resignation.status = 'Rejected'
    resignation.reviewed_by = request.user
    resignation.reviewed_at = timezone.now()
    resignation.save()

    messages.success(request, f'Resignation for {resignation.employee} rejected.')
    return redirect('attendance:resignations')

