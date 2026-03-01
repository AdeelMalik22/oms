from django.contrib import admin
from .models import Employee, Designation


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'department', 'designation', 'hire_date', 'salary']
    list_filter = ['department', 'designation']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ['title', 'department', 'level']
    list_filter = ['department']
