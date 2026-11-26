from rest_framework import serializers

from profiles.models import Skill

from .models import Need

LOCKED_FIELDS = ["start_at", "end_at", "municipality", "province", "postal_code"]
LOCKED_MESSAGE = "No se puede modificar mientras haya voluntarios que han aceptado."


class NeedSerializer(serializers.ModelSerializer):
    required_skills = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Skill.objects.filter(is_active=True),
        required=False,
    )
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    confirmed_count = serializers.SerializerMethodField()

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
            "confirmed_count",
            "organization_name",
            "created_at",
        ]
        read_only_fields = ["id", "status", "organization_name", "created_at"]

    def get_confirmed_count(self, obj):
        if hasattr(obj, "confirmed_count"):
            return obj.confirmed_count
        return obj.participations.filter(status="confirmed").count()

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

        if self.instance:
            confirmed = self.instance.participations.filter(status="confirmed").count()
            if confirmed:
                for name in LOCKED_FIELDS:
                    if name in attrs and attrs[name] != getattr(self.instance, name):
                        raise serializers.ValidationError({name: LOCKED_MESSAGE})
                if "required_skills" in attrs:
                    new = {s.id for s in attrs["required_skills"]}
                    current = set(
                        self.instance.required_skills.values_list("id", flat=True)
                    )
                    if new != current:
                        raise serializers.ValidationError(
                            {"required_skills": LOCKED_MESSAGE}
                        )
                needed = attrs.get("volunteers_needed", self.instance.volunteers_needed)
                if needed < confirmed:
                    raise serializers.ValidationError(
                        {
                            "volunteers_needed": "No puede ser menor que el número de "
                            "voluntarios que ya han aceptado."
                        }
                    )
        return attrs