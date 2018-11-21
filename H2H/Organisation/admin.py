from django.contrib import admin

# Register your models here.
from .models import Organisation


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    pass