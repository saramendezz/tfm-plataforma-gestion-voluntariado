from django.db import models


class PostalCode(models.Model):
    code = models.CharField(max_length=5, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.code