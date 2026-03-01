from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Asset, AssetCategory, AssetHistory
from .forms import AssetForm


@login_required
def asset_list(request):
    assets = Asset.objects.select_related('category', 'assigned_to__user').all()
    return render(request, 'assets/list.html', {'assets': assets})


@login_required
def asset_detail(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    history = asset.history.select_related('employee__user').all()
    return render(request, 'assets/detail.html', {'asset': asset, 'history': history})


@login_required
def asset_add(request):
    form = AssetForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Asset added.')
        return redirect('assets:list')
    return render(request, 'assets/form.html', {'form': form, 'title': 'Add Asset'})


@login_required
def asset_edit(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    form = AssetForm(request.POST or None, instance=asset)
    if form.is_valid():
        form.save()
        messages.success(request, 'Asset updated.')
        return redirect('assets:detail', pk=pk)
    return render(request, 'assets/form.html', {'form': form, 'title': 'Edit Asset'})


@login_required
def assign_asset(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    employee_id = request.POST.get('employee_id')
    if employee_id:
        from employees.models import Employee
        employee = get_object_or_404(Employee, pk=employee_id)
        asset.assigned_to = employee
        asset.status = 'Assigned'
        asset.save()
        AssetHistory.objects.create(asset=asset, employee=employee)
        messages.success(request, f'Asset assigned to {employee.full_name}.')
    return redirect('assets:detail', pk=pk)


@login_required
def return_asset(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    history = asset.history.filter(returned_at__isnull=True).first()
    if history:
        history.returned_at = timezone.now()
        history.save()
    asset.assigned_to = None
    asset.status = 'Available'
    asset.save()
    messages.success(request, 'Asset returned.')
    return redirect('assets:detail', pk=pk)
