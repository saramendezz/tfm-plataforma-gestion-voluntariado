from django.contrib import admin

from .models import OrganizationProfile, Skill, VolunteerProfile


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name",)


@admin.register(VolunteerProfile)
class VolunteerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "municipality", "province", "is_available")
    list_filter = ("province", "is_available")
    filter_horizontal = ("skills",)


@admin.register(OrganizationProfile)
class OrganizationProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "municipality", "province", "is_verified")
    list_filter = ("is_verified", "province")