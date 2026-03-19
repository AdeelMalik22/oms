from django.db import models
from django.conf import settings


class LeaveType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    max_days_per_year = models.PositiveIntegerField(default=0)
    is_paid = models.BooleanField(default=True)
    color = models.CharField(max_length=20, default='primary', help_text='Bootstrap color (primary, success, danger, warning, info, etc.)')
    icon = models.CharField(max_length=50, default='bi-calendar', help_text='Bootstrap icon class')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'), ('Absent', 'Absent'),
        ('Late', 'Late'), ('Half-Day', 'Half-Day'),
    ]
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Present')
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.status}"


class LeaveBalance(models.Model):
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    total_days = models.PositiveIntegerField(default=0)
    used_days = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('employee', 'leave_type', 'year')

    @property
    def remaining_days(self):
        return self.total_days - self.used_days

    def __str__(self):
        return f"{self.employee} - {self.leave_type} - {self.year}"


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected'),
    ]
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='approved_leaves'
    )
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.status})"

    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1
