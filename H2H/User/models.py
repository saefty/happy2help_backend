from django.contrib.auth.models import User
from django.db import models

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birthday = models.DateField(blank=True, null=True)
    credit_points = models.PositiveIntegerField(default=0)

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

    class Meta:
        unique_together = ('skill', 'user')

    def __str__(self):
        return str(self.user) + ' has skill: ' + str(self.skill)


class Favourite(models.Model):
    event = models.ForeignKey('Event.Event', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user) + ' likes ' + str(self.event)


@receiver(post_save, sender=User)
def create_profile_on_user_create(sender, user, created, **kwargs):
    if created:
        Profile.objects.create(user=user)
