from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


class Event(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    start = models.DateTimeField()
    end = models.DateTimeField()

    organisation = models.ForeignKey('Organisation.Organisation', on_delete=models.CASCADE, blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.OneToOneField('Location.Location', on_delete=models.PROTECT, null=True)

    def save(self, *args, **kwargs):
        if self.end < self.start:
            raise Exception("End time before start time")
        self.full_clean()
        super(Event, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Job(models.Model):
    class Meta:
        unique_together = ('name', 'event')

    name = models.CharField(max_length=200)
    description = models.TextField(null=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    total_positions = models.IntegerField(default=999)
    canceled = models.BooleanField(default=False)

    def occupied_positions(self):
        return self.participation_set.filter(state=4).count()

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

    class Meta:
        unique_together = ('user', 'job')

    job = models.ForeignKey(Job, on_delete=models.SET_NULL, blank=False, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    state = models.IntegerField(choices=PARTICIPATION_STATES, default=2)
    rating = models.ForeignKey('Feedback.Rating', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return str(self.user) + ' attends ' + str(self.job)


@receiver(post_delete, sender=Event)
def delete_location_for_event(sender, instance, *args, **kwargs):
    if instance.location:
        instance.location.delete()


@receiver(post_save, sender=Event)
def create_default_job_for_event(sender, instance, created, **kwargs):
    if created:
        Job.objects.create(name=instance.name, description=instance.description, event=instance)


@receiver(post_delete, sender=Job)
def set_participations_to_cancelled(sender, instance, *args, **kwargs):
    for participation in instance.participation_set.all():
        if participation.state in (2, 4):
            participation.state = 5
            participation.save()
