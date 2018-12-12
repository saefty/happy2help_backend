from django.contrib.auth.models import User
from django.db import models

from Organisation.models import Organisation
from Event.models import Event

class Image(models.Model):
    public_id = models.TextField()
    url = models.TextField() 

    organisation = models.OneToOneField(Organisation, on_delete=models.CASCADE, blank=True, null=True)
    event = models.OneToOneField(Event, on_delete=models.CASCADE, blank=True, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.public_id
