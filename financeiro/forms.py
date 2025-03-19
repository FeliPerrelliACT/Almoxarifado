from django import forms
from .models import PlanosFinanceiros

class PlanosFinanceirosForm(forms.ModelForm):
    class Meta:
        model = PlanosFinanceiros
        fields = ['finance_name', 'status']
        labels = {
            'finance_name': 'Nome do Plano Financeiro',
            'status': 'Ativo'
        }
        widgets = {
            'finance_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite o nome'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    # Garantir que o valor padrão de 'status' seja True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Definir o valor padrão de 'status' como True
        if self.instance and self.instance.status is None:
            self.instance.status = True



