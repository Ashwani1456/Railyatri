from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import AccessMixin
from django.conf import settings

from . import forms

User = get_user_model()


class AnonymousRequiredMixin(AccessMixin):
    """Restrict access to authenticated users."""
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('book:home')
        return super().dispatch(request, *args, **kwargs)


class LoginView(AnonymousRequiredMixin, auth_views.LoginView):
    template_name = "accounts/login.html"
    form_class = forms.LoginForm

    def form_valid(self, form):
        response = super().form_valid(form)
        remember_me = form.cleaned_data.get('remember_me')
        if remember_me:
            expiry = getattr(settings, "KEEP_LOGGED_DURATION", 30 * 24 * 60 * 60)
            self.request.session.set_expiry(expiry)
        return redirect('book:home')


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('book:home')


class SignUpView(AnonymousRequiredMixin, generic.CreateView):
    form_class = forms.SignupForm
    model = User
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('book:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = authenticate(
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password1"]
        )
        if user:
            login(self.request, user)
        messages.success(self.request, "You're signed up!")
        return response


class PasswordChangeView(auth_views.PasswordChangeView):
    form_class = forms.PasswordChangeForm
    template_name = 'accounts/password-change.html'
    success_url = reverse_lazy('book:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request,
            "Your password was changed, hence you have been logged out. Please relogin."
        )
        return response