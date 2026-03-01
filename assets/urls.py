from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    path('', views.asset_list, name='list'),
    path('add/', views.asset_add, name='add'),
    path('<int:pk>/', views.asset_detail, name='detail'),
    path('<int:pk>/edit/', views.asset_edit, name='edit'),
    path('<int:pk>/assign/', views.assign_asset, name='assign'),
    path('<int:pk>/return/', views.return_asset, name='return'),
]

