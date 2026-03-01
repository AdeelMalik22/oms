from django.contrib import admin
from .models import Payroll, Allowance, Deduction, PayrollTemplate


class AllowanceInline(admin.TabularInline):
    model = Allowance
    extra = 0


class DeductionInline(admin.TabularInline):
    model = Deduction
    extra = 0


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ['employee', 'month', 'year', 'basic_salary', 'net_salary', 'status']
    list_filter = ['status', 'year', 'month']
    inlines = [AllowanceInline, DeductionInline]


@admin.register(PayrollTemplate)
class PayrollTemplateAdmin(admin.ModelAdmin):
    list_display = ['employee']
