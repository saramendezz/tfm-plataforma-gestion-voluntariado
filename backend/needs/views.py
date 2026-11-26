from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsVerifiedOrganization

from .models import Need
from .serializers import NeedSerializer


def with_confirmed(queryset):
    return queryset.annotate(
        confirmed_count=Count(
            "participations", filter=Q(participations__status="confirmed")
        )
    )


class NeedListCreateView(generics.ListCreateAPIView):
    serializer_class = NeedSerializer
    permission_classes = [IsVerifiedOrganization]

    def get_queryset(self):
        queryset = with_confirmed(
            Need.objects.filter(organization=self.request.user.organization_profile)
        )
        status = self.request.query_params.get("status")
        if status in Need.Status.values:
            queryset = queryset.filter(status=status)
        return queryset

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization_profile)


class NeedDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NeedSerializer
    permission_classes = [IsVerifiedOrganization]

    def get_queryset(self):
        return with_confirmed(
            Need.objects.filter(organization=self.request.user.organization_profile)
        )


class NeedCloseView(APIView):
    permission_classes = [IsVerifiedOrganization]

    def post(self, request, pk):
        need = get_object_or_404(
            Need, pk=pk, organization=request.user.organization_profile
        )
        need.status = Need.Status.CLOSED
        need.save(update_fields=["status", "updated_at"])
        return Response(NeedSerializer(need).data)