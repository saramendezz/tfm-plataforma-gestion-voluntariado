from django.contrib import admin

from .models import Participation


@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Participation._meta.fields]
    list_filter = ["status"]
    list_per_page = 50