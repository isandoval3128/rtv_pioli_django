from django.urls import path
from . import views
from .views_cancelacion import (
    cancelar_turno_definitivo,
    solicitar_reprogramacion,
    ReprogramarTurnoView
)

app_name = 'turnero'

urlpatterns = [
    # Home
    path('', views.TurneroHomeView.as_view(), name='home'),

    # Flujo de 5 pasos
    path('paso1/', views.Step1ClienteView.as_view(), name='step1_cliente'),
    path('paso2/', views.Step2VehiculoView.as_view(), name='step2_vehiculo'),
    path('paso3/', views.Step3TallerView.as_view(), name='step3_taller'),
    path('paso4/', views.Step4FechaHoraView.as_view(), name='step4_fecha_hora'),
    path('paso5/', views.Step5ConfirmacionView.as_view(), name='step5_confirmacion'),

    # Success
    path('turno/<str:codigo>/success/', views.TurnoSuccessView.as_view(), name='turno_success'),

    # Consultar turno
    path('consultar/', views.ConsultarTurnoView.as_view(), name='consultar_turno'),

    # Imprimir turno (público)
    path('imprimir/<str:codigo>/', views.imprimir_turno_publico, name='imprimir_turno'),

    # Cancelación y Reprogramación
    path('cancelar-definitivo/<int:turno_id>/', cancelar_turno_definitivo, name='cancelar_definitivo'),
    path('solicitar-reprogramacion/<int:turno_id>/', solicitar_reprogramacion, name='solicitar_reprogramacion'),
    path('reprogramar/<str:token>/', ReprogramarTurnoView.as_view(), name='reprogramar_turno'),

    # AJAX endpoints
    path('ajax/buscar-persona/', views.buscar_persona_ajax, name='buscar_persona_ajax'),
    path('ajax/buscar-vehiculo/', views.buscar_vehiculo_ajax, name='buscar_vehiculo_ajax'),
    path('ajax/horarios-disponibles/', views.obtener_horarios_disponibles_ajax, name='horarios_disponibles_ajax'),
    path('ajax/fechas-disponibles/', views.obtener_fechas_disponibles_ajax, name='fechas_disponibles_ajax'),
    path('ajax/reservar-horario/', views.reservar_horario_ajax, name='reservar_horario_ajax'),
]
