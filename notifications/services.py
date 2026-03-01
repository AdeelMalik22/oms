from .models import Notification


def create_notification(user, title, message, notif_type='info', link=''):
    Notification.objects.create(
        recipient=user, title=title, message=message, type=notif_type, link=link
    )

