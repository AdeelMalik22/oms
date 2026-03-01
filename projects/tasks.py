from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task
def check_task_deadlines():
    """Daily task: notify employees of tasks due within 3 days."""
    from projects.models import Task
    from notifications.services import create_notification

    today = timezone.now().date()
    deadline = today + timedelta(days=3)
    upcoming_tasks = Task.objects.filter(
        due_date__range=[today, deadline],
        assigned_to__isnull=False
    ).exclude(status='Done').select_related('assigned_to__user', 'project')

    for task in upcoming_tasks:
        days_left = (task.due_date - today).days
        label = "today" if days_left == 0 else f"in {days_left} day(s)"
        create_notification(
            user=task.assigned_to.user,
            title=f'Task Due {label.title()}',
            message=f'"{task.title}" in project "{task.project.name}" is due {label}.',
            notif_type='warning',
            link=f'/projects/{task.project_id}/',
        )
    return f"Checked {upcoming_tasks.count()} upcoming tasks."

