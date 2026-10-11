"""Модели фестиваля «Былинный берег»."""
from django.contrib.auth.models import User
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.urls import reverse


class Festival(models.Model):
    """Фестиваль — корень всей структуры."""
    name = models.CharField('Название', max_length=255)
    description = models.TextField('Описание', blank=True)
    start_date = models.DateField('Дата начала', null=True, blank=True)
    end_date = models.DateField('Дата окончания', null=True, blank=True)
    map_center = gis_models.PointField(
        'Центр карты', srid=4326,
        default='POINT(31.538780 58.764184)'
    )
    map_zoom = models.IntegerField('Зум по умолчанию', default=14)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        db_table = 'festival'
        verbose_name = 'Фестиваль'
        verbose_name_plural = 'Фестивали'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('index')


class Profile(models.Model):
    """Доп. данные к User."""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    phone = models.CharField('Телефон', max_length=20, blank=True)
    bio = models.TextField('О себе', blank=True)

    class Meta:
        db_table = 'profile'
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'Профиль {self.user.username}'


class FestivalParticipant(models.Model):
    """Роль пользователя на конкретном фестивале."""
    ROLE_CHOICES = [
        ('organizer', 'Организатор'),
        ('moderator', 'Модератор'),
        ('volunteer', 'Волонтёр'),
        ('participant', 'Участник'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='festival_roles'
    )
    festival = models.ForeignKey(
        Festival, on_delete=models.CASCADE, related_name='participants'
    )
    role = models.CharField(
        'Роль', max_length=20, choices=ROLE_CHOICES, default='participant'
    )
    created_at = models.DateTimeField('Добавлен', auto_now_add=True)

    class Meta:
        db_table = 'festival_participant'
        verbose_name = 'Участник фестиваля'
        verbose_name_plural = 'Участники фестиваля'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'festival'],
                name='unique_user_festival'
            )
        ]

    def __str__(self):
        return f'{self.user.username} — {self.get_role_display()}'


class Location(models.Model):
    """Точка интереса (POI) на карте."""
    LOCATION_TYPES = [
        ('stage', 'Сцена'),
        ('food', 'Еда'),
        ('medical', 'Медицина'),
        ('toilet', 'Туалет'),
        ('shower', 'Душ'),
        ('info', 'Информация'),
        ('market', 'Ярмарка'),
        ('tournament', 'Ристалище'),
        ('camp', 'Лагерь'),
        ('hotel_camp', 'Гостиничный лагерь'),
        ('organizers_camp', 'Лагерь организаторов'),
        ('other', 'Другое'),
    ]
    PRIORITY_CHOICES = [
        (1, 'Низкое'),
        (2, 'Обычное'),
        (3, 'Высокое'),
    ]

    festival = models.ForeignKey(
        Festival, on_delete=models.CASCADE, related_name='locations'
    )
    name = models.CharField('Название', max_length=255)
    description = models.TextField('Описание', blank=True)
    geo_point = gis_models.PointField('Координаты', srid=4326)
    location_type = models.CharField(
        'Тип', max_length=20, choices=LOCATION_TYPES, default='other'
    )
    priority = models.IntegerField(
        'Значение места', choices=PRIORITY_CHOICES, default=2
    )
    capacity = models.IntegerField('Вместимость', null=True, blank=True)
    is_active = models.BooleanField('Активна', default=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    class Meta:
        db_table = 'location'
        verbose_name = 'Локация'
        verbose_name_plural = 'Локации'

    def __str__(self):
        return f'{self.name} ({self.get_location_type_display()})'

    def get_absolute_url(self):
        return reverse('location_detail', args=[self.pk])


class LocationTab(models.Model):
    """Вкладка внутри карточки локации."""
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name='tabs'
    )
    tab_name = models.CharField('Название вкладки', max_length=100)
    content = models.TextField('Содержимое', blank=True)
    sort_order = models.IntegerField('Порядок', default=0)

    class Meta:
        db_table = 'location_tab'
        verbose_name = 'Вкладка локации'
        verbose_name_plural = 'Вкладки локаций'
        ordering = ['sort_order']

    def __str__(self):
        return f'{self.location.name} — {self.tab_name}'


