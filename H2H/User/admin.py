from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Profile, HasSkill, Skill, Favourite


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fields = ('birthday', 'location', 'credit_points')
    verbose_name_plural = 'profiles'


class SkillInline(admin.StackedInline):
    model = HasSkill
    can_delete = False
    fields = ('user', 'skill', 'approved')
    verbose_name_plural = 'has_skills'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline, SkillInline,)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    pass


@admin.register(HasSkill)
class HasSkillAdmin(admin.ModelAdmin):
    pass


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    pass


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    pass


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

