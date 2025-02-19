from .models import Request, Product, RequestProduct
from django.contrib import admin
from django import forms


# Formulário de Produto
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'unidade_medida', 'price', 'valor']


# Inline de RequestProduct para exibir os produtos associados a uma Request
class RequestProductInline(admin.TabularInline):
    model = RequestProduct
    extra = 1
    fields = ['product', 'quantity', 'total_price']
    readonly_fields = ['total_price']


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'request_text', 'pub_date', 'status', 'created_by', 'total_value')
    list_filter = ('pub_date', 'status')
    search_fields = ('request_text',)
    ordering = ('-pub_date',)
    readonly_fields = ('status', 'total_value')
    inlines = [RequestProductInline]

    def total_value(self, obj):
        # Certifique-se de que o related_name para RequestProduct no modelo Request é 'request_products'.
        # Se não for, ajuste para o nome correto, como por exemplo: obj.requestproduct_set.all()
        return sum(rp.total_price for rp in obj.request_products.all())
    total_value.short_description = 'Valor Total'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductForm  # Usa o formulário customizado para Product, se necessário
    list_display = ('product_name', 'unidade_medida', 'price', 'valor')
    search_fields = ('product_name',)
    ordering = ('product_name',)


@admin.register(RequestProduct)
class RequestProductAdmin(admin.ModelAdmin):
    list_display = ('request', 'product', 'quantity', 'total_price')
    list_filter = ('request', 'product')