class Event(models.Model):
    """Мероприятие."""
    STATUS_CHOICES = [
        ('scheduled', 'Запланировано'),
        ('ongoing', 'Идёт'),
        ('cancelled', 'Отменено'),
        ('ended', 'Завершено'),
    ]

    festival = models.ForeignKey(
        Festival, on_delete=models.CASCADE, related_name='events'
    )
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='events'
    )
    title = models.CharField('Название', max_length=255)
    description = models.TextField('Описание', blank=True)
    start_time = models.DateTimeField('Начало')
    end_time = models.DateTimeField('Окончание', null=True, blank=True)
    status = models.CharField(
        'Статус', max_length=20, choices=STATUS_CHOICES, default='scheduled'
    )
    geo_point = gis_models.PointField(
        'Координаты на карте', srid=4326, null=True, blank=True
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        db_table = 'event'
        verbose_name = 'Мероприятие'
        verbose_name_plural = 'Мероприятия'
        ordering = ['start_time']

    def __str__(self):
        return f'{self.title} ({self.start_time:%d.%m %H:%M})'


class InfoStand(models.Model):
    """Инфостенд — временный информационный блок."""
    festival = models.ForeignKey(
        Festival, on_delete=models.CASCADE, related_name='infostands'
    )
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='infostands'
    )
    title = models.CharField('Заголовок', max_length=255)
    content = models.JSONField('Содержимое', default=dict)
    geo_point = gis_models.PointField(
        'Координаты', srid=4326, null=True, blank=True
    )
    valid_from = models.DateTimeField('Актуален с', null=True, blank=True)
    valid_until = models.DateTimeField('Актуален до', null=True, blank=True)
    priority = models.IntegerField('Приоритет', default=0)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        db_table = 'info_stand'
        verbose_name = 'Инфостенд'
        verbose_name_plural = 'Инфостенды'
        ordering = ['-priority', '-valid_from']

    def __str__(self):
        return self.title


class Road(models.Model):
    """Дорога — линия на карте."""
    ROAD_TYPES = [
        ('main', 'Основная'),
        ('secondary', 'Второстепенная'),
    ]

    festival = models.ForeignKey(
        Festival, on_delete=models.CASCADE, related_name='roads'
    )
    name = models.CharField('Название', max_length=255, blank=True)
    path = gis_models.LineStringField('Маршрут', srid=4326)
    road_type = models.CharField(
        'Тип', max_length=20, choices=ROAD_TYPES, default='main'
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_roads'
    )
    created_at = models.DateTimeField('Создана', auto_now_add=True)

    class Meta:
        db_table = 'road'
        verbose_name = 'Дорога'
        verbose_name_plural = 'Дороги'

    def __str__(self):
        return self.name or f'Дорога #{self.pk}'


class Camp(models.Model):
    """Территория лагеря — полигон на карте."""
    CAMP_TYPES = [
        ('general', 'Общий'),
        ('participants', 'Участники'),
        ('volunteers', 'Волонтёры'),
        ('organizers', 'Организаторы'),
        ('hotel', 'Гостиничный'),
    ]

    festival = models.ForeignKey(
        Festival, on_delete=models.CASCADE, related_name='camps'
    )
    name = models.CharField('Название', max_length=255)
    territory = gis_models.PolygonField('Территория', srid=4326)
    description = models.TextField('Описание', blank=True)
    camp_type = models.CharField(
        'Тип', max_length=20, choices=CAMP_TYPES, default='general'
    )
    capacity = models.IntegerField('Вместимость', null=True, blank=True)

    class Meta:
        db_table = 'camp'
        verbose_name = 'Лагерь'
        verbose_name_plural = 'Лагеря'

    def __str__(self):
        return self.name


class Group(models.Model):
    """Группа участников."""
    festival = models.ForeignKey(
        Festival, on_delete=models.CASCADE, related_name='groups'
    )
    name = models.CharField('Название', max_length=255)
    camp = models.ForeignKey(
        Camp, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='groups'
    )
    leader = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='led_groups'
    )
    description = models.TextField('Описание', blank=True)

    class Meta:
        db_table = 'group'
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    """Участник группы."""
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name='members'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='group_memberships'
    )
    joined_at = models.DateTimeField('Присоединился', auto_now_add=True)

    class Meta:
        db_table = 'group_member'
        verbose_name = 'Участник группы'
        verbose_name_plural = 'Участники группы'
        constraints = [
            models.UniqueConstraint(
                fields=['group', 'user'],
                name='unique_group_user'
            )
        ]

    def __str__(self):
        return f'{self.user.username} в {self.group.name}'


class Booking(models.Model):
    """Бронирование территории в лагере."""
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('confirmed', 'Подтверждено'),
        ('rejected', 'Отклонено'),
        ('cancelled', 'Отменено'),
    ]

    festival = models.ForeignKey(
        Festival, on_delete=models.CASCADE, related_name='bookings'
    )
    camp = models.ForeignKey(
        Camp, on_delete=models.CASCADE, related_name='bookings'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='bookings'
    )
    territory = gis_models.PolygonField('Территория', srid=4326)
    status = models.CharField(
        'Статус', max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    notes = models.TextField('Комментарий', blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_bookings'
    )
    reviewed_at = models.DateTimeField('Рассмотрено', null=True, blank=True)

    class Meta:
        db_table = 'booking'
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} — {self.camp.name} ({self.get_status_display()})'