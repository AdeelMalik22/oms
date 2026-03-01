from django.db import models
from django.conf import settings


class Designation(models.Model):
    title = models.CharField(max_length=100)
    department = models.ForeignKey('accounts.Department', on_delete=models.CASCADE, related_name='designations')
    level = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.title} ({self.department})"


class Employee(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_profile')
    department = models.ForeignKey('accounts.Department', null=True, blank=True, on_delete=models.SET_NULL)
    designation = models.ForeignKey(Designation, null=True, blank=True, on_delete=models.SET_NULL)
    hire_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    address = models.TextField(blank=True)
    nic = models.CharField(max_length=20, blank=True, verbose_name='NIC')
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return str(self.user)

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username
