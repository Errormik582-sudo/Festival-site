"""Наполнение БД тестовыми данными."""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import sqlite_patch  # noqa: E402, F401

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'festival_map.settings')

import django  # noqa: E402
django.setup()

from datetime import timedelta  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402
from django.contrib.gis.geos import Point, LineString, Polygon  # noqa: E402
from django.utils import timezone  # noqa: E402
from core.models import (  # noqa: E402
    Festival, Profile, FestivalParticipant, Location, LocationTab,
    Event, InfoStand, Road, Camp, Group, GroupMember,
)


def run():
    # 1. Суперпользователь.
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            'admin', 'admin@example.com', 'admin123'
        )
        admin.is_staff = True
        admin.save()
        Profile.objects.create(user=admin, phone='+7-000-000-00-00')
        print('[seed] Создан admin / admin123')
    else:
        admin = User.objects.get(username='admin')

    # 2. Фестиваль.
    festival, created = Festival.objects.get_or_create(
        name='Былинный берег',
        defaults={
            'description': 'Фестиваль исторической реконструкции',
            'map_center': Point(31.538780, 58.764184, srid=4326),
            'map_zoom': 14,
            'is_active': True,
        }
    )
    if created:
        print('[seed] Создан фестиваль «Былинный берег»')

    # 3. Роль admin — организатор.
    FestivalParticipant.objects.get_or_create(
        user=admin, festival=festival,
        defaults={'role': 'organizer'}
    )

    # 4. Участники.
    participants = []
    for username in ['ivan', 'petr', 'maria']:
        u, created = User.objects.get_or_create(
            username=username,
            defaults={'email': f'{username}@example.com'}
        )
        if created:
            u.set_password('test1234')
            u.save()
            Profile.objects.create(user=u)
            print(f'[seed] Создан пользователь {username} / test1234')
        FestivalParticipant.objects.get_or_create(
            user=u, festival=festival,
            defaults={'role': 'participant'}
        )
        participants.append(u)

    # 5. Локации — все типы.
    locations_data = [
        ('Главная сцена', 'stage', 31.5390, 58.7645, 3),
        ('Полевая кухня', 'food', 31.5380, 58.7640, 2),
        ('Медпункт', 'medical', 31.5375, 58.7638, 3),
        ('Инфоцентр', 'info', 31.5385, 58.7642, 2),
        ('Туалет (северный)', 'toilet', 31.5395, 58.7648, 2),
        ('Туалет (южный)', 'toilet', 31.5378, 58.7635, 2),
        ('Душевые', 'shower', 31.5388, 58.7637, 2),
        ('Ярмарка', 'market', 31.5398, 58.7643, 2),
        ('Ристалище', 'tournament', 31.5405, 58.7650, 3),
        ('Гостиничный лагерь', 'hotel_camp', 31.5365, 58.7655, 2),
        ('Лагерь организаторов', 'organizers_camp', 31.5372, 58.7648, 3),
    ]
    locations = {}
    for name, loc_type, lon, lat, priority in locations_data:
        loc, created = Location.objects.get_or_create(
            festival=festival, name=name,
            defaults={
                'geo_point': Point(lon, lat, srid=4326),
                'location_type': loc_type,
                'priority': priority,
            }
        )
        if created:
            LocationTab.objects.create(
                location=loc, tab_name='Описание',
                content=f'Информация о точке «{name}».', sort_order=1,
            )
            print(f'[seed] Локация: {name}')
        locations[name] = loc

    # 6. Мероприятие.
    now = timezone.now()
    stage = locations['Главная сцена']
    Event.objects.get_or_create(
        festival=festival, title='Открытие фестиваля',
        defaults={
            'location': stage,
            'description': 'Торжественное открытие',
            'start_time': now + timedelta(hours=1),
            'end_time': now + timedelta(hours=2),
            'status': 'scheduled',
            'geo_point': stage.geo_point,
        }
    )
    print('[seed] Мероприятие: Открытие фестиваля')

    # 7. Инфостенд.
    InfoStand.objects.get_or_create(
        festival=festival, title='Расписание на сегодня',
        defaults={
            'content': {'text': 'Смотрите программу на инфоцентре.'},
            'geo_point': locations['Инфоцентр'].geo_point,
            'valid_from': now,
            'valid_until': now + timedelta(days=3),
            'priority': 10,
        }
    )
    print('[seed] Инфостенд: Расписание')

    # 8. Лагерь участников.
    camp_polygon = Polygon((
        (31.5380, 58.7640),
        (31.5400, 58.7640),
        (31.5400, 58.7650),
        (31.5380, 58.7650),
        (31.5380, 58.7640),
    ), srid=4326)
    camp, created = Camp.objects.get_or_create(
        festival=festival, name='Лагерь участников',
        defaults={
            'territory': camp_polygon,
            'camp_type': 'participants',
            'capacity': 100,
        }
    )
    if created:
        print('[seed] Лагерь: Лагерь участников')

    # 9. Дорога.
    road_path = LineString(
        (31.5370, 58.7630),
        (31.5380, 58.7640),
        (31.5390, 58.7645),
        srid=4326,
    )
    Road.objects.get_or_create(
        festival=festival, name='Главная дорога',
        defaults={
            'path': road_path,
            'road_type': 'main',
            'created_by': admin,
        }
    )
    print('[seed] Дорога: Главная')

    # 10. Группа.
    group, created = Group.objects.get_or_create(
        festival=festival, name='Дружина',
        defaults={
            'camp': camp,
            'leader': participants[0],
            'description': 'Первая дружина фестиваля',
        }
    )
    for u in participants:
        GroupMember.objects.get_or_create(group=group, user=u)
    print('[seed] Группа: Дружина (3 участника)')

    print('[seed] Готово.')


if __name__ == '__main__':
    run()