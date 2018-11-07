from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import (
    Profile,
    Organisation,
    Event,
    Job,
    Participation,
    Rating,
    Favourite,
    Report,
    Location,
    Skill,
    HasSkill
)


# Define an inline admin descriptor for Profile model
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fields = ('birthday','location', 'credit_points')
    verbose_name_plural = 'profiles'


class SkillInline(admin.StackedInline):
    model = HasSkill
    can_delete = False
    fields = ('user', 'skill', 'approved')
    verbose_name_plural = 'has_skills'


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline, SkillInline,)


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    pass


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    pass


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    pass


@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    pass


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    pass


@admin.register(HasSkill)
class HasSkillAdmin(admin.ModelAdmin):
    pass


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    pass


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    pass


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    pass


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    pass


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    pass

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
