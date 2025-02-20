from .models import Request, Product, RequestProduct
from django.contrib import admin
from django import forms


# Formulário de Produto
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'unidade_medida']


# Inline de RequestProduct para exibir os produtos associados a uma Request
class RequestProductInline(admin.TabularInline):
    model = RequestProduct
    extra = 1
    fields = ['product', 'quantity']
    readonly_fields = []


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'request_text', 'pub_date', 'status', 'created_by')  
    list_filter = ('pub_date', 'status')
    search_fields = ('request_text',)
    ordering = ('-pub_date',)
    readonly_fields = ('status',)
    inlines = [RequestProductInline]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductForm  # Usa o formulário customizado para Product
    list_display = ('product_name', 'unidade_medida')
    ordering = ('product_name',)


@admin.register(RequestProduct)
class RequestProductAdmin(admin.ModelAdmin):
    list_display = ('request', 'product', 'quantity')
    list_filter = ('request', 'product')
