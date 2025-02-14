from django.urls import path
from Accounts import views

urlpatterns = [
    path(
        'signup/',
        views.AccountCreateView.as_view(),
        name="signup"
    ),
    path(
        '<int:pk>/edit/',
        views.AccountUpdateView.as_view(),
        name="account_edit"
    ),
]
