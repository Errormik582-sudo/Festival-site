"""Формы регистрации."""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False, label='Email')
    phone = forms.CharField(max_length=20, required=False, label='Телефон')

    class Meta:
        model = User
        fields = ('username', 'email', 'phone')

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            Profile.objects.create(
                user=user,
                phone=self.cleaned_data.get('phone', ''),
            )
        return user