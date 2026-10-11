"""Регистрация всех моделей в админке."""
from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.utils import timezone
from .models import (
    Festival, Profile, FestivalParticipant, Location, LocationTab,
    Event, InfoStand, Road, Camp, Group, GroupMember, Booking,
)


@admin.register(Festival)
class FestivalAdmin(GISModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')


@admin.register(FestivalParticipant)
class FestivalParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'festival', 'role', 'created_at')
    list_filter = ('festival', 'role')
    search_fields = ('user__username',)


class LocationTabInline(admin.TabularInline):
    model = LocationTab
    extra = 1


@admin.register(Location)
class LocationAdmin(GISModelAdmin):
    list_display = ('name', 'festival', 'location_type', 'priority', 'is_active')
    list_filter = ('festival', 'location_type', 'priority', 'is_active')
    search_fields = ('name',)
    inlines = [LocationTabInline]


@admin.register(Event)
class EventAdmin(GISModelAdmin):
    list_display = ('title', 'festival', 'location', 'start_time', 'status')
    list_filter = ('festival', 'status')
    search_fields = ('title',)


@admin.register(InfoStand)
class InfoStandAdmin(GISModelAdmin):
    list_display = ('title', 'festival', 'priority',
                    'valid_from', 'valid_until', 'is_active')
    list_filter = ('festival', 'is_active', 'priority')


@admin.register(Road)
class RoadAdmin(GISModelAdmin):
    list_display = ('name', 'festival', 'road_type', 'created_by', 'created_at')
    list_filter = ('festival', 'road_type')


@admin.register(Camp)
class CampAdmin(GISModelAdmin):
    list_display = ('name', 'festival', 'camp_type', 'capacity')
    list_filter = ('festival', 'camp_type')


class GroupMemberInline(admin.TabularInline):
    model = GroupMember
    extra = 1


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'festival', 'camp', 'leader')
    list_filter = ('festival',)
    inlines = [GroupMemberInline]


@admin.register(Booking)
class BookingAdmin(GISModelAdmin):
    list_display = ('id', 'user', 'camp', 'status', 'created_at', 'reviewed_by')
    list_filter = ('status', 'camp', 'festival')
    search_fields = ('user__username', 'notes')
    readonly_fields = ('created_at', 'reviewed_at')

    actions = ['approve_selected', 'reject_selected']

    @admin.action(description='Подтвердить выбранные')
    def approve_selected(self, request, queryset):
        queryset.update(
            status='confirmed',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )

    @admin.action(description='Отклонить выбранные')
    def reject_selected(self, request, queryset):
        queryset.update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )