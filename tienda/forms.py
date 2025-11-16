from django import forms
from .models import Producto, Categoria

class ProductoForm(forms.ModelForm):
    stock = forms.IntegerField(label='Stock', min_value=0, initial=0)

    class Meta:
        model = Producto
        fields = ['nombre', 'precio', 'categoria', 'imagen', 'stock']
        widgets = {
            'categoria': forms.CheckboxSelectMultiple(),
        }

class CategoriaForm(forms.ModelForm):
    class Meta:
        model=Categoria
        fields="__all__"