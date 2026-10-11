#!/bin/bash
# Полная перезапись файлов проекта «Былинный берег».
set -e

cd "$(dirname "$0")"

mkdir -p static/css templates/core templates/registration core

# =====================================================================
# core/permissions.py
# =====================================================================
cat > core/permissions.py << 'PYEOF'
"""Права доступа на основе ролей FestivalParticipant."""
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
PYEOF

# =====================================================================
# core/forms.py
# =====================================================================
cat > core/forms.py << 'PYEOF'
"""Формы регистрации."""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False, label='Email')
    phone = forms.CharField(max_length=20, required=False, label='Телефон')

    class Meta:
        model = User
        fields = ('username', 'email', 'phone')

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            Profile.objects.create(
                user=user,
                phone=self.cleaned_data.get('phone', ''),
            )
        return user
PYEOF

# =====================================================================
# core/serializers.py
# =====================================================================
cat > core/serializers.py << 'PYEOF'
"""Сериализаторы: модель → GeoJSON."""
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import Festival, Location, Event, InfoStand, Road, Camp


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
                  'priority', 'capacity', 'festival')


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


class CampSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Camp
        geo_field = 'territory'
        fields = ('id', 'name', 'description', 'camp_type',
                  'capacity', 'festival')
PYEOF

# =====================================================================
# core/views.py
# =====================================================================
cat > core/views.py << 'PYEOF'
"""Обработчики страниц и API."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .forms import RegisterForm
from .models import Festival, Location, Event, InfoStand, Road, Camp
from .serializers import (
    FestivalSerializer, LocationSerializer, EventSerializer,
    InfoStandSerializer, RoadSerializer, CampSerializer,
)
from .permissions import IsOrganizerOrReadOnly


def get_active_festival():
    return Festival.objects.filter(is_active=True).first()


def index(request):
    return render(request, 'core/index.html', {
        'festival': get_active_festival(),
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
        'festival': festival,
        'events': events,
    })


def location_detail(request, pk):
    location = get_object_or_404(Location, pk=pk)
    tabs = location.tabs.all()
    events = location.events.order_by('start_time')[:20]
    return render(request, 'core/location_detail.html', {
        'location': location,
        'tabs': tabs,
        'events': events,
    })


class FestivalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Festival.objects.filter(is_active=True)
    serializer_class = FestivalSerializer
    permission_classes = [AllowAny]


class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LocationSerializer
    permission_classes = [IsOrganizerOrReadOnly]

    def get_queryset(self):
        qs = Location.objects.filter(is_active=True).select_related('festival')
        festival_id = self.request.query_params.get('festival')
        if festival_id:
            qs = qs.filter(festival_id=festival_id)
        return qs


class EventViewSet(viewsets.ReadOnlyModelViewSet):
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


class RoadViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RoadSerializer
    permission_classes = [IsOrganizerOrReadOnly]

    def get_queryset(self):
        qs = Road.objects.all()
        festival_id = self.request.query_params.get('festival')
        if festival_id:
            qs = qs.filter(festival_id=festival_id)
        return qs


class CampViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CampSerializer
    permission_classes = [IsOrganizerOrReadOnly]

    def get_queryset(self):
        qs = Camp.objects.all()
        festival_id = self.request.query_params.get('festival')
        if festival_id:
            qs = qs.filter(festival_id=festival_id)
        return qs
PYEOF

# =====================================================================
# core/api_urls.py
# =====================================================================
cat > core/api_urls.py << 'PYEOF'
"""URL-маршруты для API."""
from rest_framework.routers import DefaultRouter
from .views import (
    FestivalViewSet, LocationViewSet, EventViewSet,
    InfoStandViewSet, RoadViewSet, CampViewSet,
)

router = DefaultRouter()
router.register('festivals', FestivalViewSet, basename='festival')
router.register('locations', LocationViewSet, basename='location')
router.register('events', EventViewSet, basename='event')
router.register('infostands', InfoStandViewSet, basename='infostand')
router.register('roads', RoadViewSet, basename='road')
router.register('camps', CampViewSet, basename='camp')

urlpatterns = router.urls
PYEOF

# =====================================================================
# core/urls.py
# =====================================================================
cat > core/urls.py << 'PYEOF'
"""URL-маршруты HTML-страниц."""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('events/', views.events_list, name='events_list'),
    path('locations/<int:pk>/', views.location_detail, name='location_detail'),
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
PYEOF

echo "== Python-файлы обновлены =="

# =====================================================================
# templates/base.html
# =====================================================================
cat > templates/base.html << 'HTMLEOF'
{% load static %}
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}Былинный берег{% endblock %}</title>
    <link rel="stylesheet" href="{% static 'css/main.css' %}">
    {% block head %}{% endblock %}
</head>
<body>

<header class="topbar">
    <a href="{% url 'index' %}" class="brand">
        <span class="brand-mark">Б</span>
        <span>Былинный берег</span>
    </a>
    <nav class="nav">
        <a href="{% url 'index' %}" class="{% if request.resolver_match.url_name == 'index' %}active{% endif %}">Карта</a>
        <a href="{% url 'events_list' %}" class="{% if request.resolver_match.url_name == 'events_list' %}active{% endif %}">Мероприятия</a>
        <a href="/admin/" target="_blank">Админка</a>
    </nav>
    <div class="auth">
        {% if user.is_authenticated %}
            <span class="user-chip">{{ user.username }}</span>
            <form action="{% url 'logout' %}" method="post" style="margin:0">
                {% csrf_token %}
                <button type="submit" class="btn btn-ghost btn-sm">Выйти</button>
            </form>
        {% else %}
            <a href="{% url 'login' %}" class="btn btn-ghost btn-sm">Войти</a>
            <a href="{% url 'register' %}" class="btn btn-accent btn-sm">Регистрация</a>
        {% endif %}
    </div>
</header>

<main>
    {% block content %}{% endblock %}
</main>

{% block scripts %}{% endblock %}
</body>
</html>
HTMLEOF

# =====================================================================
# templates/core/index.html
# =====================================================================
cat > templates/core/index.html << 'HTMLEOF'
{% extends "base.html" %}
{% load static %}
{% block title %}Карта — Былинный берег{% endblock %}

{% block head %}
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
{% endblock %}

{% block content %}
<div class="container" style="padding-bottom:12px">
    <h1 class="page-title">Карта фестиваля</h1>
    <p class="page-sub">{% if festival %}{{ festival.name }}{% else %}Активный фестиваль не найден{% endif %}</p>
</div>

<div class="container" style="padding-top:0">
    <div class="map-wrap">
        <div id="map"></div>

        <div class="map-panel">
            <h4>Слои</h4>
            <label class="layer-toggle"><input type="checkbox" id="layer-locations" checked><span class="layer-dot" style="background:#b6422b"></span>Локации</label>
            <label class="layer-toggle"><input type="checkbox" id="layer-roads" checked><span class="layer-dot" style="background:#8b6f47"></span>Дороги</label>
            <label class="layer-toggle"><input type="checkbox" id="layer-camps" checked><span class="layer-dot" style="background:#4a7c59"></span>Лагеря</label>
            <label class="layer-toggle"><input type="checkbox" id="layer-events" checked><span class="layer-dot" style="background:#c9a227"></span>Мероприятия</label>
        </div>

        <div class="legend">
            <h4>Типы локаций</h4>
            <div class="legend-item"><span class="layer-dot" style="background:#b6422b"></span>Сцена</div>
            <div class="legend-item"><span class="layer-dot" style="background:#d98324"></span>Еда</div>
            <div class="legend-item"><span class="layer-dot" style="background:#c0392b"></span>Медицина</div>
            <div class="legend-item"><span class="layer-dot" style="background:#2d6fb0"></span>Информация</div>
            <div class="legend-item"><span class="layer-dot" style="background:#6a7b8a"></span>Туалет</div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
(function() {
    const map = L.map('map').setView([58.764184, 31.538780], 14);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap', maxZoom: 19,
    }).addTo(map);

    const ICONS = {
        stage:   { emoji: '♪', cls: 'pin-stage' },
        food:    { emoji: '🍲', cls: 'pin-food' },
        medical: { emoji: '✚', cls: 'pin-medical' },
        toilet:  { emoji: '⚑', cls: 'pin-toilet' },
        info:    { emoji: 'i', cls: 'pin-info' },
        camp:    { emoji: '⛺', cls: 'pin-camp' },
        other:   { emoji: '•', cls: 'pin-other' },
    };
    function makeIcon(type) {
        const cfg = ICONS[type] || ICONS.other;
        const html = '<div class="pin ' + cfg.cls + '">' + cfg.emoji + '</div>';
        return L.divIcon({ html: html, className: '', iconSize: [32, 32],
                           iconAnchor: [16, 16], popupAnchor: [0, -16] });
    }

    const layers = {
        locations: L.layerGroup().addTo(map),
        roads:     L.layerGroup().addTo(map),
        camps:     L.layerGroup().addTo(map),
        events:    L.layerGroup().addTo(map),
    };

    fetch('/api/locations/').then(r => r.json()).then(data => {
        L.geoJSON(data, {
            pointToLayer: (f, ll) => L.marker(ll, { icon: makeIcon(f.properties.location_type) }),
            onEachFeature: (f, layer) => {
                const p = f.properties;
                layer.bindPopup(
                    '<div class="popup-title">' + p.name + '</div>' +
                    '<span class="popup-type">' + p.location_type + '</span>' +
                    (p.description ? '<div>' + p.description + '</div>' : '') +
                    '<a class="popup-link" href="/locations/' + p.id + '/">Подробнее →</a>'
                );
            }
        }).addTo(layers.locations);
    }).catch(e => console.error('locations:', e));

    fetch('/api/roads/').then(r => r.json()).then(data => {
        L.geoJSON(data, {
            style: f => ({
                color: f.properties.road_type === 'main' ? '#8b6f47' : '#b39a76',
                weight: f.properties.road_type === 'main' ? 5 : 3,
                opacity: 0.85, lineCap: 'round',
            }),
            onEachFeature: (f, layer) => {
                if (f.properties.name) layer.bindPopup('<b>' + f.properties.name + '</b>');
            }
        }).addTo(layers.roads);
    }).catch(e => console.error('roads:', e));

    fetch('/api/camps/').then(r => r.json()).then(data => {
        L.geoJSON(data, {
            style: { color: '#4a7c59', weight: 2, fillColor: '#4a7c59',
                     fillOpacity: 0.18, dashArray: '6 4' },
            onEachFeature: (f, layer) => layer.bindPopup('<b>' + f.properties.name + '</b>')
        }).addTo(layers.camps);
    }).catch(e => console.error('camps:', e));

    fetch('/api/events/').then(r => r.json()).then(data => {
        L.geoJSON(data, {
            filter: f => f.geometry !== null,
            pointToLayer: (f, ll) => L.circleMarker(ll, {
                radius: 8, color: '#c9a227', weight: 2,
                fillColor: '#fbf3d9', fillOpacity: 1,
            }),
            onEachFeature: (f, layer) => {
                const p = f.properties;
                const d = p.start_time ? new Date(p.start_time) : null;
                const time = d ? d.toLocaleString('ru-RU') : '';
                layer.bindPopup('<div class="popup-title">' + p.title + '</div>' +
                    (time ? '<div style="font-size:.85rem;color:#6b776b">' + time + '</div>' : ''));
            }
        }).addTo(layers.events);
    }).catch(e => console.error('events:', e));

    document.getElementById('layer-locations').addEventListener('change', e => {
        e.target.checked ? map.addLayer(layers.locations) : map.removeLayer(layers.locations);
    });
    document.getElementById('layer-roads').addEventListener('change', e => {
        e.target.checked ? map.addLayer(layers.roads) : map.removeLayer(layers.roads);
    });
    document.getElementById('layer-camps').addEventListener('change', e => {
        e.target.checked ? map.addLayer(layers.camps) : map.removeLayer(layers.camps);
    });
    document.getElementById('layer-events').addEventListener('change', e => {
        e.target.checked ? map.addLayer(layers.events) : map.removeLayer(layers.events);
    });
})();
</script>
{% endblock %}
HTMLEOF

echo "== Шаблоны (часть 1) обновлены =="

# =====================================================================
# templates/core/events.html
# =====================================================================
cat > templates/core/events.html << 'HTMLEOF'
{% extends "base.html" %}
{% block title %}Мероприятия{% endblock %}

{% block content %}
<div class="container">
    <h1 class="page-title">Мероприятия</h1>
    <p class="page-sub">{% if festival %}{{ festival.name }}{% endif %}</p>

    {% if events %}
        <div class="grid grid-2">
            {% for event in events %}
                <article class="event-card">
                    <span class="event-time">{{ event.start_time|date:"d M, H:i" }}</span>
                    <span class="badge badge-{{ event.status }}">{{ event.get_status_display }}</span>
                    <h3 class="event-title">{{ event.title }}</h3>
                    {% if event.description %}<p class="event-desc">{{ event.description }}</p>{% endif %}
                    <div class="event-meta">
                        {% if event.location %}<span>📍 {{ event.location.name }}</span>{% endif %}
                    </div>
                </article>
            {% endfor %}
        </div>
    {% else %}
        <div class="empty"><div class="empty-icon">📅</div><p>Пока мероприятий нет.</p></div>
    {% endif %}
</div>
{% endblock %}
HTMLEOF

# =====================================================================
# templates/core/location_detail.html
# =====================================================================
cat > templates/core/location_detail.html << 'HTMLEOF'
{% extends "base.html" %}
{% block title %}{{ location.name }}{% endblock %}

{% block head %}
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>#mini-map { width: 100%; height: 320px; border-radius: 16px; }</style>
{% endblock %}

{% block content %}
<div class="container">
    <h1 class="page-title">{{ location.name }}</h1>
    <p class="page-sub">
        <span class="badge" style="background:#e8eee9;color:#2d4a32">{{ location.get_location_type_display }}</span>
    </p>

    <div class="grid grid-2" style="grid-template-columns: 2fr 1fr">
        <div class="card">
            {% if tabs %}
                <div class="tabs">
                    {% for tab in tabs %}
                        <button class="tab-btn {% if forloop.first %}active{% endif %}" data-tab="tab-{{ tab.id }}">{{ tab.tab_name }}</button>
                    {% endfor %}
                </div>
                {% for tab in tabs %}
                    <div class="tab-panel {% if forloop.first %}active{% endif %}" id="tab-{{ tab.id }}">{{ tab.content|linebreaks }}</div>
                {% endfor %}
            {% else %}
                <p>{{ location.description|default:"Описание пока не добавлено." }}</p>
            {% endif %}

            {% if events %}
                <h3 style="margin-top:28px">Мероприятия здесь</h3>
                <ul style="list-style:none;padding:0">
                    {% for event in events %}
                        <li style="padding:10px 0;border-bottom:1px solid #e3e0d6">
                            <strong>{{ event.title }}</strong>
                            <span style="color:#6b776b;font-size:.85rem">— {{ event.start_time|date:"d M, H:i" }}</span>
                        </li>
                    {% endfor %}
                </ul>
            {% endif %}
        </div>
        <div class="card"><div id="mini-map"></div></div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.add('active');
        });
    });
    const lon = {{ location.geo_point.x }};
    const lat = {{ location.geo_point.y }};
    const map = L.map('mini-map').setView([lat, lon], 16);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap', maxZoom: 19,
    }).addTo(map);
    L.marker([lat, lon]).addTo(map).bindPopup('<b>{{ location.name|escapejs }}</b>').openPopup();
</script>
{% endblock %}
HTMLEOF

# =====================================================================
# templates/core/register.html
# =====================================================================
cat > templates/core/register.html << 'HTMLEOF'
{% extends "base.html" %}
{% block title %}Регистрация{% endblock %}
{% block content %}
<div class="container" style="max-width:480px">
    <div class="card">
        <h1 class="page-title" style="font-size:1.6rem">Регистрация</h1>
        <p class="page-sub">Создайте аккаунт, чтобы участвовать в фестивале.</p>
        <form method="post">
            {% csrf_token %}
            {{ form.as_p }}
            <button type="submit" class="btn" style="width:100%">Создать аккаунт</button>
        </form>
        <p style="text-align:center;margin-top:18px;color:#6b776b">
            Уже есть аккаунт? <a href="{% url 'login' %}" style="color:#2d4a32;font-weight:600">Войти</a>
        </p>
    </div>
</div>
{% endblock %}
HTMLEOF

# =====================================================================
# templates/registration/login.html
# =====================================================================
cat > templates/registration/login.html << 'HTMLEOF'
{% extends "base.html" %}
{% block title %}Вход{% endblock %}
{% block content %}
<div class="container" style="max-width:480px">
    <div class="card">
        <h1 class="page-title" style="font-size:1.6rem">Вход</h1>
        <p class="page-sub">Войдите, чтобы получить доступ к фестивалю.</p>
        <form method="post">
            {% csrf_token %}
            {{ form.as_p }}
            <button type="submit" class="btn" style="width:100%">Войти</button>
        </form>
        <p style="text-align:center;margin-top:18px;color:#6b776b">
            Нет аккаунта? <a href="{% url 'register' %}" style="color:#2d4a32;font-weight:600">Зарегистрируйтесь</a>
        </p>
    </div>
</div>
{% endblock %}
HTMLEOF

echo "== Шаблоны (часть 2) обновлены =="

# =====================================================================
# static/css/main.css
# =====================================================================
cat > static/css/main.css << 'CSSEOF'
:root {
    --bg: #f7f5f0;
    --surface: #ffffff;
    --surface-2: #fbfaf7;
    --primary: #2d4a32;
    --primary-hover: #243c28;
    --primary-soft: #e8eee9;
    --accent: #c9a227;
    --accent-hover: #b18d1a;
    --accent-soft: #fbf3d9;
    --text: #1f2a1f;
    --text-muted: #6b776b;
    --border: #e3e0d6;
    --danger: #a8392f;
    --success: #4a7c59;
    --shadow-sm: 0 2px 8px rgba(31, 42, 31, 0.06);
    --shadow: 0 4px 20px rgba(31, 42, 31, 0.08);
    --shadow-lg: 0 12px 40px rgba(31, 42, 31, 0.14);
    --radius-sm: 10px;
    --radius: 16px;
    --radius-lg: 24px;
    --transition: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

* { box-sizing: border-box; }

html, body {
    margin: 0; padding: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    font-size: 16px; line-height: 1.55; min-height: 100vh;
}
body { animation: fadeIn 0.5s ease-out; }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideInRight { from { opacity: 0; transform: translateX(20px); } to { opacity: 1; transform: translateX(0); } }
@keyframes pulse { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.08); opacity: 0.85; } }

.topbar {
    position: sticky; top: 0; z-index: 1000;
    display: flex; align-items: center; gap: 24px;
    padding: 14px 32px;
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: saturate(180%) blur(12px);
    -webkit-backdrop-filter: saturate(180%) blur(12px);
    border-bottom: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
}
.brand {
    display: flex; align-items: center; gap: 10px;
    font-weight: 700; font-size: 1.15rem;
    color: var(--primary); text-decoration: none;
    transition: transform var(--transition);
}
.brand:hover { transform: scale(1.03); }
.brand-mark {
    width: 32px; height: 32px; border-radius: 50%;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    display: grid; place-items: center; color: white;
    font-size: 16px; box-shadow: var(--shadow-sm);
}
.nav { display: flex; gap: 4px; margin-left: 8px; }
.nav a {
    padding: 8px 16px; border-radius: 999px;
    color: var(--text); text-decoration: none;
    font-size: 0.95rem; font-weight: 500;
    transition: background var(--transition), color var(--transition), transform var(--transition);
}
.nav a:hover { background: var(--primary-soft); color: var(--primary); transform: translateY(-1px); }
.nav a.active { background: var(--primary); color: white; }
.auth { margin-left: auto; display: flex; align-items: center; gap: 10px; }
.auth .user-chip {
    display: flex; align-items: center; gap: 8px;
    padding: 6px 14px; background: var(--primary-soft);
    border-radius: 999px; font-weight: 500; color: var(--primary);
}
.auth .user-chip::before {
    content: ""; width: 8px; height: 8px; border-radius: 50%;
    background: var(--success); animation: pulse 2.4s ease-in-out infinite;
}
.btn {
    display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    padding: 10px 20px; border: none; border-radius: 999px;
    background: var(--primary); color: white;
    font-family: inherit; font-size: 0.95rem; font-weight: 600;
    text-decoration: none; cursor: pointer;
    box-shadow: var(--shadow-sm);
    transition: transform var(--transition), box-shadow var(--transition), background var(--transition);
}
.btn:hover { background: var(--primary-hover); transform: translateY(-2px); box-shadow: var(--shadow); }
.btn:active { transform: translateY(0); }
.btn-accent { background: linear-gradient(135deg, var(--accent), var(--accent-hover)); color: white; }
.btn-accent:hover { background: linear-gradient(135deg, var(--accent-hover), #9c7a12); }
.btn-ghost { background: transparent; color: var(--primary); box-shadow: none; border: 1px solid var(--border); }
.btn-ghost:hover { background: var(--primary-soft); border-color: var(--primary); }
.btn-sm { padding: 6px 14px; font-size: 0.85rem; }
.container { max-width: 1200px; margin: 0 auto; padding: 32px; }
.card {
    background: var(--surface); border-radius: var(--radius-lg);
    padding: 24px; box-shadow: var(--shadow); border: 1px solid var(--border);
    animation: slideUp 0.4s ease-out both;
}
.card + .card { margin-top: 20px; }
.grid { display: grid; gap: 20px; }
.grid-2 { grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); }
.grid-3 { grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }
.grid > *:nth-child(1) { animation-delay: 0.00s; }
.grid > *:nth-child(2) { animation-delay: 0.05s; }
.grid > *:nth-child(3) { animation-delay: 0.10s; }
.grid > *:nth-child(4) { animation-delay: 0.15s; }
.grid > *:nth-child(5) { animation-delay: 0.20s; }
.grid > *:nth-child(6) { animation-delay: 0.25s; }
form p { margin: 0 0 18px; }
form p label { display: block; margin-bottom: 6px; font-weight: 600; font-size: 0.9rem; }
form p input {
    width: 100%; padding: 12px 16px;
    border: 1.5px solid var(--border); border-radius: var(--radius);
    background: var(--surface-2); font-family: inherit; font-size: 1rem;
    transition: border-color var(--transition), box-shadow var(--transition);
}
form p input:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 4px rgba(45, 74, 50, 0.12); }
form p .helptext { display: block; font-size: 0.8rem; color: var(--text-muted); margin-top: 4px; }
form p .errorlist { list-style: none; padding: 0; margin: 6px 0 0; color: var(--danger); font-size: 0.85rem; }
.map-wrap {
    position: relative; border-radius: var(--radius-lg); overflow: hidden;
    box-shadow: var(--shadow-lg);
    height: calc(100vh - 160px); min-height: 480px;
}
#map { width: 100%; height: 100%; }
.map-panel {
    position: absolute; top: 20px; right: 20px; z-index: 500;
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: saturate(180%) blur(12px);
    -webkit-backdrop-filter: saturate(180%) blur(12px);
    border-radius: var(--radius); padding: 16px 18px;
    box-shadow: var(--shadow-lg); min-width: 220px;
    animation: slideInRight 0.4s ease-out both;
}
.map-panel h4 {
    margin: 0 0 12px; font-size: 0.85rem; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--text-muted);
}
.layer-toggle {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 10px; border-radius: var(--radius-sm);
    cursor: pointer; transition: background var(--transition);
    font-size: 0.92rem; user-select: none;
}
.layer-toggle:hover { background: var(--primary-soft); }
.layer-toggle input {
    appearance: none; -webkit-appearance: none;
    width: 36px; height: 20px; border-radius: 999px;
    background: var(--border); position: relative; cursor: pointer;
    transition: background var(--transition);
}
.layer-toggle input::after {
    content: ""; position: absolute; top: 2px; left: 2px;
    width: 16px; height: 16px; border-radius: 50%; background: white;
    transition: transform var(--transition); box-shadow: var(--shadow-sm);
}
.layer-toggle input:checked { background: var(--primary); }
.layer-toggle input:checked::after { transform: translateX(16px); }
.layer-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
.legend {
    position: absolute; left: 20px; bottom: 20px; z-index: 500;
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: saturate(180%) blur(12px);
    -webkit-backdrop-filter: saturate(180%) blur(12px);
    border-radius: var(--radius); padding: 14px 18px;
    box-shadow: var(--shadow-lg);
    animation: slideUp 0.4s ease-out both;
}
.legend h4 {
    margin: 0 0 10px; font-size: 0.8rem; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--text-muted);
}
.legend-item { display: flex; align-items: center; gap: 8px; font-size: 0.88rem; padding: 3px 0; }
.pin {
    width: 32px; height: 32px; border-radius: 50%;
    display: grid; place-items: center; color: white;
    font-size: 15px; font-weight: 700; border: 2.5px solid white;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.25);
    transition: transform 0.15s ease-out;
}
.pin:hover { transform: scale(1.15); }
.pin-stage { background: #b6422b; }
.pin-food { background: #d98324; }
.pin-medical { background: #c0392b; }
.pin-toilet { background: #6a7b8a; }
.pin-info { background: #2d6fb0; }
.pin-camp { background: #4a7c59; }
.pin-other { background: #6b776b; }
.leaflet-popup-content-wrapper { border-radius: var(--radius); box-shadow: var(--shadow-lg); padding: 4px; }
.leaflet-popup-content { margin: 12px 16px; font-family: inherit; min-width: 180px; }
.popup-title { font-weight: 700; font-size: 1rem; margin-bottom: 4px; color: var(--primary); }
.popup-type {
    display: inline-block; font-size: 0.78rem; padding: 2px 10px;
    background: var(--primary-soft); color: var(--primary);
    border-radius: 999px; margin-bottom: 8px;
}
.popup-link {
    display: inline-block; margin-top: 8px; font-size: 0.85rem;
    color: var(--accent-hover); font-weight: 600; text-decoration: none;
}
.popup-link:hover { text-decoration: underline; }
.event-card {
    background: var(--surface); border-radius: var(--radius-lg);
    padding: 22px; border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
    transition: transform var(--transition), box-shadow var(--transition);
    animation: slideUp 0.4s ease-out both;
}
.event-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); }
.event-time {
    display: inline-block; font-size: 0.85rem; font-weight: 700;
    color: var(--accent-hover); background: var(--accent-soft);
    padding: 4px 12px; border-radius: 999px;
    margin-bottom: 10px; margin-right: 6px;
}
.event-title { font-size: 1.15rem; font-weight: 700; margin: 8px 0; color: var(--text); }
.event-desc { color: var(--text-muted); font-size: 0.94rem; margin: 0 0 12px; }
.event-meta { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: var(--text-muted); }
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 999px;
    font-size: 0.75rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.04em;
}
.badge-scheduled { background: #e3ecf5; color: #2d6fb0; }
.badge-ongoing { background: #e3f0e6; color: var(--success); }
.badge-cancelled { background: #f5e3e0; color: var(--danger); }
.badge-ended { background: #ececea; color: var(--text-muted); }
.page-title {
    font-size: 2rem; font-weight: 800; margin: 0 0 8px;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    -webkit-background-clip: text; background-clip: text; color: transparent;
}
.page-sub { color: var(--text-muted); margin: 0 0 28px; font-size: 1rem; }
.tabs {
    display: flex; gap: 4px; border-bottom: 1px solid var(--border);
    margin-bottom: 20px; overflow-x: auto;
}
.tab-btn {
    padding: 10px 18px; border: none; background: none;
    font-family: inherit; font-size: 0.95rem; font-weight: 600;
    color: var(--text-muted); cursor: pointer; position: relative;
    transition: color var(--transition); white-space: nowrap;
}
.tab-btn:hover { color: var(--primary); }
.tab-btn.active { color: var(--primary); }
.tab-btn.active::after {
    content: ""; position: absolute; bottom: -1px; left: 0; right: 0;
    height: 3px; background: linear-gradient(90deg, var(--primary), var(--accent));
    border-radius: 3px 3px 0 0; animation: slideUp 0.3s ease-out;
}
.tab-panel { display: none; animation: fadeIn 0.3s ease-out; }
.tab-panel.active { display: block; }
.empty { text-align: center; padding: 60px 20px; color: var(--text-muted); }
.empty-icon { font-size: 3rem; margin-bottom: 12px; opacity: 0.5; }
@media (max-width: 720px) {
    .topbar { padding: 12px 16px; gap: 12px; flex-wrap: wrap; }
    .nav a { padding: 6px 12px; font-size: 0.9rem; }
    .container { padding: 20px 16px; }
    .map-wrap { height: calc(100vh - 200px); }
    .map-panel { top: 10px; right: 10px; padding: 12px; min-width: 180px; }
    .legend { left: 10px; bottom: 10px; padding: 10px 12px; }
    .page-title { font-size: 1.6rem; }
}
CSSEOF

echo "== CSS обновлён =="
echo ""
echo "Готово. Теперь выполните:"
echo "  bash fix_all.sh"
