from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import views_asistente

urlpatterns = [
    # Autenticación
    path('login/', auth_views.LoginView.as_view(
        template_name='panel/login.html',
        redirect_authenticated_user=True
    ), name='panel_login'),
    path('logout/', views.logout_view, name='panel_logout'),

    # Home del panel
    path('', views.home, name='panel_home'),

    # Gestión de Turnos
    path('turnos/', views.gestion_turnos, name='gestion_turnos'),
    path('turnos/ajax/', views.gestion_turnos_ajax, name='gestion_turnos_ajax'),
    path('turnos/form/', views.gestion_turnos_form, name='gestion_turnos_form'),
    path('turnos/ver/', views.gestion_turnos_ver, name='gestion_turnos_ver'),
    path('turnos/guardar/', views.gestion_turnos_guardar, name='gestion_turnos_guardar'),
    path('turnos/cancelar/', views.gestion_turnos_cancelar, name='gestion_turnos_cancelar'),
    path('turnos/reenviar-email/', views.gestion_turnos_reenviar_email, name='gestion_turnos_reenviar_email'),
    path('turnos/whatsapp/', views.gestion_turnos_whatsapp, name='gestion_turnos_whatsapp'),
    path('turnos/imprimir/<int:pk>/', views.gestion_turnos_imprimir, name='gestion_turnos_imprimir'),

    # Escaneo de QR - Atención de Turnos
    path('turnos/escanear/', views.escanear_turno, name='escanear_turno'),
    path('turnos/verificar/', views.verificar_turno_panel, name='verificar_turno_panel'),
    path('turnos/registrar-atencion/', views.registrar_atencion_turno, name='registrar_atencion_turno'),

    # Gestión de Usuarios
    path('usuarios/', views.gestion_usuarios, name='gestion_usuarios'),
    path('usuarios/ajax/', views.gestion_usuarios_ajax, name='gestion_usuarios_ajax'),
    path('usuarios/form/', views.gestion_usuarios_form, name='gestion_usuarios_form'),
    path('usuarios/ver/', views.gestion_usuarios_ver, name='gestion_usuarios_ver'),
    path('usuarios/guardar/', views.gestion_usuarios_guardar, name='gestion_usuarios_guardar'),
    path('usuarios/imprimir/<int:pk>/', views.gestion_usuarios_imprimir, name='gestion_usuarios_imprimir'),
    path('usuarios/reset-password/', views.gestion_usuarios_reset_password, name='gestion_usuarios_reset_password'),
    path('usuarios/toggle/', views.gestion_usuarios_toggle, name='gestion_usuarios_toggle'),

    # Restablecimiento de contraseña (acceso público con token)
    path('restablecer-password/confirmar/', views.password_reset_confirm, name='password_reset_confirm'),
    path('restablecer-password/<str:token>/', views.password_reset_form, name='password_reset_form'),

    # Auxiliares
    path('vehiculos-cliente/', views.obtener_vehiculos_cliente, name='obtener_vehiculos_cliente'),
    path('cliente/guardar-rapido/', views.guardar_cliente_rapido, name='guardar_cliente_rapido'),
    path('vehiculo/guardar-rapido/', views.guardar_vehiculo_rapido, name='guardar_vehiculo_rapido'),
    path('taller/configuracion/', views.obtener_configuracion_taller, name='obtener_configuracion_taller'),
    path('taller/tipos-tramite/', views.obtener_tipos_tramite_taller, name='obtener_tipos_tramite_taller'),
    path('taller/horarios-disponibles/', views.obtener_horarios_disponibles, name='obtener_horarios_disponibles'),

    # ============================================
    # ASISTENTE VIRTUAL IA
    # ============================================
    # Configuración
    path('asistente/config/', views_asistente.asistente_config, name='asistente_config'),
    path('asistente/config/guardar/', views_asistente.asistente_config_guardar, name='asistente_config_guardar'),
    path('asistente/config/test/', views_asistente.asistente_config_test, name='asistente_config_test'),

    # FAQs
    path('asistente/faqs/', views_asistente.asistente_faqs, name='asistente_faqs'),
    path('asistente/faqs/ajax/', views_asistente.asistente_faqs_ajax, name='asistente_faqs_ajax'),
    path('asistente/faqs/form/', views_asistente.asistente_faqs_form, name='asistente_faqs_form'),
    path('asistente/faqs/guardar/', views_asistente.asistente_faqs_guardar, name='asistente_faqs_guardar'),
    path('asistente/faqs/eliminar/', views_asistente.asistente_faqs_eliminar, name='asistente_faqs_eliminar'),
    path('asistente/faqs/aprobar/', views_asistente.asistente_faqs_aprobar, name='asistente_faqs_aprobar'),
    path('asistente/faqs/default/', views_asistente.asistente_faqs_default, name='asistente_faqs_default'),

    # Base de Conocimiento
    path('asistente/kb/', views_asistente.asistente_kb, name='asistente_kb'),
    path('asistente/kb/ajax/', views_asistente.asistente_kb_ajax, name='asistente_kb_ajax'),
    path('asistente/kb/guardar/', views_asistente.asistente_kb_guardar, name='asistente_kb_guardar'),
    path('asistente/kb/eliminar/', views_asistente.asistente_kb_eliminar, name='asistente_kb_eliminar'),
    path('asistente/kb/toggle/', views_asistente.asistente_kb_toggle, name='asistente_kb_toggle'),

    # Conversaciones
    path('asistente/conversaciones/', views_asistente.asistente_conversaciones, name='asistente_conversaciones'),
    path('asistente/conversaciones/ajax/', views_asistente.asistente_conversaciones_ajax, name='asistente_conversaciones_ajax'),
    path('asistente/conversaciones/ver/', views_asistente.asistente_conversaciones_ver, name='asistente_conversaciones_ver'),

    # Uso IA / Costos
    path('asistente/uso-ia/', views_asistente.asistente_uso_ia, name='asistente_uso_ia'),
    path('asistente/uso-ia/ajax/', views_asistente.asistente_uso_ia_ajax, name='asistente_uso_ia_ajax'),

    # Dashboard
    path('asistente/dashboard/', views_asistente.asistente_dashboard, name='asistente_dashboard'),
    path('asistente/dashboard/ajax/', views_asistente.asistente_dashboard_ajax, name='asistente_dashboard_ajax'),

    # Sugerencias
    path('asistente/sugerencias/', views_asistente.asistente_sugerencias, name='asistente_sugerencias'),
    path('asistente/sugerencias/ajax/', views_asistente.asistente_sugerencias_ajax, name='asistente_sugerencias_ajax'),
    path('asistente/sugerencias/actualizar/', views_asistente.asistente_sugerencias_actualizar, name='asistente_sugerencias_actualizar'),
    path('asistente/sugerencias/eliminar/', views_asistente.asistente_sugerencias_eliminar, name='asistente_sugerencias_eliminar'),
    path('asistente/sugerencias/crear-faq/', views_asistente.asistente_sugerencias_crear_faq, name='asistente_sugerencias_crear_faq'),

    # Email resumen manual
    path('asistente/enviar-resumen/', views_asistente.asistente_enviar_resumen, name='asistente_enviar_resumen'),
]
