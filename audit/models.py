from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=200)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} ({self.timestamp:%Y-%m-%d %H:%M})"
