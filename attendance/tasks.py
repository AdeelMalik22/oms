from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from accounts.models import CustomUser
from .models import ResignationRequest


@shared_task
def send_leave_decision_email(employee_email, employee_name, leave_type, status, start_date, end_date):
    """Send email notification when a leave request is approved or rejected."""
    subject = f'Leave Request {status} — {leave_type}'
    message = (
        f'Dear {employee_name},\n\n'
        f'Your {leave_type} leave request from {start_date} to {end_date} '
        f'has been {status.lower()}.\n\n'
        f'Regards,\nOMS HR Team'
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [employee_email], fail_silently=True)


@shared_task
def deactivate_resigned_users():
    """Deactivate any users whose approved resignation date has passed."""
    today = timezone.now().date()
    user_ids = ResignationRequest.objects.filter(
        status='Approved', requested_last_working_date__lte=today
    ).values_list('employee__user_id', flat=True)
    if not user_ids:
        return 0
    return CustomUser.objects.filter(id__in=user_ids, is_active=True).update(is_active=False)
