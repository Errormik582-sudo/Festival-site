"""
Сериализаторы: модель → GeoJSON / JSON.
"""
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import (
    Festival, Location, Event, InfoStand, Road, Camp,
    Booking, FestivalParticipant, Group, GroupMember,
)

class FestivalSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Festival
        geo_field = 'map_center'
        fields = ('id', 'name', 'description', 'map_zoom',
                  'start_date', 'end_date', 'is_active')


class LocationSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Location
        geo_field = 'geo_point'
        fields = ('id', 'name', 'description', 'location_type',
                  'priority', 'capacity', 'festival', 'is_active')


class EventSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Event
        geo_field = 'geo_point'
        fields = ('id', 'title', 'description', 'start_time',
                  'end_time', 'status', 'festival', 'location')


class InfoStandSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = InfoStand
        geo_field = 'geo_point'
        fields = ('id', 'title', 'content', 'priority',
                  'valid_from', 'valid_until', 'is_active', 'festival')


class RoadSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Road
        geo_field = 'path'
        fields = ('id', 'name', 'road_type', 'festival', 'created_at')
        read_only_fields = ('created_at',)


class CampSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Camp
        geo_field = 'territory'
        fields = ('id', 'name', 'description', 'camp_type',
                  'capacity', 'festival')


class BookingSerializer(GeoFeatureModelSerializer):
    """Бронирование → GeoJSON."""
    class Meta:
        model = Booking
        geo_field = 'territory'
        fields = ('id', 'user', 'camp', 'festival', 'status',
                  'notes', 'created_at', 'reviewed_by', 'reviewed_at')
        read_only_fields = ('user', 'status', 'reviewed_by',
                            'reviewed_at', 'created_at')


class FestivalParticipantSerializer(serializers.ModelSerializer):
    """Роль пользователя на фестивале."""
    user_username = serializers.CharField(source='user.username', read_only=True)
    festival_name = serializers.CharField(source='festival.name', read_only=True)

    class Meta:
        model = FestivalParticipant
        fields = ('id', 'user', 'user_username', 'festival', 'festival_name',
                  'role', 'created_at')
        read_only_fields = ('created_at',)


class UserSerializer(serializers.ModelSerializer):
    """Пользователь + его роль на активном фестивале."""
    role = serializers.SerializerMethodField()
    role_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'is_staff', 'is_superuser', 'is_active',
                  'role', 'role_id')

    def get_role(self, obj):
        """Роль на активном фестивале, если он есть."""
        festival = self.context.get('festival')
        if not festival:
            return None
        p = obj.festival_roles.filter(festival=festival).first()
        return p.role if p else None

    def get_role_id(self, obj):
        festival = self.context.get('festival')
        if not festival:
            return None
        p = obj.festival_roles.filter(festival=festival).first()
        return p.id if p else None
    from .models import Group, GroupMember


class GroupMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = GroupMember
        fields = ('id', 'user', 'username', 'joined_at')
        read_only_fields = ('joined_at', 'user')


class GroupSerializer(serializers.ModelSerializer):
    leader_username = serializers.CharField(
        source='leader.username', read_only=True
    )
    camp_name = serializers.CharField(source='camp.name', read_only=True)
    members = GroupMemberSerializer(many=True, read_only=True)
    members_count = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ('id', 'name', 'festival', 'camp', 'camp_name',
                  'leader', 'leader_username', 'description',
                  'members', 'members_count', 'is_member')
        read_only_fields = ('leader',)

    def get_members_count(self, obj):
        return obj.members.count()

    def get_is_member(self, obj):
        """Состоит ли текущий пользователь в этой группе."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.members.filter(user=request.user).exists()