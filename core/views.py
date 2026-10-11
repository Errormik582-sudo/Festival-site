"""Обработчики страниц и API."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .forms import RegisterForm
from .models import (
    Festival, Location, Event, InfoStand, Road, Camp, Booking,
    FestivalParticipant,
)
from .serializers import (
    FestivalSerializer, LocationSerializer, EventSerializer,
    InfoStandSerializer, RoadSerializer, CampSerializer,
    BookingSerializer, FestivalParticipantSerializer, UserSerializer,
    GroupSerializer,
)
from .permissions import (
    IsOrganizerOrReadOnly, IsOwnerOrOrganizer, IsOrganizer,BookingPermission,
)
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly,
)
from .models import (
    Festival, Location, Event, InfoStand, Road, Camp, Booking,
    FestivalParticipant, Group, GroupMember,
)


def get_active_festival():
    return Festival.objects.filter(is_active=True).first()


def is_organizer(user):
    """Проверка: организатор или модератор хотя бы на одном фестивале."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return FestivalParticipant.objects.filter(
        user=user, role__in=['organizer', 'moderator']
    ).exists()


# ---------- HTML-страницы ----------

@ensure_csrf_cookie
def index(request):
    return render(request, 'core/index.html', {
        'festival': get_active_festival(),
        'is_organizer': is_organizer(request.user),
    })


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})


def events_list(request):
    festival = get_active_festival()
    events = []
    if festival:
        events = (Event.objects
                  .filter(festival=festival)
                  .select_related('location')
                  .order_by('start_time'))
    return render(request, 'core/events.html', {
        'festival': festival, 'events': events,
    })


def location_detail(request, pk):
    location = get_object_or_404(Location, pk=pk)
    tabs = location.tabs.all()
    events = location.events.order_by('start_time')[:20]
    return render(request, 'core/location_detail.html', {
        'location': location, 'tabs': tabs, 'events': events,
    })


@login_required
@ensure_csrf_cookie
def booking_view(request):
    festival = get_active_festival()
    camps = Camp.objects.filter(festival=festival) if festival else Camp.objects.none()
    my_bookings = Booking.objects.filter(user=request.user).select_related('camp')
    return render(request, 'core/booking.html', {
        'festival': festival,
        'camps': camps,
        'my_bookings': my_bookings,
        'is_organizer': is_organizer(request.user),
    })

@login_required
@ensure_csrf_cookie
def groups_view(request):
    """Страница групп: создать, вступить, выйти."""
    festival = get_active_festival()
    camps = Camp.objects.filter(festival=festival) if festival else Camp.objects.none()
    return render(request, 'core/groups.html', {
        'festival': festival,
        'camps': camps,
        'is_organizer': is_organizer(request.user),
    })

@login_required
@ensure_csrf_cookie
def manage_view(request):
    if not is_organizer(request.user):
        return redirect('index')
    return render(request, 'core/manage.html', {
        'festival': get_active_festival(),
        'is_organizer': True,
    })


@login_required
@ensure_csrf_cookie
def users_view(request):
    """Страница управления пользователями. Только для организаторов."""
    if not is_organizer(request.user):
        return redirect('index')
    return render(request, 'core/users.html', {
        'festival': get_active_festival(),
        'is_organizer': True,
    })


# ---------- API ----------

class FestivalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Festival.objects.filter(is_active=True)
    serializer_class = FestivalSerializer
    permission_classes = [AllowAny]


class LocationViewSet(viewsets.ModelViewSet):
    """CRUD локаций. Писать — только организаторам."""
    serializer_class = LocationSerializer
    permission_classes = [IsOrganizerOrReadOnly]

    def get_queryset(self):
        qs = Location.objects.select_related('festival')
        # Обычные пользователи видят только активные. Организаторы — все.
        if not is_organizer(self.request.user):
            qs = qs.filter(is_active=True)
        festival_id = self.request.query_params.get('festival')
        if festival_id:
            qs = qs.filter(festival_id=festival_id)
        return qs


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsOrganizerOrReadOnly]

    def get_queryset(self):
        qs = Event.objects.select_related('festival', 'location')
        festival_id = self.request.query_params.get('festival')
        if festival_id:
            qs = qs.filter(festival_id=festival_id)
        return qs


class InfoStandViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InfoStandSerializer
    permission_classes = [IsOrganizerOrReadOnly]

    def get_queryset(self):
        qs = InfoStand.objects.filter(is_active=True).select_related('festival')
        festival_id = self.request.query_params.get('festival')
        if festival_id:
            qs = qs.filter(festival_id=festival_id)
        return qs


class RoadViewSet(viewsets.ModelViewSet):
    serializer_class = RoadSerializer
    permission_classes = [IsOrganizerOrReadOnly]

    def get_queryset(self):
        qs = Road.objects.all()
        festival_id = self.request.query_params.get('festival')
        if festival_id:
            qs = qs.filter(festival_id=festival_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CampViewSet(viewsets.ModelViewSet):
    serializer_class = CampSerializer
    permission_classes = [IsOrganizerOrReadOnly]

    def get_queryset(self):
        qs = Camp.objects.all()
        festival_id = self.request.query_params.get('festival')
        if festival_id:
            qs = qs.filter(festival_id=festival_id)
        return qs


class BookingViewSet(viewsets.ModelViewSet):
    """Бронирования территории."""
    serializer_class = BookingSerializer
    permission_classes = [BookingPermission]

    def get_queryset(self):
        qs = Booking.objects.select_related('user', 'camp', 'festival')
        # Анонимный пользователь — пустой список.
        if not self.request.user.is_authenticated:
            return Booking.objects.none()
        # Обычный пользователь — только свои брони. Организатор — все.
        if not is_organizer(self.request.user):
            qs = qs.filter(user=self.request.user)
        return qs

    # create / approve / reject / cancel — как было раньше.
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        props = request.data.get('properties', {}) or {}
        camp_id = props.get('camp') or request.data.get('camp')
        territory = serializer.validated_data.get('territory')

        if not camp_id or territory is None:
            return Response(
                {'error': 'Не указан лагерь или территория'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            camp = Camp.objects.get(pk=camp_id)
        except Camp.DoesNotExist:
            return Response(
                {'error': 'Лагерь не найден'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not camp.territory.contains(territory):
            return Response(
                {'error': 'Территория должна находиться внутри лагеря'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        overlap = Booking.objects.filter(
            camp=camp,
            status__in=['pending', 'confirmed'],
            territory__intersects=territory,
        ).exists()
        if overlap:
            return Response(
                {'error': 'Территория пересекается с существующей бронью'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save(user=request.user, festival=camp.festival, camp=camp)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsOrganizer])
    def approve(self, request, pk=None):
        booking = self.get_object()
        booking.status = 'confirmed'
        booking.reviewed_by = request.user
        booking.reviewed_at = timezone.now()
        booking.save()
        return Response({'status': 'confirmed'})

    @action(detail=True, methods=['post'], permission_classes=[IsOrganizer])
    def reject(self, request, pk=None):
        booking = self.get_object()
        booking.status = 'rejected'
        booking.reviewed_by = request.user
        booking.reviewed_at = timezone.now()
        booking.save()
        return Response({'status': 'rejected'})

    @action(detail=True, methods=['post'], permission_classes=[IsOrganizer])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        booking.status = 'cancelled'
        booking.save()
        return Response({'status': 'cancelled'})
    
class GroupViewSet(viewsets.ModelViewSet):
    """
    Группы участников.

    Создать может любой авторизованный. Создатель автоматически становится
    лидером и первым участником.
    Вступить в чужую группу может любой авторизованный.
    Редактировать/удалять — лидер, организатор или суперпользователь.
    """
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Group.objects.select_related('camp', 'leader', 'festival')
        festival_id = self.request.query_params.get('festival')
        if festival_id:
            qs = qs.filter(festival_id=festival_id)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def create(self, request, *args, **kwargs):
        """При создании группы лидер = текущий пользователь."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.save(leader=request.user)
        # Сразу добавляем создателя в участники.
        GroupMember.objects.get_or_create(group=group, user=request.user)
        return Response(
            self.get_serializer(group).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        """Удалять может только лидер или организатор."""
        group = self.get_object()
        if not (group.leader_id == request.user.id or is_organizer(request.user)):
            return Response(
                {'error': 'Нет прав на удаление группы'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Редактировать может только лидер или организатор."""
        group = self.get_object()
        if not (group.leader_id == request.user.id or is_organizer(request.user)):
            return Response(
                {'error': 'Нет прав на редактирование группы'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Вступить в группу."""
        group = self.get_object()
        if GroupMember.objects.filter(group=group, user=request.user).exists():
            return Response(
                {'error': 'Вы уже состоите в этой группе'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        GroupMember.objects.create(group=group, user=request.user)
        return Response({'status': 'joined'})

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Выйти из группы."""
        group = self.get_object()
        member = GroupMember.objects.filter(
            group=group, user=request.user
        ).first()
        if not member:
            return Response(
                {'error': 'Вы не состоите в этой группе'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Если лидер уходит — снимаем его с должности, но группу оставляем.
        if group.leader_id == request.user.id:
            group.leader = None
            group.save()
        member.delete()
        return Response({'status': 'left'})

    @action(detail=True, methods=['post'])
    def kick(self, request, pk=None):
        """Исключить участника — только лидер или организатор."""
        group = self.get_object()
        if not (group.leader_id == request.user.id or is_organizer(request.user)):
            return Response(
                {'error': 'Нет прав'},
                status=status.HTTP_403_FORBIDDEN,
            )
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'Не указан user_id'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Лидер не может исключить сам себя через kick — используйте leave.
        if str(user_id) == str(group.leader_id):
            return Response(
                {'error': 'Лидер не может исключить себя. Выйдите из группы.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        member = GroupMember.objects.filter(
            group=group, user_id=user_id
        ).first()
        if member:
            member.delete()
        return Response({'status': 'kicked'})    

class FestivalParticipantViewSet(viewsets.ModelViewSet):
    """Управление ролями на фестивале."""
    queryset = FestivalParticipant.objects.select_related('user', 'festival')
    serializer_class = FestivalParticipantSerializer
    permission_classes = [IsOrganizerOrReadOnly]


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Пользователи. Читать может только организатор.
    Даёт список для страницы управления ролями.
    """
    serializer_class = UserSerializer
    permission_classes = [IsOrganizer]

    def get_queryset(self):
        return User.objects.all().order_by('username')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['festival'] = get_active_festival()
        return ctx

    @action(detail=True, methods=['post'])
    def set_role(self, request, pk=None):
        """Установить роль пользователю на активном фестивале."""
        user = self.get_object()
        festival = get_active_festival()
        if not festival:
            return Response({'error': 'Нет активного фестиваля'},
                            status=status.HTTP_400_BAD_REQUEST)

        role = request.data.get('role')
        valid_roles = [r[0] for r in FestivalParticipant.ROLE_CHOICES]
        if role and role not in valid_roles:
            return Response({'error': 'Некорректная роль'},
                            status=status.HTTP_400_BAD_REQUEST)

        participant, _ = FestivalParticipant.objects.get_or_create(
            user=user, festival=festival,
            defaults={'role': role or 'participant'},
        )

        if role:
            participant.role = role
            participant.save()

        return Response(FestivalParticipantSerializer(participant).data)

    @action(detail=True, methods=['post'])
    def toggle_staff(self, request, pk=None):
        """Выдать/снять доступ в Django admin (is_staff)."""
        user = self.get_object()
        user.is_staff = not user.is_staff
        user.save()
        return Response({'is_staff': user.is_staff})