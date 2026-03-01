from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('', views.employee_list, name='list'),
    path('add/', views.employee_add, name='add'),
    path('export/csv/', views.employee_export_csv, name='export_csv'),
    path('departments/', views.department_list, name='departments'),
    path('<int:pk>/', views.employee_detail, name='detail'),
    path('<int:pk>/edit/', views.employee_edit, name='edit'),
    path('<int:pk>/deactivate/', views.employee_deactivate, name='deactivate'),
]

