from django import forms
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User


class LoginForm(forms.Form):
    userlogin = forms.CharField(max_length=255, label='Nom d’utilisateur ou email ',
                                widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
    password = forms.CharField(max_length=255, label='Mot de passe ',
                               widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'}))


class RegisterForm(forms.Form):
    email = forms.EmailField(max_length=255, label='Adresse email ',
                             widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
    username = forms.CharField(max_length=255, label='Nom d’utilisateur ',
                               widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
    password = forms.CharField(max_length=255, label='Mot de passe ',
                               widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'}))
    password_confirm = forms.CharField(max_length=255, label='Confirmer le mot de passe ',
                                       widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'}))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Les mots de passe ne correspondent pas')

        return cleaned_data

    def save(self):
        return User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password']
        )


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(max_length=255, label='Adresse email ',
                             widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
    username = forms.CharField(max_length=255, label='Nom d’utilisateur ',
                               widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))

    class Meta:
        model = User
        fields = ['email', 'username']

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        username = cleaned_data.get('username')

        if User.objects.filter(email=email).exclude(username=username).exists():
            raise forms.ValidationError('Cette adresse email est déjà utilisée')
        if User.objects.filter(username=username).exclude(email=email).exists():
            raise forms.ValidationError('Ce nom d’utilisateur est déjà utilisé')

        return cleaned_data

    def save(self, commit=True):
        user = self.instance
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['username']
        user.save()
        return user


class PasswordForm(forms.Form):
    current_password = forms.CharField(max_length=255, label='Ancien mot de passe ',
                                       widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'}))
    password = forms.CharField(max_length=255, label='Nouveau mot de passe ',
                               widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'}))
    password_confirm = forms.CharField(max_length=255, label='Confirmer le mot de passe ',
                                       widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'}))

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get('current_password')
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if not check_password(current_password, self.user.password):
            raise forms.ValidationError('Le mot de passe actuel est incorrect.')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Les mots de passe ne correspondent pas')

        return cleaned_data

    def save(self, user):
        user.set_password(self.cleaned_data['password'])
        user.save()
        return user
