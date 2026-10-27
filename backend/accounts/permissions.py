from rest_framework.permissions import BasePermission

from .models import User


class HasRole(BasePermission):
    role = None

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == self.role)


class IsVolunteer(HasRole):
    role = User.Role.VOLUNTEER


class IsOrganization(HasRole):
    role = User.Role.ORGANIZATION


class IsAdminRole(HasRole):
    role = User.Role.ADMIN