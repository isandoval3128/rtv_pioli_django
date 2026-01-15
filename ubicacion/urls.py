from django.urls import path
from . import views

app_name = 'ubicacion'

urlpatterns = [
    path('', views.home, name='home'),
    path('api/<int:ubicacion_id>/', views.get_ubicacion_data, name='get_ubicacion_data'),
]
