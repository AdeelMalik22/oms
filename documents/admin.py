from django.contrib import admin
from .models import Document, DocumentCategory, DocumentVersion


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'department', 'version', 'uploaded_by', 'created_at']
    list_filter = ['category', 'department']
    search_fields = ['title']


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ['document', 'version', 'uploaded_by', 'uploaded_at']
