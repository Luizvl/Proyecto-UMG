from django.urls import path
from . import views_web

app_name = 'convocatorias'

urlpatterns = [
    path('', views_web.listado_convocatorias, name='lista'),
]