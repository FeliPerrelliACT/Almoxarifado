from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Paginas
    path('', views.index, name='index'),
    path('admin-requests/', views.admin_requests, name='admin_requests'),
    path('solicitar/', views.request_create, name='solicitar'),
    path('compras/', views.all_requests, name='all_requests'),
    path('solicitante/', views.solicitante, name='solicitante'),

    # Produtos
    path('product/<int:product_id>/toggle_status/', views.toggle_product_status, name='toggle_product_status'),
    path('get_request_products/<int:request_id>/', views.get_request_products, name='get_request_products'),
    path('products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('produto/criar/', views.ProductCreateView.as_view(), name='produto_criar'),
    path('get-products/', views.get_products, name='get_products'),
    path('products/', views.product_list, name='product_list'),

    # Solicitações
    path('update-request-status/', views.update_request_status, name='update_request_status'),
    path('request/edit/<int:pk>/', views.RequestUpdateView.as_view(), name='edit_request'),
    
    # Mudar status
    path('request/avaluate/<int:request_id>/', views.request_to_evaluate, name='request_to_evaluate'),
    path("request/disapprove/<int:request_id>/", views.request_disapprove, name="request_disapprove"),
    path('request/revision/<int:request_id>/', views.request_revision, name='request_revision'),
    path('request/publish/<int:request_id>/', views.request_publish, name='request_publish'),
    path("request/approve/<int:request_id>/", views.request_approve, name="request_approve"),
    path("request/standby/<int:request_id>/", views.request_standby, name="request_standby"),
    path('request/delete/<int:request_id>/', views.request_delete, name='request_delete'),

    # Cotações
    path('get_quotations/<int:request_id>/', views.get_quotations, name='get_quotations'),
    path('quotations/<int:quotation_id>/', views.delete_quotation, name='delete_quotation'),
    path('upload_quotation/', views.upload_quotation, name='upload_quotation'),

    # centros de custo
    path('centros-custo/', views.listar_centros_custo, name='listar_centros_custo'),
    path('centros-custo/cadastrar/', views.cadastrar_centro_custo, name='cadastrar_centro_custo'),
    path('centros-custo/editar/<int:centro_id>/', views.editar_centro_custo, name='editar_centro_custo'),
    path('centros-custo/toggle-status/<int:centro_id>/', views.toggle_centro_custo_status, name='toggle_centro_custo_status'),

    # planos financeiros
    path('planos-financeiros/', views.listar_planos_financeiros, name='listar_planos_financeiros'),
    path('plano-financeiro/cadastrar/', views.cadastrar_plano_financeiro, name='cadastrar_plano_financeiro'),
    path('plano-financeiro/editar/<int:plano_id>/', views.editar_plano_financeiro, name='editar_plano_financeiro'),
    path('plano-financeiro/toggle-status/<int:plano_id>/', views.toggle_plano_financeiro_status, name='toggle_plano_financeiro_status'),

    # armazem
    path('armazem/', views.listar_armazens, name='listar_armazens'),
    path('armazem/cadastrar/', views.cadastrar_armazem, name='cadastrar_armazem'),
    path('armazem/editar/<int:armazem_id>/', views.editar_armazem, name='editar_armazem'),
    path('armazem/toggle-status/<int:armazem_id>/', views.toggle_armazem_status, name='toggle_armazem_status'),

    # funcionarios
    path('funcionarios/', views.listar_funcionarios, name='listar_funcionarios'),
    path('funcionario/cadastrar/', views.cadastrar_funcionario, name='cadastrar_funcionario'),
    path('funcionario/editar/<int:funcionario_id>/', views.editar_funcionario, name='editar_funcionario'),
    path('funcionario/toggle-status/<int:funcionario_id>/', views.toggle_funcionario_status, name='toggle_funcionario_status'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

