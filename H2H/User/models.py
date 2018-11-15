from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.db.models.signals import post_delete
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birthday = models.DateField(blank=True, null=True)
    credit_points = models.IntegerField(default=0)

    def __str__(self):
        return str(self.user)


class Skill(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class HasSkill(models.Model):
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user) + ' has skill: ' + str(self.skill)


class Favourite(models.Model):
    event = models.ForeignKey('Event.Event', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user) + ' likes ' + str(self.event)


@receiver(post_delete, sender=Profile)
def post_delete_location_for_profile(sender, instance, *args, **kwargs):
    if instance.location:
        instance.location.delete()