from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.db.models.signals import post_delete
from django.dispatch import receiver


class Event(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    organisation = models.ForeignKey('Organisation.Organisation', on_delete=models.CASCADE, blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.OneToOneField('Location.Location', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name


class Job(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(null=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    total_positions = models.IntegerField(default=999)
    open_positions = models.IntegerField(default=999)
    canceled = models.BooleanField(default=False)

    def __str__(self):
        return str(self.name) + " at the event " + str(self.event)


class Participation(models.Model):
    PARTICIPATION_STATES = (
        (1, 'Participated'),
        (2, 'Applied'),
        (3, 'Declined'),
        (4, 'Accepted'),
        (5, 'Canceled'),
    )

    job = models.ForeignKey(Job, on_delete=models.SET_NULL, blank=False, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    state = models.IntegerField(choices=PARTICIPATION_STATES, default=2)
    rating = models.ForeignKey('Feedback.Rating', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return str(self.user) + ' attends ' + str(self.job)


@receiver(post_delete, sender=Event)
def post_delete_location_for_event(sender, instance, *args, **kwargs):
    if instance.location:
        instance.location.delete()