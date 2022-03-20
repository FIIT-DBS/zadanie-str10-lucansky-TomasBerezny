from django import views
from django.urls import path
from . import views

urlpatterns = [
    path("v1/health/", views.say_hello),
    path('v2/patches/', views.endpoint2)
]