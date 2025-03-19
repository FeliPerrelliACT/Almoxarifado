from django.conf import settings
from django.db import models

class PlanosFinanceiros(models.Model):
    finance_name = models.CharField(max_length=100)
    status = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.finance_name