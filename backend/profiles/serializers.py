from rest_framework import serializers

from .models import AvailabilitySlot, OrganizationProfile, Skill, VolunteerProfile


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


class AvailabilitySlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilitySlot
        fields = ["id", "start_at", "end_at"]

    def validate(self, attrs):
        start, end = attrs["start_at"], attrs["end_at"]
        if end <= start:
            raise serializers.ValidationError(
                {"end_at": "La fecha de fin debe ser posterior a la de inicio."}
            )
        overlaps = AvailabilitySlot.objects.filter(
            volunteer=self.context["volunteer"], start_at__lt=end, end_at__gt=start
        )
        if overlaps.exists():
            raise serializers.ValidationError(
                "La franja se solapa con otra que ya has indicado."
            )
        return attrs