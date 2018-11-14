from django.db import models

# Create your models here.
class Location(models.Model):
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name