from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from . import forms


def index(request):
    return render(request, 'base.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('room_list')

    form = forms.LoginForm()
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['userlogin'],
                password=form.cleaned_data['password']
            )
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenue {user.username}')
                return redirect('room_list')
            else:
                messages.error(request, 'Nom d’utilisateur ou mot de passe incorrect')
    return render(request, 'login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('room_list')

    form = forms.RegisterForm()
    if request.method == 'POST':
        form = forms.RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Compte créé pour {user.username}')
            return redirect('room_list')
    else:
        return render(request, 'register.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('index')


@login_required
def profile_view(request):
    user_form = forms.ProfileForm(instance=request.user)
    pwd_form = forms.PasswordForm(user=request.user)
    if request.method == 'POST':
        if 'user_form_submit' in request.POST:
            user_form = forms.ProfileForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Profil mis à jour avec succès.')
        elif 'pwd_form_submit' in request.POST:
            pwd_form = forms.PasswordForm(request.user, request.POST)
            if pwd_form.is_valid():
                pwd_form.save(request.user)
                messages.success(request, 'Mot de passe mis à jour avec succès. Veuillez vous reconnecter.')

    return render(request, 'profile.html', {'user_form': user_form, 'pwd_form': pwd_form})
