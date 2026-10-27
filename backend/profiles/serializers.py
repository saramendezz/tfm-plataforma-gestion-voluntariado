from rest_framework import serializers

from .models import OrganizationProfile, Skill, VolunteerProfile


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name", "category"]


class VolunteerProfileSerializer(serializers.ModelSerializer):
    skills = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Skill.objects.filter(is_active=True),
        required=False,
    )

    class Meta:
        model = VolunteerProfile
        fields = [
            "municipality",
            "province",
            "postal_code",
            "phone",
            "skills",
            "max_distance_km",
            "is_available",
        ]


class OrganizationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationProfile
        fields = [
            "name",
            "description",
            "phone",
            "municipality",
            "province",
            "postal_code",
            "is_verified",
        ]
        read_only_fields = ["is_verified"]