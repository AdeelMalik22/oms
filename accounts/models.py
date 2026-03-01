from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    ADMIN = 'Admin'
    HR = 'HR'
    MANAGER = 'Manager'
    EMPLOYEE = 'Employee'
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (HR, 'HR'),
        (MANAGER, 'Manager'),
        (EMPLOYEE, 'Employee'),
    ]
    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    manager = models.ForeignKey(
        'employees.Employee', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='managed_department'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_admin(self):
        if self.is_superuser:
            return True
        return bool(self.role and self.role.name == Role.ADMIN)

    @property
    def is_hr(self):
        return bool(self.role and self.role.name == Role.HR)

    @property
    def is_manager(self):
        return bool(self.role and self.role.name == Role.MANAGER)

    @property
    def is_employee(self):
        # Treat users with no role as employee so they always see something
        if not self.role:
            return not self.is_superuser
        return bool(self.role and self.role.name == Role.EMPLOYEE)

    @property
    def role_display(self):
        if self.is_superuser and not self.role:
            return 'Admin'
        return self.role.name if self.role else 'Employee'
