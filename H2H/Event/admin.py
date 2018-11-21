from django.contrib import admin

# Register your models here.
from .models import Event, Job, Participation


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    pass


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    pass


@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    pass