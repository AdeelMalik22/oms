from django.contrib import admin
from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'target_department', 'is_pinned', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_pinned', 'target_department']
