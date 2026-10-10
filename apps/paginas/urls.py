from django.urls import path
from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("como-funciona/", views.como_funciona, name="como_funciona"),
]
