from .models import SaidaEstoque, TransferenciaEstoque 
from suprimentos.models import Product, Funcionario, CentroCusto
from django import forms

class EntradaEstoqueForm(forms.Form):
    local = forms.CharField(label="Local", max_length=100)
    produto = forms.ModelChoiceField(
        queryset=Product.objects.filter(status=1), 
        label="Produto"
    )
    quantidade = forms.IntegerField(label="Quantidade", min_value=1)

class SaidaEstoqueForm(forms.Form):
    local = forms.CharField(label="Local", max_length=255)
    responsavel = forms.ModelChoiceField(queryset=Funcionario.objects.filter(status=True), label="Responsável")
    centro_custo = forms.ModelChoiceField(queryset=CentroCusto.objects.all(), label="Centro de Custo")
    observacao = forms.CharField(widget=forms.Textarea, required=False, label="Observação")

    def clean_quantidade(self):
        quantidade = self.cleaned_data.get('quantidade')
        if quantidade <= 0:
            raise forms.ValidationError("A quantidade deve ser maior que zero.")
        return quantidade

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

