from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    admin_requests, solicitante, request_create, all_requests,

    get_request_products, get_products, ProductCreateView,
    product_list, edit_product, toggle_product_status,

    update_request_status,RequestUpdateView,

    request_delete, request_publish, request_revision,
    request_approve, request_disapprove, request_standby,
    request_to_evaluate,

    upload_quotation, delete_quotation, get_quotations,


)

urlpatterns = [
    # Paginas
    path('admin-requests/', admin_requests, name='admin_requests'),
    path('solicitante/', solicitante, name='solicitante'),
    path('solicitar/', request_create, name='solicitar'),
    path('compras/', all_requests, name='all_requests'),

    # Produtos
    path('product/<int:product_id>/toggle_status/', toggle_product_status, name='toggle_product_status'),
    path('get_request_products/<int:request_id>/', get_request_products, name='get_request_products'),
    path('products/edit/<int:product_id>/', edit_product, name='edit_product'),
    path('produto/criar/', ProductCreateView.as_view(), name='produto_criar'),
    path('get-products/', get_products, name='get_products'),
    path('products/', product_list, name='product_list'),

    # Solicitações
    path('update-request-status/', update_request_status, name='update_request_status'),
    path('request/edit/<int:pk>/', RequestUpdateView.as_view(), name='edit_request'),
    
    # Mudar status
    path('request/avaluate/<int:request_id>/', request_to_evaluate, name='request_to_evaluate'),
    path("request/disapprove/<int:request_id>/", request_disapprove, name="request_disapprove"),
    path('request/revision/<int:request_id>/', request_revision, name='request_revision'),
    path('request/publish/<int:request_id>/', request_publish, name='request_publish'),
    path("request/approve/<int:request_id>/", request_approve, name="request_approve"),
    path("request/standby/<int:request_id>/", request_standby, name="request_standby"),
    path('request/delete/<int:request_id>/', request_delete, name='request_delete'),

    # Cotações
    path('get_quotations/<int:request_id>/', get_quotations, name='get_quotations'),
    path('quotations/<int:quotation_id>/', delete_quotation, name='delete_quotation'),
    path('upload_quotation/', upload_quotation, name='upload_quotation'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

