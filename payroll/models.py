from django.db import models
from django.conf import settings


class PayrollTemplate(models.Model):
    employee = models.OneToOneField('employees.Employee', on_delete=models.CASCADE, related_name='payroll_template')
    default_allowances = models.JSONField(default=list)
    default_deductions = models.JSONField(default=list)

    def __str__(self):
        return f"Template for {self.employee}"


class Payroll(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'), ('Generated', 'Generated'), ('Paid', 'Paid'),
    ]
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='payrolls')
    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='generated_payrolls'
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'month', 'year')
        ordering = ['-year', '-month']

    def calculate_net(self):
        self.net_salary = self.basic_salary + self.total_allowances - self.total_deductions
        self.save(update_fields=['net_salary'])

    def __str__(self):
        return f"{self.employee} - {self.month}/{self.year}"


class Allowance(models.Model):
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='allowances')
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.amount}"


class Deduction(models.Model):
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='deductions')
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.amount}"
