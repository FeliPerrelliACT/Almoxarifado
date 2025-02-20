from .models import Request, Product, RequestProduct, Quotation
from django import forms

UNIT_CHOICES = [
    ('km', 'Quilômetro (km)'), ('m', 'Metro (m)'), ('cm', 'Centímetro (cm)'), ('mm', 'Milímetro (mm)'),
    ('in', 'Polegada (in)'), ('kg', 'Quilograma (kg)'), ('g', 'Grama (g)'), ('mg', 'Miligrama (mg)'),
    ('t', 'Tonelada (t)'), ('lb', 'Libras (lb)'), ('oz', 'Onça (oz)'), ('ct', 'Quilate (ct)'),
    ('m2', 'Metro quadrado (m²)'), ('km2', 'Quilômetro quadrado (km²)'), ('cm2', 'Centímetro quadrado (cm²)'),
    ('ha', 'Hectare (ha)'), ('acre', 'Acre'), ('mi2', 'Milha quadrada (mi²)'), ('L', 'Litro (L)'),
    ('mL', 'Mililitro (mL)'), ('m3', 'Metro cúbico (m³)'), ('cm3', 'Centímetro cúbico (cm³)'),
    ('galao', 'Galão'), ('fl_oz', 'Onça fluida (fl oz)'), ('barril', 'Barril'),
    ('UND', 'Unidade'), ('DEZ', 'Dezena'), ('CEN', 'Centena'), ('MIL', 'Milhar'),
    ('DEZ_MIL', 'Dezena de milhar'), ('CEN_MIL', 'Centena de milhar'), ('MILHAO', 'Milhão'),
    ('DEZ_MILHAO', 'Dezena de milhão'), ('MILHAO_MIL', 'Milhão de milhar'), ('BILHAO', 'Bilhão')
]

# Formulário de Solicitação
class RequestForm(forms.ModelForm):
    # A referência ao modelo Cotacao foi removida

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Garantir que pelo menos um produto será mostrado; default = 1
        num_products = kwargs.get('data', {}).get('num_products', 1)

        # Adicionar campos de produto e quantidade dinamicamente
        for i in range(1, int(num_products) + 1):
            self.fields[f'product_{i}'] = forms.ModelChoiceField(
                queryset=Product.objects.all(),
                required=True,
                label=f'Produto {i}'
            )
            self.fields[f'quantity_{i}'] = forms.IntegerField(
                min_value=1,
                required=True,
                label=f'Quantidade {i}'
            )

    def save(self, commit=True):
        # Criação da solicitação
        instance = super().save(commit=False)
        if commit:
            instance.save()

            # Processar produtos e quantidades
            num_products = int(self.data.get('num_products', 1))
            for i in range(1, num_products + 1):
                product = self.cleaned_data.get(f'product_{i}')
                quantity = self.cleaned_data.get(f'quantity_{i}')

                if product and quantity:
                    RequestProduct.objects.create(
                        request=instance,
                        product=product,
                        quantity=quantity
                    )

        return instance

    class Meta:
        model = Request
        fields = ['request_text', 'status']  # Inclui apenas os campos do modelo Request

# Formulário para Produto na Solicitação
class RequestProductForm(forms.ModelForm):
    class Meta:
        model = RequestProduct
        fields = ['product', 'quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': '1', 'class': 'form-control'}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity <= 0:
            raise forms.ValidationError("A quantidade deve ser maior que zero.")
        return quantity

# Formulário de Produto
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name','unidade_medida', 'valor']
        widgets = {
            'product_name': forms.TextInput(attrs={'placeholder': 'Nome do produto', 'class': 'form-control'}),
            'unidade_medida': forms.Select(choices=UNIT_CHOICES, attrs={'class': 'form-control'}),

        }

    def clean(self):
        cleaned_data = super().clean()
        valor = cleaned_data.get('valor')
        unidade_medida = cleaned_data.get('unidade_medida')

        # Garantir que a unidade de medida seja válida
        if unidade_medida not in dict(UNIT_CHOICES):
            self.add_error('unidade_medida', "Unidade de medida inválida.")


        return cleaned_data

# Formulário para upload de arquivo
class UploadFileForm(forms.Form):
    file = forms.FileField()

    def clean_file(self):
        file = self.cleaned_data.get('file')
        # Validação para aceitar apenas arquivos com extensão .jpg ou .png (case insensitive)
        if not (file.name.lower().endswith('.jpg') or file.name.lower().endswith('.png')):
            raise forms.ValidationError("Arquivo não permitido!")
        return file

class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['file', 'supplier']
