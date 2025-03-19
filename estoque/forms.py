from .models import EntradaEstoque, SaidaEstoque
from django.forms import modelformset_factory
from suprimentos.models import Product
from django import forms

class EntradaEstoqueForm(forms.Form):
    local = forms.CharField(label="Local", max_length=100)
    produto = forms.ModelChoiceField(
        queryset=Product.objects.filter(status=1), 
        label="Produto"
    )
    quantidade = forms.IntegerField(label="Quantidade", min_value=1)

class SaidaEstoqueForm(forms.ModelForm):
    class Meta:
        model = SaidaEstoque
        fields = ['product', 'local', 'quantidade']

