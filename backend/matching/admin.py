from django.contrib import admin

from .models import PostalCode


@admin.register(PostalCode)
class PostalCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "latitude", "longitude")
    search_fields = ("code",)