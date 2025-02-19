from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ADMIN = 'admin'
    suprimentos = 'suprimentos'
    FINANCEIRO = 'financeiro'
    USER_TYPE_CHOICES = [
        (ADMIN, 'Administrador'),
        (suprimentos, 'suprimentos'),
        (FINANCEIRO, 'Financeiro'),
    ]

    type_user = models.CharField(
        'Tipo de Usuário',
        max_length=50,
        choices=USER_TYPE_CHOICES,
        default=suprimentos,
    )
    imagem = models.FileField(
        upload_to='images/user',
        default=None,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.username} ({self.type_user})"
