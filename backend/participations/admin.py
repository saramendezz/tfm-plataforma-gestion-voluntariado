from django.contrib import admin

from .models import Participation


@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    list_display = ("volunteer", "need", "status", "created_at", "ended_at")
    list_filter = ("status",)