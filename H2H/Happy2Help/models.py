from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
# Create your models here.


class Organisation(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    member = models.ManyToManyField(User)

    def __str__(self):
        return self.name






class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birthday = models.DateField(blank=True, null=True)
    creditPoints = models.IntegerField(default=0)


    def __str__(self):
        return str(self.user)


class Event(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, blank=True, null=True) # es gibt immer einen creator aber nicht immer eine organisation
    creator = models.ForeignKey(User, on_delete=models.CASCADE) # wird doch gebraucht weil ein user ohne orga auch erstellen kann!


    def __str__(self):
        return self.name


class Job(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(null=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    total_positions = models.IntegerField(default=999)
    open_positions = models.IntegerField(default=999)
    canceled = models.BooleanField(default=0)


    def __str__(self):
        return str(self.name) + " at the event " + str(self.event)


class Rating(models.Model):
    user_a = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='rating_from_user')
    orga_a = models.ForeignKey(Organisation, on_delete=models.CASCADE, blank=True, null=True, related_name='rating_from_orga')

    user_b = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='rating_to_user')
    orga_b = models.ForeignKey(Organisation, on_delete=models.CASCADE, blank=True, null=True, related_name='rating_to_orga')

    rating = models.FloatField(default=0.0)

    def __str__(self):
        return str(self.rating)


class Participation(models.Model):
    #event = models.ForeignKey(Event, on_delete=models.SET_NULL, blank=False, null=True) # partip nicht löschen wenn event gelöscht wird. etwas besseres als NULL wär gut...
    PARTICIPATION_STATES = (
        (1, 'Participated'),
        (2, 'Applied'),
        (3, 'Declined'),
        (4, 'Accepted'),
        (5, 'Canceled'),
    )

    job = models.ForeignKey(Job, on_delete=models.SET_NULL, blank=False, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE) # wenn user gelöscht, dann ist particip auch weg
    rating = models.ForeignKey(Rating, on_delete=models.SET_NULL, blank=True, null=True)
    state = models.IntegerField(choices=PARTICIPATION_STATES, default=2)


    

    def __str__(self):
        return str(self.user) + ' attends ' + str(self.job)


class Favourite(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user) + ' likes ' + str(self.event)


class Report(models.Model):
    REASON_CHOICES = (
        ('--', 'None'),
        ('AB', 'Abuse'),
        ('HA', 'Hate'),
    )

    user_a = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='report_from_user')
    orga_a = models.ForeignKey(Organisation, on_delete=models.CASCADE, blank=True, null=True, related_name='report_from_orga')

    user_b = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='report_to_user')
    orga_b = models.ForeignKey(Organisation, on_delete=models.CASCADE, blank=True, null=True, related_name='report_to_orga')

    text = models.TextField()
    reason = models.CharField(max_length=2, choices=REASON_CHOICES, default='--')

    def __str__(self):
        return self.reason



