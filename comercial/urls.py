from django.urls import path
from .views import toggle_centro_custo_status, lista_centros_custo, cadastro_centro_custo, editar_centro_custo, get_centros

urlpatterns = [
    path('cadastro_centro_custo/', cadastro_centro_custo, name='cadastro_centro_custo'),
    path('lista/', lista_centros_custo, name='lista_centros_custo'),
    path("toggle_status/<int:id>/", toggle_centro_custo_status, name="toggle_centro_custo_status"),
    path("editar/<int:id>/", editar_centro_custo, name="editar_centro_custo"),
    path('get_centros/', get_centros, name='get_centros'),
]
