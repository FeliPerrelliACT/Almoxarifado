from django.urls import path
from django.conf.urls.static import static
from .views import (
criar_PlanosFinanceiros, listar_planos, editar_plano, toggle_plano_status,
)

urlpatterns = [
    path('planos/', listar_planos, name='lista_planos'),
    path('criar-plano/', criar_PlanosFinanceiros, name='criar_plano'),
    path("planos/editar/<int:id>/", editar_plano, name="editar_plano"),
    path("planos/toggle-status/<int:id>/", toggle_plano_status, name="toggle_plano_status"),
]


