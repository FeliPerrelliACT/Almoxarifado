from .views import index, verificar_grupos
from django.urls import path


urlpatterns = [
    path('', index, name='index'),
    path('verificar-grupos/', verificar_grupos, name='verificar_grupos'),
    
]
