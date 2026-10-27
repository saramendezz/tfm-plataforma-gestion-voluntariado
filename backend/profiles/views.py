from rest_framework import generics

from accounts.permissions import IsOrganization, IsVolunteer

from .models import OrganizationProfile, Skill, VolunteerProfile
from .serializers import (
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