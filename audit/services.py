from .models import AuditLog


def log_action(user, action, model_name, object_id='', request=None):
    ip = None
    if request:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')
    AuditLog.objects.create(
        user=user, action=action, model_name=model_name,
        object_id=str(object_id), ip_address=ip
    )

