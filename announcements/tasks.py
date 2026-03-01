from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_announcement_email(announcement_id):
    """Send announcement email blast to target department or all employees."""
    from announcements.models import Announcement
    from accounts.models import CustomUser

    try:
        announcement = Announcement.objects.get(pk=announcement_id)
    except Announcement.DoesNotExist:
        return "Announcement not found."

    users = CustomUser.objects.filter(is_active=True)
    if announcement.target_department:
        users = users.filter(department=announcement.target_department)

    emails = list(users.values_list('email', flat=True))
    if emails:
        send_mail(
            subject=f'[OMS Announcement] {announcement.title}',
            message=announcement.content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=emails,
            fail_silently=True,
        )
    return f"Sent to {len(emails)} recipients."

