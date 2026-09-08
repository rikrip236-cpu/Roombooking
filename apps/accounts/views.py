from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages

from .forms import UserRegistrationForm, UserLoginForm
from .models import User


class RegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Compte créé avec succès. Vous pouvez maintenant vous connecter.')
        return response


class CustomLoginView(LoginView):
    form_class = UserLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


def logout_view(request):
    logout(request)
    messages.info(request, 'Vous avez été déconnecté.')
    return redirect('accounts:login')
