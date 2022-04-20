from django import views
from django.urls import path
from . import views

urlpatterns = [
    path("v1/health/", views.say_hello),
    path('v2/patches/', views.endpoint2),
    path('v2/players/<player_id>/game_exp', views.endpoint1),
    path('v3/matches/<match_id>/top_purchases/', views.purchases),
    path('v3/abilities/<ability_id>/usage/', views.ability_usage),
    path('v3/statistics/tower_kills/', views.tower_kills)
]