from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    index, all_requests, request_create, get_request_products, upload_request_files,
    request_delete, request_revisao, add_comment, solicitante, ProductCreateView,
    RequestUpdateView, add_quotation, delete_quotation, request_to_evaluate,
    get_products, update_request_status, request_publish, admin_requests,
    request_approve, request_disapprove, request_standby, add_quotation,
)

urlpatterns = [
    # Rota principal do solicitante
    path('compras/', all_requests, name='all_requests'),
    path('solicitante/', solicitante, name='solicitante'),
    path('solicitar/', request_create, name='solicitar'),
    path('admin-requests/', admin_requests, name='admin_requests'),

    # Rotas para produtos
    path('produto/criar/', ProductCreateView.as_view(), name='produto_criar'),
    path('get-products/', get_products, name='get_products'),

    # Rotas para solicitações
    path('get_request_products/<int:request_id>/', get_request_products, name='get_request_products'),
    path('update-request-status/', update_request_status, name='update_request_status'),
    path('request/publish/<int:request_id>/', request_publish, name='request_publish'),
    path('request/delete/<int:request_id>/', request_delete, name='request_delete'),
    path('request/edit/<int:pk>/', RequestUpdateView.as_view(), name='edit_request'),
    path('request/revisao/<int:request_id>/', request_revisao, name='request_revisao'),
    path('request/<int:request_id>/add_comment/', add_comment, name='add_comment'),
    path('solicitacao/<int:request_id>/avaliar/', request_to_evaluate, name='request_to_evaluate'),
    
    path("request/approve/<int:request_id>/", request_approve, name="request_approve"),
    path("request/disapprove/<int:request_id>/", request_disapprove, name="request_disapprove"),
    path("request/standby/<int:request_id>/", request_standby, name="request_standby"),
    path('add-quotation/', add_quotation, name='add_quotation'),

    # Rotas de arquivos
    path('upload-files/', upload_request_files, name='upload_request_files'),
    path('delete_quotation/<int:quotation_id>/', delete_quotation, name='delete_quotation'),

    # Página inicial
    path('', index, name='index'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)