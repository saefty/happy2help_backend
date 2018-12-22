import geopy.distance
from django.db import models


# Create your models here.
class Location(models.Model):
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    def distance(self, other):
        own_loc = (self.latitude, self.longitude)
        other_loc = (other.latitude, other.longitude)
        return geopy.distance.vincenty(own_loc, other_loc).km