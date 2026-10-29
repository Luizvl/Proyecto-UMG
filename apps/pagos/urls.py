from django.urls import path
from . import views

urlpatterns = [
    path('subir/', views.subir_pago, name='subir_pago'),
]