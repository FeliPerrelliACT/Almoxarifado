from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ADMIN = 'admin'
    COMPRADOR = 'comprador'
    USER_TYPE_CHOICES = [
        (ADMIN, 'Administrador'),
        (COMPRADOR, 'Comprador'),
    ]

    type_user = models.CharField(
        'Tipo de Usuário',
        max_length=50,
        choices=USER_TYPE_CHOICES,
        default=COMPRADOR,
    )
    imagem = models.FileField(
        upload_to='images/user',
        default=None,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.username} ({self.type_user})"
