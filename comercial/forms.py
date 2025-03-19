from django import forms
from .models import CentroCusto

class CentroCustoForm(forms.ModelForm):
    class Meta:
        model = CentroCusto
        fields = ['name']
        labels = {
            'name': 'Centro de Custo',
        }

