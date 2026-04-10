import uuid

from django.db import models

# Create your models here.

class BaseModels(models.Model):
    id = models.UUIDField(unique=True,primary_key=True,default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True