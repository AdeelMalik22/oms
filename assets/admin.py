from django.contrib import admin
from .models import Asset, AssetCategory, AssetHistory


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'serial_number', 'assigned_to', 'status', 'value']
    list_filter = ['status', 'category']


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(AssetHistory)
class AssetHistoryAdmin(admin.ModelAdmin):
    list_display = ['asset', 'employee', 'assigned_at', 'returned_at']
