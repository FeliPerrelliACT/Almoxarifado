from django.urls import path
from accounts import views

urlpatterns = [
    path('signup/', views.AccountCreateView.as_view(), name="signup"),
    path('<int:pk>/edit/', views.AccountUpdateView.as_view(), name="account_edit"),
    path('remover-imagem/<int:user_id>/', views.remover_imagem, name='remover_imagem'),
]
