from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Role, Department


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'department', 'is_active']
    list_filter = ['role', 'department', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('OMS Info', {'fields': ('role', 'department', 'profile_picture', 'phone')}),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager', 'created_at']
