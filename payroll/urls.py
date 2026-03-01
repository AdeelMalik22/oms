from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('', views.payroll_list, name='list'),
    path('generate/', views.generate_payroll, name='generate'),
    path('my-payslips/', views.my_payslips, name='my_payslips'),
    path('<int:pk>/', views.payslip_detail, name='payslip'),
    path('<int:pk>/pdf/', views.payslip_pdf, name='payslip_pdf'),
    path('<int:pk>/mark-paid/', views.mark_paid, name='mark_paid'),
]

