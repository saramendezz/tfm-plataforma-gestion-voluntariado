from rest_framework import serializers

from profiles.models import Skill

from .models import Need


class NeedSerializer(serializers.ModelSerializer):
    required_skills = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Skill.objects.filter(is_active=True),
        required=False,
    )
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )

    class Meta:
        model = Need
        fields = [
            "id",
            "title",
            "description",
            "required_skills",
            "municipality",
            "province",
            "postal_code",
            "start_at",
            "end_at",
            "volunteers_needed",
            "status",
            "organization_name",
            "created_at",
        ]
        read_only_fields = ["id", "status", "organization_name", "created_at"]

    def validate(self, attrs):
        if self.instance and self.instance.status == Need.Status.CLOSED:
            raise serializers.ValidationError(
                "No se puede modificar una necesidad cerrada."
            )
        start = attrs.get("start_at", getattr(self.instance, "start_at", None))
        end = attrs.get("end_at", getattr(self.instance, "end_at", None))
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end_at": "La fecha de fin debe ser posterior a la de inicio."}
            )
        return attrs