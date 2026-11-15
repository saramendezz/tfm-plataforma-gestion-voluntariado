from django.contrib import admin

from .models import Need


@admin.register(Need)
class NeedAdmin(admin.ModelAdmin):
    list_display = ("title", "organization", "status", "start_at", "volunteers_needed")
    list_filter = ("status", "province")
    filter_horizontal = ("required_skills",)