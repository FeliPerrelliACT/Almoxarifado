from django.urls import path
from . import views

urlpatterns = [
    path('entrada/', views.entrada_estoque, name='entrada_estoque'),
    path('saida/', views.saida_estoque, name='saida_estoque'),
    path('lista/', views.lista_estoque, name='lista_estoque'),
    path('exportar/excel/', views.exportar_estoque_excel, name='exportar_estoque_excel'),
    path('exportar/pdf/', views.exportar_estoque_pdf, name='exportar_estoque_pdf'),
    path('get_produtos/<str:local>/', views.get_produtos_por_local, name='get_produtos_por_local'),

]


