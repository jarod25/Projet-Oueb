from django import forms
from django.contrib.auth.hashers import check_password, make_password
from .models import User


class LoginForm(forms.Form):
    userlogin = forms.CharField(
        max_length=255,
        label='Nom d’utilisateur ou email ',
        widget=forms.TextInput(attrs={'class': 'form-control rounded-3'})
    )
    password = forms.CharField(
        max_length=255,
        label='Mot de passe ',
        widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'})
    )

    def login(self, request):
        userlogin = self.cleaned_data['userlogin']
        password = self.cleaned_data['password']

        if '@' in userlogin:
            try:
                user = User.objects.get(mail=userlogin)
            except User.DoesNotExist:
                raise forms.ValidationError('Aucun compte ne correspond à ces informations de connexion')
        else:
            try:
                user = User.objects.get(username=userlogin)
            except User.DoesNotExist:
                raise forms.ValidationError('Aucun compte ne correspond à ces informations de connexion')

        if not check_password(password, user.password):
            raise forms.ValidationError('Mot de passe incorrect')

        request.session['user_id'] = user.id
        return user


class RegisterForm(forms.Form):
    mail = forms.EmailField(
        max_length=255,
        label='Adresse email ',
        widget=forms.TextInput(attrs={'class': 'form-control rounded-3'})
    )
    username = forms.CharField(
        max_length=255,
        label='Nom d’utilisateur ',
        widget=forms.TextInput(attrs={'class': 'form-control rounded-3'})
    )
    password = forms.CharField(
        max_length=255,
        label='Mot de passe ',
        widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'})
    )
    password_confirm = forms.CharField(
        max_length=255,
        label='Confirmer le mot de passe ',
        widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'})
    )

    def clean(self):
        cleaned_data = super().clean()
        mail = cleaned_data.get('mail')
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if User.objects.filter(mail=mail).exclude(username=username).exists():
            raise forms.ValidationError('Cette adresse email est déjà utilisée.')

        if User.objects.filter(username=username).exclude(mail=mail).exists():
            raise forms.ValidationError('Ce nom d’utilisateur est déjà utilisé.')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Les mots de passe ne correspondent pas')

        return cleaned_data

    def save(self):
        user = User(
            mail=self.cleaned_data["mail"],
            username=self.cleaned_data["username"],
            password=make_password(self.cleaned_data["password"]),
        )
        user.save()
        return user


class ProfileForm(forms.ModelForm):
    mail = forms.EmailField(
        max_length=255,
        label='Adresse email ',
        widget=forms.TextInput(attrs={'class': 'form-control rounded-3'})
    )
    username = forms.CharField(
        max_length=127,
        label='Nom d’utilisateur ',
        widget=forms.TextInput(attrs={'class': 'form-control rounded-3'})
    )

    class Meta:
        model = User
        fields = ['mail', 'username']

    def clean(self):
        cleaned_data = super().clean()
        mail = cleaned_data.get('mail')
        username = cleaned_data.get('username')

        if User.objects.filter(mail=mail).exclude(username=username).exists():
            raise forms.ValidationError('Cette adresse email est déjà utilisée.')

        if User.objects.filter(username=username).exclude(mail=mail).exists():
            raise forms.ValidationError('Ce nom d’utilisateur est déjà utilisé.')

        return cleaned_data

    def save(self, commit=True):
        user = self.instance
        user.mail = self.cleaned_data['mail']
        user.username = self.cleaned_data['username']
        if commit:
            user.save()
        return user


class PasswordForm(forms.Form):
    current_password = forms.CharField(
        max_length=255,
        label='Ancien mot de passe ',
        widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'})
    )
    password = forms.CharField(
        max_length=255,
        label='Nouveau mot de passe ',
        widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'})
    )
    password_confirm = forms.CharField(
        max_length=255,
        label='Confirmer le mot de passe ',
        widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'})
    )

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
            raise forms.ValidationError('Les mots de passe ne correspondent pas.')

        return cleaned_data

    def save(self):
        self.user.password = make_password(self.cleaned_data['password'])
        self.user.save()
        return self.user
