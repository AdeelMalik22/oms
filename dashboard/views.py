from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta, date as date_type
from employees.models import Employee
from attendance.models import Attendance, LeaveRequest, LeaveBalance
from projects.models import Project, Task
from announcements.models import Announcement
from notifications.models import Notification
from audit.models import AuditLog


def _get_or_create_employee(user):
    """Get or silently create an Employee profile for the user."""
    try:
        return user.employee_profile
    except Employee.DoesNotExist:
        from accounts.models import Department
        dept = user.department or Department.objects.first()
        if dept is None:
            return None
        return Employee.objects.create(
            user=user,
            department=dept,
            hire_date=timezone.now().date(),
        )


def _build_week_data(emp, today):
    """Build a list of 7 dicts (Mon-Sun of current week) with hours worked."""
    monday = today - timedelta(days=today.weekday())
    week_days = []
    for i in range(7):
        day = monday + timedelta(days=i)
        rec = Attendance.objects.filter(employee=emp, date=day).first()
        hours = 0
        label = day.strftime('%a')
        if rec and rec.check_in:
            if rec.check_out:
                import datetime
                ci = datetime.datetime.combine(day, rec.check_in)
                co = datetime.datetime.combine(day, rec.check_out)
                hours = round((co - ci).total_seconds() / 3600, 1)
            else:
                hours = 0
        week_days.append({
            'label': label,
            'date': day.strftime('%d %b'),
            'hours': hours,
            'is_today': day == today,
            'is_future': day > today,
            'status': rec.status if rec else ('Future' if day > today else 'Absent'),
        })
    return week_days


@login_required
def index(request):
    from django.db.models import Q
    today = timezone.now().date()
    user = request.user

    # Announcements filtered by department (company-wide OR user's dept)
    announcements_qs = Announcement.objects.filter(is_active=True, is_pinned=True)
    if not (user.is_admin or user.is_hr):
        announcements_qs = announcements_qs.filter(
            Q(target_department__isnull=True) | Q(target_department=user.department)
        )

    context = {
        'today': today,
        'announcements': announcements_qs[:5],
        'unread_count': Notification.objects.filter(recipient=user, is_read=False).count(),
    }

    # Every user gets a check-in widget — get or create their employee profile
    emp = _get_or_create_employee(user)
    if emp:
        context['my_attendance'] = Attendance.objects.filter(employee=emp, date=today).first()

    if user.is_admin or user.is_hr:
        total_emp = Employee.objects.filter(user__is_active=True).count()
        present_today = Attendance.objects.filter(
            date=today, status__in=['Present', 'Late', 'Half-Day']
        ).count()
        # Absent = all active employees who did NOT check in today
        absent_today = max(0, total_emp - present_today)
        context.update({
            'total_employees': total_emp,
            'present_today': present_today,
            'absent_today': absent_today,
            'pending_leaves': LeaveRequest.objects.filter(status='Pending').count(),
            'active_projects': Project.objects.filter(status='Active').count(),
            'overdue_tasks': Task.objects.filter(due_date__lt=today).exclude(status='Done').count(),
            'recent_attendance': Attendance.objects.select_related('employee__user').filter(date=today)[:10],
            'recent_leaves': LeaveRequest.objects.select_related(
                'employee__user', 'leave_type'
            ).filter(status='Pending').order_by('-applied_at')[:5],
        })

    elif user.is_manager:
        try:
            from django.db.models import Q as Q2
            from projects.models import ProjectMember as PM
            team_emp_ids = PM.objects.filter(
                Q2(project__manager=emp)
            ).values_list('employee_id', flat=True).distinct()

            team_pending_leaves = LeaveRequest.objects.filter(
                employee_id__in=team_emp_ids, status='Pending'
            ).select_related('employee__user', 'leave_type').order_by('-applied_at')

            context.update({
                'my_projects': Project.objects.filter(
                    Q(manager=emp) | Q(members__employee=emp)
                ).distinct() if emp else Project.objects.none(),
                'overdue_tasks': Task.objects.filter(
                    project__manager=emp, due_date__lt=today
                ).exclude(status='Done').count() if emp else 0,
                'team_pending_leaves': team_pending_leaves,
                'pending_leave_count': team_pending_leaves.count(),
            })
        except Exception:
            context.update({'my_projects': [], 'overdue_tasks': 0, 'team_pending_leaves': [], 'pending_leave_count': 0})

    else:
        # Standard employee
        if emp:
            try:
                context['my_tasks'] = Task.objects.filter(
                    assigned_to=emp
                ).exclude(status='Done').select_related('project')[:5]
                context['my_month_attendance'] = Attendance.objects.filter(
                    employee=emp,
                    date__year=today.year,
                    date__month=today.month,
                    status='Present',
                ).count()
                context['days_in_company'] = (today - emp.hire_date).days if emp.hire_date else None
                context['hire_date'] = emp.hire_date
                context['week_attendance'] = _build_week_data(emp, today)
                context['week_present'] = Attendance.objects.filter(
                    employee=emp,
                    date__gte=today - timedelta(days=today.weekday()),
                    date__lte=today,
                    status='Present',
                ).count()
                context['leave_balances'] = LeaveBalance.objects.filter(
                    employee=emp, year=today.year
                ).select_related('leave_type')
                context['my_pending_leaves'] = LeaveRequest.objects.filter(
                    employee=emp, status='Pending'
                ).select_related('leave_type').order_by('-applied_at')[:3]
            except Exception:
                pass
        context.setdefault('my_month_attendance', 0)
        context.setdefault('week_attendance', [])
        context.setdefault('my_tasks', [])
        context.setdefault('week_present', 0)
        context.setdefault('leave_balances', [])
        context.setdefault('my_pending_leaves', [])

    return render(request, 'dashboard/index.html', context)


@login_required
def audit_log(request):
    qs = AuditLog.objects.select_related('user').all()
    q = request.GET.get('q', '')
    if q:
        from django.db.models import Q
        qs = qs.filter(Q(action__icontains=q) | Q(model_name__icontains=q) | Q(user__username__icontains=q))
    paginator = Paginator(qs, 30)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'dashboard/audit_log.html', {'page_obj': page, 'q': q})
