from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

# Create your models here.
class Tenant(TenantMixin):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Domain(DomainMixin):
    pass
