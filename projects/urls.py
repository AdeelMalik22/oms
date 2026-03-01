from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='list'),
    path('add/', views.project_add, name='add'),
    path('<int:pk>/', views.project_detail, name='detail'),
    path('<int:pk>/edit/', views.project_edit, name='edit'),
    path('<int:pk>/members/add/', views.add_member, name='add_member'),
    path('<int:pk>/members/<int:member_pk>/remove/', views.remove_member, name='remove_member'),
    path('<int:project_pk>/tasks/add/', views.task_add, name='task_add'),
    path('tasks/<int:pk>/status/', views.task_update_status, name='task_status'),
]

