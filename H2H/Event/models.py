from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.db.models import QuerySet
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from Location.models import Location


class SoftDeletionQuerySet(QuerySet):
    def delete(self):
        return super(SoftDeletionQuerySet, self).update(deleted_at=timezone.now())

    def hard_delete(self):
        return super(SoftDeletionQuerySet, self).delete()


class SoftDeletionManager(models.Manager):
    def __init__(self, *args, **kwargs):
        self.alive_only = kwargs.pop('alive_only', True)
        super(SoftDeletionManager, self).__init__(*args, **kwargs)

    def get_queryset(self):
        if self.alive_only:
            return SoftDeletionQuerySet(self.model).filter(deleted_at=None)
        return SoftDeletionQuerySet(self.model)

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class SoftDeletionModel(models.Model):
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SoftDeletionManager()
    all_objects = SoftDeletionManager(alive_only=False)

    class Meta:
        abstract = True

    def delete(self, **kwargs):
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self):
        super(SoftDeletionModel, self).delete()


class EventQuerySet(models.QuerySet):
    def near(self, other):
        all_locations = [e.location for e in self]
        sorted_events = []
        for location in all_locations:
            try:
                event = location.event
            except Location.event.RelatedObjectDoesNotExist:
                event = None
            if event:
                sorted_events.append((location.distance(other), event))
        sorted_events.sort(key=lambda d: d[0])  # sort by distance
        return [l[1] for l in sorted_events]


class EventManager(models.Manager):
    def get_queryset(self):
        return EventQuerySet(self.model, using=self._db)

    def near(self, other):
        return self.get_queryset().near(other)


class Event(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    start = models.DateTimeField()
    end = models.DateTimeField()

    organisation = models.ForeignKey('Organisation.Organisation', on_delete=models.CASCADE, blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.OneToOneField('Location.Location', on_delete=models.PROTECT, null=True)

    objects = EventManager()

    def save(self, *args, **kwargs):
        if self.end < self.start:
            raise Exception("End time before start time")
        self.full_clean()
        super(Event, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Job(SoftDeletionModel):
    name = models.CharField(max_length=200)
    description = models.TextField(null=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    total_positions = models.PositiveIntegerField(default=None, null=True, blank=True)

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


class RequiresSkill(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    skill = models.ForeignKey("User.Skill", on_delete=models.CASCADE)

    def __str__(self):
        return str(self.job) + " requires skill " + str(self.skill)


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
