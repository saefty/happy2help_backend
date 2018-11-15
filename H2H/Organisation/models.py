from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class Organisation(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creator')
    members = models.ManyToManyField(User)

    def __str__(self):
        return self.name