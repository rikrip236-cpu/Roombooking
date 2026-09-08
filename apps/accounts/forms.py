from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control','placeholder': ' Email'})
    )
    first_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control','placeholder': ' prénom'})
    )
    last_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control','placeholder': ' Nom'})
    )
    department = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Département'})
    )
    floor = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'étage'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'department', 'floor', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': "Nom d'utilisateur"})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Mot de passe'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmer le mot de passe'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Un compte existe déjà avec cet e-mail.')
        return email


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': "Nom d'utilisateur"
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Mot de passe'
    }))
