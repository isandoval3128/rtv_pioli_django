from django.urls import path
from . import views_api

urlpatterns = [
    path('api/session/', views_api.api_session, name='asistente_api_session'),
    path('api/mensaje/', views_api.api_mensaje, name='asistente_api_mensaje'),
    path('api/status/', views_api.api_status, name='asistente_api_status'),
    # Acción sobre sugerencia desde email (público, tokenizado)
    path('sugerencia-accion/<uuid:token>/', views_api.sugerencia_accion_token, name='sugerencia_accion_token'),
]
