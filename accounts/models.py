from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    imagem = models.FileField(
        upload_to='images/user',
        default=None,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.username
