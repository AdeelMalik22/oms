from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import LoginForm, UserProfileForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
        )
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard:index'))
        messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def profile_settings(request):
    form = UserProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    pw_form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST':
        if 'update_profile' in request.POST and form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
        elif 'change_password' in request.POST and pw_form.is_valid():
            user = pw_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed.')
    return render(request, 'accounts/settings.html', {'form': form, 'pw_form': pw_form})
