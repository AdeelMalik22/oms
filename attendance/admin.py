from django.contrib import admin
from .models import Attendance, LeaveRequest, LeaveType, LeaveBalance, ResignationRequest


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'check_in', 'check_out', 'status']
    list_filter = ['status', 'date']
    search_fields = ['employee__user__first_name', 'employee__user__last_name']
    date_hierarchy = 'date'


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'status', 'applied_at']
    list_filter = ['status', 'leave_type']


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'max_days_per_year', 'is_paid']


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'year', 'total_days', 'used_days', 'remaining_days']
    list_filter = ['year', 'leave_type']


@admin.register(ResignationRequest)
class ResignationRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'requested_last_working_date', 'status', 'applied_at', 'reviewed_by']
    list_filter = ['status', 'applied_at']
    search_fields = ['employee__user__first_name', 'employee__user__last_name']
    date_hierarchy = 'applied_at'
    readonly_fields = ['applied_at', 'reviewed_at', 'reviewed_by']

