from django.contrib import admin
from .models import Project, Task, ProjectMember


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ['title', 'assigned_to', 'priority', 'status', 'due_date']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'manager', 'start_date', 'end_date', 'progress']
    list_filter = ['status']
    inlines = [TaskInline]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'assigned_to', 'priority', 'status', 'due_date']
    list_filter = ['status', 'priority', 'project']
