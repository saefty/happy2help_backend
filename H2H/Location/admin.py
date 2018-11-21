from django.contrib import admin

# Register your models here.
from .models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    pass