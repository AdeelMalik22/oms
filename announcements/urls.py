from django.urls import path
from . import views

app_name = 'announcements'

urlpatterns = [
    path('', views.announcement_list, name='list'),
    path('add/', views.announcement_add, name='add'),
    path('<int:pk>/pin/', views.toggle_pin, name='pin'),
    path('<int:pk>/delete/', views.announcement_delete, name='delete'),
]

