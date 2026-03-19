from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.attendance_list, name='list'),
    path('me/', views.my_attendance, name='my'),
    path('checkin/', views.checkin, name='checkin'),
    path('checkout/', views.checkout, name='checkout'),
    path('leaves/', views.leave_list, name='leaves'),
    path('leaves/apply/', views.apply_leave, name='apply_leave'),
    path('leaves/<int:pk>/approve/', views.approve_leave, name='approve_leave'),
    path('leaves/<int:pk>/reject/', views.reject_leave, name='reject_leave'),
    path('resignations/', views.resignation_list, name='resignations'),
    path('resignations/apply/', views.apply_resignation, name='apply_resignation'),
    path('resignations/<int:pk>/approve/', views.approve_resignation, name='approve_resignation'),
    path('resignations/<int:pk>/reject/', views.reject_resignation, name='reject_resignation'),
]



