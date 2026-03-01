from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Announcement
from .forms import AnnouncementForm
from .tasks import send_announcement_email


@login_required
def announcement_list(request):
    from django.db.models import Q
    user = request.user
    # Show company-wide (no target dept) OR targeted at the user's own department
    qs = Announcement.objects.filter(is_active=True).select_related('created_by', 'target_department')
    if not (user.is_admin or user.is_hr):
        qs = qs.filter(
            Q(target_department__isnull=True) |
            Q(target_department=user.department)
        )
    paginator = Paginator(qs, 10)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'announcements/list.html', {'page_obj': page})


@login_required
def announcement_add(request):
    form = AnnouncementForm(request.POST or None)
    if form.is_valid():
        announcement = form.save(commit=False)
        announcement.created_by = request.user
        announcement.save()
        send_announcement_email.delay(announcement.pk)
        messages.success(request, 'Announcement posted.')
        return redirect('announcements:list')
    return render(request, 'announcements/form.html', {'form': form, 'title': 'New Announcement'})


@login_required
def toggle_pin(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.is_pinned = not announcement.is_pinned
    announcement.save()
    return redirect('announcements:list')


@login_required
def announcement_delete(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.is_active = False
    announcement.save()
    messages.success(request, 'Announcement removed.')
    return redirect('announcements:list')
