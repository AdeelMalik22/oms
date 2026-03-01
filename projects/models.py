from django.db import models


class Project(models.Model):
    STATUS_CHOICES = [
        ('Planning', 'Planning'), ('Active', 'Active'),
        ('On Hold', 'On Hold'), ('Completed', 'Completed'),
    ]
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Planning')
    manager = models.ForeignKey(
        'employees.Employee', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='managed_projects'
    )
    budget = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def progress(self):
        total = self.tasks.count()
        if total == 0:
            return 0
        done = self.tasks.filter(status='Done').count()
        return int((done / total) * 100)


class ProjectMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE)
    role = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ('project', 'employee')

    def __str__(self):
        return f"{self.employee} in {self.project}"


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High'), ('Critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('To-Do', 'To-Do'), ('In Progress', 'In Progress'),
        ('Review', 'Review'), ('Done', 'Done'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ForeignKey(
        'employees.Employee', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='tasks'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='To-Do')
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} [{self.status}]"
