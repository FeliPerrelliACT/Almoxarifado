from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.conf import settings
from accounts.forms import User
from django.db import models
from django import forms
import os

class Product(models.Model):
    product_name = models.CharField(max_length=100)
    unidade_medida = models.CharField(max_length=50)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.product_name

# Modelo de Solicitação (Request)
class Request(models.Model):
    id = models.AutoField(primary_key=True)
    request_text = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=User.objects.first)  # Ou qualquer lógica para pegar o usuário
    pub_date = models.DateTimeField(default=now)
    status = models.CharField(max_length=50, default="criada")
    comment = models.TextField(blank=True, null=True)
    
    company = models.CharField(max_length=255, blank=True, null=True)
    supplier = models.CharField(max_length=255, blank=True, null=True)
    cost_center = models.CharField(max_length=255, blank=True, null=True)
    financial_plan = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Request {self.id} - {self.status}"

# Modelo que liga a solicitação ao produto
class RequestProduct(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='request_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.product_name} ({self.quantity} unidades)"

# Formulário para Solicitação
class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ['request_text']

# Formulário para produtos dentro de uma solicitação
class RequestProductForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), required=True)
    quantity = forms.IntegerField(min_value=1, required=True)

# Modelo de Pedido de Produto
class ProductOrder(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity}"

# Modelo de Arquivo para Solicitação
class RequestFile(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')  # Para outros tipos de arquivos, como PDFs, ZIPs, etc.
    imagem = models.ImageField(upload_to='requestfiles/', null=True, blank=True)  # Para as imagens
    data_adicao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for Request {self.request.id}"

class PollRequest(models.Model):
    request_text = models.CharField(max_length=255)
    pub_date = models.DateTimeField()
    status = models.CharField(max_length=50)
    comment = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.request_text

class Quotation(models.Model):
    request = models.ForeignKey('Request', on_delete=models.CASCADE)  # Relaciona a cotação com a solicitação
    file = models.FileField(upload_to='quotations/')  # Caminho do arquivo
    created_at = models.DateTimeField(auto_now_add=True)  # Data de criação
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Cotação para {self.request.request_text} - {self.file_id}"

