import cloudinary
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

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


@receiver(post_delete, sender=Image)
def delete_cloud_image(sender, instance, *args, **kwargs):
    cloudinary.uploader.destroy(instance.public_id)
