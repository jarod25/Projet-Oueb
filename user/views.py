from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from . import forms

def index(request):
    return render(request, 'base.html')

@login_required
def home(request):
    return render(request, 'home.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

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
                return redirect('home')
            else:
                messages.error(request, 'Nom d’utilisateur ou mot de passe incorrect')
    return render(request, 'login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = forms.RegisterForm()
    if request.method == 'POST':
        form = forms.RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Compte créé pour {user.username}')
            return redirect('home')
    else:
        return render(request, 'register.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('index')