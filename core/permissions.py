"""
Права доступа на основе ролей FestivalParticipant.
"""
from rest_framework import permissions
from .models import FestivalParticipant


class IsOrganizerOrReadOnly(permissions.BasePermission):
    """Запись — только организаторам/модераторам. Чтение — всем."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return FestivalParticipant.objects.filter(
            user=request.user,
            role__in=['organizer', 'moderator'],
        ).exists()


class IsOwnerOrOrganizer(permissions.BasePermission):
    """Редактировать объект может только владелец или организатор."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        if getattr(obj, 'user_id', None) == request.user.id:
            return True
        return FestivalParticipant.objects.filter(
            user=request.user,
            role__in=['organizer', 'moderator'],
        ).exists()


class IsOrganizer(permissions.BasePermission):
    """Только организаторы/модераторы/суперпользователи."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return FestivalParticipant.objects.filter(
            user=request.user,
            role__in=['organizer', 'moderator'],
        ).exists()
class BookingPermission(permissions.BasePermission):
    """
    Чтение — всем (анонимным отдаём пустой список через queryset).
    Создание — только авторизованным.
    Редактирование — владельцу или организатору.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        if obj.user_id == request.user.id:
            return True
        return FestivalParticipant.objects.filter(
            user=request.user,
            role__in=['organizer', 'moderator'],
        ).exists()