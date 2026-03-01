from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Project, Task, ProjectMember
from .forms import ProjectForm, TaskForm, ProjectMemberForm
from notifications.services import create_notification


@login_required
def project_list(request):
    user = request.user
    if user.is_admin or user.is_hr:
        # Admins and HR see every project
        projects = Project.objects.prefetch_related('tasks', 'members').all()
    elif user.is_manager:
        # Managers see projects they manage OR are a member of
        try:
            emp = user.employee_profile
            from django.db.models import Q
            projects = Project.objects.prefetch_related('tasks', 'members').filter(
                Q(manager=emp) | Q(members__employee=emp)
            ).distinct()
        except Exception:
            projects = Project.objects.none()
    else:
        # Employees only see projects they are explicitly a member of
        try:
            emp = user.employee_profile
            projects = Project.objects.prefetch_related('tasks', 'members').filter(
                members__employee=emp
            ).distinct()
        except Exception:
            projects = Project.objects.none()
    return render(request, 'projects/list.html', {'projects': projects})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    user = request.user

    # Access control: employees must be a member
    if not (user.is_admin or user.is_hr):
        try:
            emp = user.employee_profile
            is_manager = user.is_manager and project.manager == emp
            is_member = project.members.filter(employee=emp).exists()
            if not (is_manager or is_member):
                messages.error(request, 'You do not have access to this project.')
                return redirect('projects:list')
        except Exception:
            messages.error(request, 'You do not have access to this project.')
            return redirect('projects:list')

    # Only project manager or HR/Admin can manage members
    can_manage_members = False
    try:
        emp = user.employee_profile
        can_manage_members = (
            user.is_admin or user.is_hr or
            (user.is_manager and project.manager == emp)
        )
    except Exception:
        can_manage_members = user.is_admin or user.is_hr

    tasks = project.tasks.select_related('assigned_to__user').all()
    members = project.members.select_related('employee__user').all()
    member_form = ProjectMemberForm() if can_manage_members else None

    return render(request, 'projects/detail.html', {
        'project': project,
        'tasks': tasks,
        'members': members,
        'member_form': member_form,
        'can_manage_members': can_manage_members,
    })


@login_required
def add_member(request, pk):
    project = get_object_or_404(Project, pk=pk)
    user = request.user

    # Permission check
    try:
        emp = user.employee_profile
        allowed = user.is_admin or user.is_hr or (user.is_manager and project.manager == emp)
    except Exception:
        allowed = user.is_admin or user.is_hr

    if not allowed:
        messages.error(request, 'You do not have permission to add members.')
        return redirect('projects:detail', pk=pk)

    if request.method == 'POST':
        form = ProjectMemberForm(request.POST)
        if form.is_valid():
            # Prevent duplicates
            employee = form.cleaned_data['employee']
            role = form.cleaned_data['role']
            _, created = ProjectMember.objects.get_or_create(
                project=project,
                employee=employee,
                defaults={'role': role},
            )
            if created:
                create_notification(
                    employee.user,
                    'Added to Project',
                    f'You have been added to project: {project.name}',
                    link=f'/projects/{project.pk}/'
                )
                messages.success(request, f'{employee.full_name} added to the project.')
            else:
                messages.info(request, f'{employee.full_name} is already a member.')
        else:
            messages.error(request, 'Invalid data. Please select a valid employee.')

    return redirect('projects:detail', pk=pk)


@login_required
def remove_member(request, pk, member_pk):
    project = get_object_or_404(Project, pk=pk)
    user = request.user

    # Permission check
    try:
        emp = user.employee_profile
        allowed = user.is_admin or user.is_hr or (user.is_manager and project.manager == emp)
    except Exception:
        allowed = user.is_admin or user.is_hr

    if not allowed:
        messages.error(request, 'You do not have permission to remove members.')
        return redirect('projects:detail', pk=pk)

    if request.method == 'POST':
        member = get_object_or_404(ProjectMember, pk=member_pk, project=project)
        name = member.employee.full_name
        member.delete()
        messages.success(request, f'{name} removed from the project.')

    return redirect('projects:detail', pk=pk)


@login_required
def project_add(request):
    form = ProjectForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Project created.')
        return redirect('projects:list')
    return render(request, 'projects/form.html', {'form': form, 'title': 'New Project'})


@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    form = ProjectForm(request.POST or None, instance=project)
    if form.is_valid():
        form.save()
        messages.success(request, 'Project updated.')
        return redirect('projects:detail', pk=pk)
    return render(request, 'projects/form.html', {'form': form, 'title': 'Edit Project'})


@login_required
def task_add(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    form = TaskForm(request.POST or None, project=project)
    if form.is_valid():
        task = form.save(commit=False)
        task.project = project
        task.save()
        if task.assigned_to:
            create_notification(
                task.assigned_to.user,
                'New Task Assigned',
                f'You have been assigned: {task.title}',
                link=f'/projects/{project.pk}/'
            )
        messages.success(request, 'Task added.')
        return redirect('projects:detail', pk=project_pk)
    return render(request, 'projects/task_form.html', {'form': form, 'project': project})


@login_required
def task_update_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    new_status = request.POST.get('status')
    if new_status in dict(Task.STATUS_CHOICES):
        task.status = new_status
        if new_status == 'Done':
            from django.utils import timezone
            task.completed_at = timezone.now()
        task.save()
    return redirect('projects:detail', pk=task.project_id)
