from django.db import models


class AssetCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Asset(models.Model):
    STATUS_CHOICES = [
        ('Available', 'Available'), ('Assigned', 'Assigned'),
        ('Under Repair', 'Under Repair'), ('Disposed', 'Disposed'),
    ]
    name = models.CharField(max_length=200)
    category = models.ForeignKey(AssetCategory, on_delete=models.SET_NULL, null=True)
    serial_number = models.CharField(max_length=100, unique=True, blank=True)
    assigned_to = models.ForeignKey(
        'employees.Employee', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='assigned_assets'
    )
    purchase_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available')
    condition = models.CharField(max_length=100, blank=True)
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} ({self.serial_number})"


class AssetHistory(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='history')
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.asset} → {self.employee}"
