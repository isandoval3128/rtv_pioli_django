from django.urls import path
from .views import tarifas_view

urlpatterns = [
    path('tarifas/', tarifas_view, name='tarifas'),
]
