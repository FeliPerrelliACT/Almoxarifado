from .models import SaidaEstoque, TransferenciaEstoque 
from suprimentos.models import Product, Funcionario
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
        fields = ['product', 'local', 'quantidade', 'responsavel', 'observacao']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'local': forms.TextInput(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'responsavel': forms.Select(attrs={'class': 'form-control'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'product': 'Produto',
            'local': 'Local',
            'quantidade': 'Quantidade',
            'responsavel': 'Responsável',
            'observacao': 'Observação',
        }

class TransferenciaEstoqueForm(forms.ModelForm):
    class Meta:
        model = TransferenciaEstoque
        fields = ['produto', 'local_saida', 'local_entrada', 'quantidade', 'responsavel', 'observacao']
        widgets = {
            'observacao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adicione observações, se necessário.'
            }),
        }

