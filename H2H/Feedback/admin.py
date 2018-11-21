from django.contrib import admin

# Register your models here.
from .models import Rating, Report


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    pass


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    pass