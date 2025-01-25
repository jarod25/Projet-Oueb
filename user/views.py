from django.contrib import messages
from django.shortcuts import render, redirect
from . import forms
from user import login_required
from .models import User


def index(request):
    return render(request, 'base.html')


def login_view(request):
    if request.session.get('user_id'):
        return redirect('room_list')

    form = forms.LoginForm()
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            user = form.login(request)
            if user is not None:
                return redirect('room_list')
            else:
                return render(request, 'login.html', {'form': form})
        else:
            return render(request, 'login.html', {'form': form})
    return render(request, 'login.html', {'form': form})


def register_view(request):
    if request.session.get('user_id'):
        return redirect('room_list')

    form = forms.RegisterForm()
    if request.method == 'POST':
        form = forms.RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Compte créé pour {user.username}, vous pouvez vous connecter.')
            return redirect('login')
        else:
            return render(request, 'register.html', {'form': form})
    else:
        return render(request, 'register.html', {'form': form})


@login_required
def logout_view(request):
    request.session.flush()
    return redirect('index')


@login_required
def profile_view(request):
    user = request.session.get('user_id')
    if not user:
        return redirect('login')

    user_instance = User.objects.get(id=user)
    user_form = forms.ProfileForm(instance=user_instance)
    pwd_form = forms.PasswordForm(user=user_instance)
    if request.method == 'POST':
        if 'user_form_submit' in request.POST:
            user_form = forms.ProfileForm(request.POST, instance=user_instance)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Profil mis à jour avec succès.')
                return redirect('profile')
            else:
                return render(request, 'profile.html', {'user_form': user_form, 'pwd_form': pwd_form})
        elif 'pwd_form_submit' in request.POST:
            pwd_form = forms.PasswordForm(user=user_instance, data=request.POST)
            if pwd_form.is_valid():
                pwd_form.save()
                messages.success(request, 'Mot de passe mis à jour avec succès. Veuillez vous reconnecter.')
                return redirect('login')
            else:
                return render(request, 'profile.html', {'user_form': user_form, 'pwd_form': pwd_form})

    return render(request, 'profile.html', {'user_form': user_form, 'pwd_form': pwd_form})
