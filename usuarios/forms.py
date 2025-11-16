from django import forms
from .models import Usuario
from django.contrib.auth.models import User


class UsuarioForm(forms.ModelForm):
    username = forms.CharField(max_length=150, label='nombre de usuario')
    password = forms.CharField(widget=forms.PasswordInput, label='contraseña', required=False)

    class Meta:
        model = Usuario
        fields = ['nombre_completo', 'rut', 'telefono', 'rol']

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password']
        )
        usuario = super().save(commit=False)
        usuario.user = user
        if commit:
            usuario.save()
        return usuario
