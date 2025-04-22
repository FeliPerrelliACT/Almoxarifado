from suprimentos.models import Product, Funcionario, CentroCusto
from django.utils.timezone import now
from django.utils import timezone
from django.conf import settings
from accounts.forms import User
from django.db import models

# Modelo de Estoque
class Estoque(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    local = models.CharField(max_length=255)
    quantidade = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.product_name} - {self.local}"

# Modelo de log de entradas no estoque
class EntradaEstoque(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    local = models.CharField(max_length=255)
    quantidade = models.PositiveIntegerField()  # Aceitando apenas números positivos
    data_entrada = models.DateTimeField(auto_now_add=True)  # Data da entrada
    usuario_registrante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"Entrada: {self.product.product_name} - {self.quantidade}"

# Modelo de log de saidas no estoque
class SaidaEstoque(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    local = models.CharField(max_length=255)
    quantidade = models.PositiveIntegerField()
    responsavel = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True)
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.SET_NULL, null=True)
    observacao = models.TextField(blank=True, null=True)
    usuario_registrante = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    data_saida = models.DateTimeField(default=now)

    def __str__(self):
        return f"Saída de {self.quantidade} {self.product.product_name} do local {self.local}"

# Modelo de log de transferências entre locais
class TransferenciaEstoque(models.Model):
    produto = models.ForeignKey('suprimentos.Product', on_delete=models.CASCADE)
    local_saida = models.CharField(max_length=255)
    local_entrada = models.CharField(max_length=255)
    quantidade = models.PositiveIntegerField()
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    responsavel = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True)
    data_transferencia = models.DateTimeField(default=timezone.now)
    observacao = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.quantidade} de {self.produto} transferido de {self.local_saida} para {self.local_entrada}"

