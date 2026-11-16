from rest_framework import generics

from accounts.permissions import IsOrganization, IsVolunteer

from .models import AvailabilitySlot, OrganizationProfile, Skill, VolunteerProfile
from .serializers import (
    AvailabilitySlotSerializer,
    OrganizationProfileSerializer,
    SkillSerializer,
    VolunteerProfileSerializer,
)


class SkillListView(generics.ListAPIView):
    serializer_class = SkillSerializer
    queryset = Skill.objects.filter(is_active=True)
    pagination_class = None


class MyVolunteerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = VolunteerProfileSerializer
    permission_classes = [IsVolunteer]

    def get_object(self):
        profile, _ = VolunteerProfile.objects.get_or_create(user=self.request.user)
        return profile


class MyOrganizationProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = OrganizationProfileSerializer
    permission_classes = [IsOrganization]

    def get_object(self):
        profile, _ = OrganizationProfile.objects.get_or_create(user=self.request.user)
        return profile


class MyAvailabilityView(generics.ListCreateAPIView):
    serializer_class = AvailabilitySlotSerializer
    permission_classes = [IsVolunteer]
    pagination_class = None

    def get_volunteer(self):
        profile, _ = VolunteerProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_queryset(self):
        return AvailabilitySlot.objects.filter(volunteer=self.get_volunteer())

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "volunteer": self.get_volunteer()}

    def perform_create(self, serializer):
        serializer.save(volunteer=self.get_volunteer())


class MyAvailabilityDetailView(generics.DestroyAPIView):
    permission_classes = [IsVolunteer]

    def get_queryset(self):
        return AvailabilitySlot.objects.filter(volunteer__user=self.request.user)