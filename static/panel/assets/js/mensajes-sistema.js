/**
 * Sistema de Mensajes - JavaScript
 * Maneja el modal emergente y el flotante lateral de tareas
 */

var MensajesSistema = (function() {
    'use strict';

    // Configuración
    var config = {
        intervaloConsulta: 30000, // 30 segundos
        csrfToken: '',
        urls: {
            pendientes: '/sistema/mensajes/pendientes/',
            bloquear: '/sistema/mensajes/bloquear/',
            desbloquear: '/sistema/mensajes/desbloquear/',
            respondido: '/sistema/mensajes/respondido/',
            descartar: '/sistema/mensajes/descartar/'
        }
    };

    // Estado
    var state = {
        mensajes: [],
        mensajeActual: null,
        intervalId: null,
        panelAbierto: false,
        mensajesVistos: [] // Para no mostrar el mismo mensaje modal varias veces (persistido en localStorage)
    };

    // Clave para localStorage
    var STORAGE_KEY = 'mensajesSistemaVistos';

    // Elementos DOM
    var elements = {
        modal: null,
        flotante: null,
        flotanteToggle: null,
        flotantePanel: null,
        flotanteBody: null,
        flotanteBadge: null
    };

    /**
     * Obtiene el CSRF token de la cookie
     */
    function getCsrfToken() {
        // Primero intentar obtenerlo del input hidden
        var csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
            return csrfInput.value;
        }

        // Si no, obtenerlo de la cookie
        var name = 'csrftoken';
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue || config.csrfToken;
    }

    /**
     * Carga los mensajes vistos desde localStorage
     */
    function cargarMensajesVistos() {
        try {
            var stored = localStorage.getItem(STORAGE_KEY);
            if (stored) {
                var data = JSON.parse(stored);
                // Verificar que sea un array
                if (Array.isArray(data)) {
                    state.mensajesVistos = data;
                }
            }
        } catch (e) {
            console.warn('[MensajesSistema] Error al cargar mensajes vistos:', e);
            state.mensajesVistos = [];
        }
    }

    /**
     * Guarda los mensajes vistos en localStorage
     */
    function guardarMensajesVistos() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state.mensajesVistos));
        } catch (e) {
            console.warn('[MensajesSistema] Error al guardar mensajes vistos:', e);
        }
    }

    /**
     * Limpia los mensajes vistos (para usar en logout si es necesario)
     */
    function limpiarMensajesVistos() {
        state.mensajesVistos = [];
        try {
            localStorage.removeItem(STORAGE_KEY);
        } catch (e) {
            console.warn('[MensajesSistema] Error al limpiar mensajes vistos:', e);
        }
    }

    /**
     * Inicializa el sistema de mensajes
     */
    function init(csrfToken) {
        config.csrfToken = csrfToken;

        // Cargar mensajes vistos desde localStorage
        cargarMensajesVistos();

        // Crear elementos HTML
        crearElementosHTML();

        // Obtener referencias
        elements.modal = document.getElementById('mensaje-sistema-modal');
        elements.flotante = document.getElementById('tareas-flotante');
        elements.flotanteToggle = document.getElementById('tareas-flotante-toggle');
        elements.flotantePanel = document.getElementById('tareas-flotante-panel');
        elements.flotanteBody = document.getElementById('tareas-flotante-body');
        elements.flotanteBadge = document.getElementById('tareas-flotante-badge');

        // Configurar eventos
        configurarEventos();

        // Consultar mensajes inicialmente
        consultarMensajes();

        // Iniciar consulta periódica
        state.intervalId = setInterval(consultarMensajes, config.intervaloConsulta);

        console.log('[MensajesSistema] Sistema inicializado');
    }

    /**
     * Crea los elementos HTML necesarios
     */
    function crearElementosHTML() {
        // Modal de mensaje - ahora muestra lista de notificaciones
        var modalHTML = `
            <div id="mensaje-sistema-modal" class="mensaje-sistema-modal">
                <div class="mensaje-sistema-modal-content mensaje-sistema-modal-lista">
                    <div class="mensaje-sistema-modal-header">
                        <div class="icon-container">
                            <i class="fa fa-bell"></i>
                        </div>
                        <div class="header-text">
                            <h4 id="mensaje-modal-titulo">Notificaciones Pendientes</h4>
                            <span id="mensaje-modal-subtitulo">Revise sus notificaciones pendientes</span>
                        </div>
                    </div>
                    <div class="mensaje-sistema-modal-body">
                        <div id="mensaje-lista-tareas" class="mensaje-lista-tareas">
                            <!-- Las tareas se cargan dinamicamente -->
                        </div>
                    </div>
                    <div class="mensaje-sistema-modal-footer">
                        <button type="button" class="btn btn-cerrar" id="btn-mensaje-cerrar">
                            <i class="fa fa-times"></i> Cerrar
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Flotante lateral
        var flotanteHTML = `
            <div id="tareas-flotante" class="tareas-flotante oculto">
                <div id="tareas-flotante-panel" class="tareas-flotante-panel">
                    <div class="tareas-flotante-header">
                        <h5><i class="fa fa-bell"></i> Notificaciones</h5>
                        <button type="button" class="btn-cerrar-panel" id="btn-cerrar-panel">
                            <i class="fa fa-times"></i>
                        </button>
                    </div>
                    <div class="tareas-flotante-body" id="tareas-flotante-body">
                        <div class="tareas-flotante-empty">
                            <i class="fa fa-check-circle"></i>
                            <p>No hay notificaciones pendientes</p>
                        </div>
                    </div>
                </div>
                <button type="button" id="tareas-flotante-toggle" class="tareas-flotante-toggle">
                    <i class="fa fa-bell"></i>
                    <span id="tareas-flotante-badge" class="badge-contador" style="display: none;">0</span>
                </button>
            </div>
        `;

        // Insertar en el body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        document.body.insertAdjacentHTML('beforeend', flotanteHTML);
    }

    /**
     * Configura los eventos
     */
    function configurarEventos() {
        // Cerrar modal
        document.getElementById('btn-mensaje-cerrar').addEventListener('click', cerrarModal);

        // Toggle del flotante
        document.getElementById('tareas-flotante-toggle').addEventListener('click', togglePanel);

        // Cerrar panel flotante
        document.getElementById('btn-cerrar-panel').addEventListener('click', function() {
            cerrarPanel();
        });

        // Cerrar modal al hacer clic fuera
        elements.modal.addEventListener('click', function(e) {
            if (e.target === elements.modal) {
                cerrarModal();
            }
        });

        // Tecla ESC para cerrar modal
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && elements.modal.classList.contains('show')) {
                cerrarModal();
            }
        });

        // Liberar mensaje bloqueado al cerrar navegador o cambiar de pagina
        window.addEventListener('beforeunload', function(e) {
            liberarMensajesBloqueados();
        });

        // Liberar mensaje bloqueado si la pagina pierde visibilidad (cambio de pestana)
        document.addEventListener('visibilitychange', function() {
            if (document.visibilityState === 'hidden') {
                // Si el modal esta abierto y hay un mensaje bloqueado, liberarlo
                if (state.mensajeActual && elements.modal.classList.contains('show')) {
                    liberarMensajesBloqueados();
                }
            }
        });
    }

    /**
     * Libera todos los mensajes bloqueados por este usuario
     */
    function liberarMensajesBloqueados() {
        // Usar sendBeacon para asegurar que la peticion se envie aunque se cierre el navegador
        if (state.mensajeActual) {
            var formData = new FormData();
            formData.append('mensaje_id', state.mensajeActual.id);
            formData.append('csrfmiddlewaretoken', getCsrfToken());

            // sendBeacon es asincrono y no bloquea el cierre del navegador
            if (navigator.sendBeacon) {
                navigator.sendBeacon(config.urls.desbloquear, formData);
            } else {
                // Fallback para navegadores antiguos
                $.ajax({
                    url: config.urls.desbloquear,
                    type: 'POST',
                    data: {
                        mensaje_id: state.mensajeActual.id,
                        csrfmiddlewaretoken: getCsrfToken()
                    },
                    async: false // Sincrono para asegurar que se complete antes de cerrar
                });
            }
        }
    }

    /**
     * Consulta los mensajes pendientes del servidor
     */
    function consultarMensajes() {
        $.ajax({
            url: config.urls.pendientes,
            type: 'POST',
            data: {
                csrfmiddlewaretoken: getCsrfToken()
            },
            success: function(response) {
                if (response.success) {
                    procesarMensajes(response.mensajes);
                }
            },
            error: function(xhr, status, error) {
                console.error('[MensajesSistema] Error al consultar mensajes:', error);
            }
        });
    }

    /**
     * Procesa los mensajes recibidos
     */
    function procesarMensajes(mensajes) {
        state.mensajes = mensajes;

        // Actualizar flotante
        actualizarFlotante();

        // Si la URL tiene mensaje_id, el usuario ya esta respondiendo una tarea
        // No mostrar el modal automaticamente en este caso
        var urlParams = new URLSearchParams(window.location.search);
        var estaRespondiendo = urlParams.get('mensaje_id') !== null;

        if (estaRespondiendo) {
            // Marcar todos como vistos para no mostrar modal
            var nuevoAgregado = false;
            mensajes.forEach(function(m) {
                if (state.mensajesVistos.indexOf(m.id) === -1) {
                    state.mensajesVistos.push(m.id);
                    nuevoAgregado = true;
                }
            });
            if (nuevoAgregado) {
                guardarMensajesVistos();
            }
            return;
        }

        // Verificar si hay mensajes nuevos no vistos
        var mensajesNuevos = mensajes.filter(function(m) {
            return state.mensajesVistos.indexOf(m.id) === -1;
        });

        // Mostrar modal con lista de tareas si hay mensajes y el modal no está abierto
        if (mensajes.length > 0 && mensajesNuevos.length > 0 && !elements.modal.classList.contains('show')) {
            mostrarModalLista();
            // Marcar todos como vistos para no volver a mostrar automaticamente
            mensajes.forEach(function(m) {
                if (state.mensajesVistos.indexOf(m.id) === -1) {
                    state.mensajesVistos.push(m.id);
                }
            });
            // Persistir en localStorage
            guardarMensajesVistos();
        }
    }

    /**
     * Actualiza el flotante lateral con los mensajes
     */
    function actualizarFlotante() {
        var total = state.mensajes.length;

        if (total === 0) {
            elements.flotante.classList.add('oculto');
            return;
        }

        elements.flotante.classList.remove('oculto');

        // Actualizar badge
        elements.flotanteBadge.textContent = total;
        elements.flotanteBadge.style.display = total > 0 ? 'flex' : 'none';

        // Actualizar lista de tareas
        var html = '';
        state.mensajes.forEach(function(mensaje) {
            // Detectar tipos de notificacion especiales - Tareas
            var esTareaCompletada = mensaje.tipo === 'TAREA_COMPLETADA';
            var esTareaCancelada = mensaje.tipo === 'TAREA_CANCELADA';
            var esTareaExpirada = mensaje.tipo === 'TAREA_EXPIRADA';

            // Detectar tipos de notificacion especiales - Movimientos
            var esMovimientoPendiente = mensaje.tipo === 'MOVIMIENTO_PENDIENTE';
            var esMovimientoAceptado = mensaje.tipo === 'MOVIMIENTO_ACEPTADO';
            var esMovimientoRechazado = mensaje.tipo === 'MOVIMIENTO_RECHAZADO';

            // Detectar tipo - Caso Creado
            var esCasoCreado = mensaje.tipo === 'CASO_CREADO';

            // Determinar urgencia para casos creados (3=alta, 2=media, 1=baja)
            var urgenciaCaso = esCasoCreado && mensaje.datos ? mensaje.datos.urgencia : null;
            var urgenciaClaseFlotante = '';
            if (esCasoCreado && urgenciaCaso) {
                if (urgenciaCaso == 3 || urgenciaCaso == '3') {
                    urgenciaClaseFlotante = 'caso-urgencia-alta';
                } else if (urgenciaCaso == 2 || urgenciaCaso == '2') {
                    urgenciaClaseFlotante = 'caso-urgencia-media';
                } else {
                    urgenciaClaseFlotante = 'caso-urgencia-baja';
                }
            }

            // Determinar clase de estado (prioridad: tipo > estado)
            var estadoClase = mensaje.bloqueado_por_otro ? 'bloqueado' :
                              esCasoCreado ? 'caso-creado ' + urgenciaClaseFlotante :
                              esTareaCompletada ? 'completada' :
                              esTareaCancelada ? 'cancelado' :
                              esTareaExpirada ? 'expirado' :
                              esMovimientoAceptado ? 'completada' :
                              esMovimientoRechazado ? 'cancelado' :
                              esMovimientoPendiente ? 'movimiento-pendiente' :
                              mensaje.estado === 'RESPONDIDO' ? 'respondido' :
                              mensaje.estado === 'CANCELADO' ? 'cancelado' :
                              mensaje.estado === 'EXPIRADO' ? 'expirado' :
                              mensaje.estado === 'EN_PROCESO' ? 'en-proceso' : 'pendiente';

            // Determinar texto de estado
            var estadoTexto = esCasoCreado ? 'Nuevo' :
                              esTareaCompletada ? 'Completada' :
                              esTareaCancelada ? 'Cancelada' :
                              esTareaExpirada ? 'Expirada' :
                              esMovimientoAceptado ? 'Aceptado' :
                              esMovimientoRechazado ? 'Rechazado' :
                              esMovimientoPendiente ? 'Pendiente' :
                              mensaje.bloqueado_por_otro ? 'Bloqueado' :
                              mensaje.estado === 'RESPONDIDO' ? 'Respondido' :
                              mensaje.estado === 'CANCELADO' ? 'Cancelado' :
                              mensaje.estado === 'EXPIRADO' ? 'Expirado' :
                              mensaje.estado === 'EN_PROCESO' ? 'En proceso' : 'Pendiente';

            var prioridadClase = 'tarea-prioridad-' + mensaje.prioridad.toLowerCase();
            var tipoClass = esCasoCreado ? 'caso-creado-flotante ' + urgenciaClaseFlotante :
                            esTareaCompletada ? 'tarea-completada-flotante' :
                            esTareaCancelada ? 'tarea-cancelado-flotante' :
                            esTareaExpirada ? 'tarea-expirado-flotante' :
                            esMovimientoAceptado ? 'movimiento-aceptado-flotante' :
                            esMovimientoRechazado ? 'movimiento-rechazado-flotante' :
                            esMovimientoPendiente ? 'movimiento-pendiente-flotante' :
                            mensaje.estado === 'RESPONDIDO' ? 'tarea-respondido-flotante' :
                            mensaje.estado === 'CANCELADO' ? 'tarea-cancelado-flotante' :
                            mensaje.estado === 'EXPIRADO' ? 'tarea-expirado-flotante' : '';

            // Icono segun tipo y estado
            var icono = esCasoCreado ? 'fa-folder-open' :
                        esTareaCompletada ? 'fa-check-circle' :
                        esTareaCancelada ? 'fa-times-circle' :
                        esTareaExpirada ? 'fa-clock-o' :
                        esMovimientoAceptado ? 'fa-check-circle' :
                        esMovimientoRechazado ? 'fa-times-circle' :
                        esMovimientoPendiente ? 'fa-exchange' :
                        mensaje.estado === 'RESPONDIDO' ? 'fa-check-circle' :
                        mensaje.estado === 'CANCELADO' ? 'fa-times-circle' :
                        mensaje.estado === 'EXPIRADO' ? 'fa-clock-o' : 'fa-check-square-o';

            var iconoClase = esCasoCreado ? 'icon-caso-creado' :
                             esTareaCompletada ? 'icon-completada' :
                             esTareaCancelada ? 'icon-cancelado' :
                             esTareaExpirada ? 'icon-expirado' :
                             esMovimientoAceptado ? 'icon-completada' :
                             esMovimientoRechazado ? 'icon-cancelado' :
                             esMovimientoPendiente ? 'icon-movimiento' :
                             mensaje.estado === 'RESPONDIDO' ? 'icon-respondido' :
                             mensaje.estado === 'CANCELADO' ? 'icon-cancelado' :
                             mensaje.estado === 'EXPIRADO' ? 'icon-expirado' : '';

            // Construir texto de origen (usuario + sector)
            var textoOrigen = escapeHtml(mensaje.usuario_origen || 'Sistema');
            if (mensaje.sector_origen) {
                textoOrigen += ' (' + escapeHtml(mensaje.sector_origen) + ')';
            }

            html += `
                <div class="tarea-flotante-item ${prioridadClase} ${tipoClass}"
                     data-mensaje-id="${mensaje.id}"
                     onclick="MensajesSistema.seleccionarTarea(${mensaje.id})">
                    <div class="tarea-icon ${iconoClase}">
                        <i class="fa ${icono}"></i>
                    </div>
                    <div class="tarea-info">
                        <div class="tarea-titulo">${escapeHtml(mensaje.titulo)}</div>
                        <div class="tarea-detalle">
                            <span><i class="fa fa-user"></i> ${textoOrigen}</span>
                            <span class="tarea-estado ${estadoClase}">${estadoTexto}</span>
                        </div>
                    </div>
                </div>
            `;
        });

        if (html === '') {
            html = `
                <div class="tareas-flotante-empty">
                    <i class="fa fa-check-circle"></i>
                    <p>No hay notificaciones pendientes</p>
                </div>
            `;
        }

        elements.flotanteBody.innerHTML = html;
    }

    /**
     * Muestra el modal con la lista de todas las notificaciones pendientes
     */
    function mostrarModalLista() {
        var listaTareas = document.getElementById('mensaje-lista-tareas');
        var titulo = document.getElementById('mensaje-modal-titulo');
        var subtitulo = document.getElementById('mensaje-modal-subtitulo');

        // Contar tipos de mensajes
        var total = state.mensajes.length;
        var totalTareas = state.mensajes.filter(function(m) {
            return m.tipo === 'TAREA_ASIGNADA' || m.tipo === 'TAREA_COMPLETADA' || m.tipo === 'TAREA_CANCELADA' || m.tipo === 'TAREA_EXPIRADA';
        }).length;
        var totalMovimientos = state.mensajes.filter(function(m) {
            return m.tipo === 'MOVIMIENTO_PENDIENTE' || m.tipo === 'MOVIMIENTO_ACEPTADO' || m.tipo === 'MOVIMIENTO_RECHAZADO';
        }).length;
        var totalCasosCreados = state.mensajes.filter(function(m) {
            return m.tipo === 'CASO_CREADO';
        }).length;

        // Actualizar titulo segun cantidad y tipo
        if (total === 1) {
            if (totalMovimientos === 1) {
                titulo.textContent = 'Solicitud de Movimiento';
                subtitulo.textContent = 'Tiene una solicitud de movimiento pendiente';
            } else if (totalCasosCreados === 1) {
                titulo.textContent = 'Nuevo Caso';
                subtitulo.textContent = 'Se ha creado un nuevo caso en el sistema';
            } else {
                titulo.textContent = 'Nueva Tarea';
                subtitulo.textContent = 'Tiene una tarea pendiente';
            }
        } else {
            // Mostrar descripcion según composición
            var descripcion = [];
            if (totalTareas > 0) descripcion.push(totalTareas + ' tarea' + (totalTareas > 1 ? 's' : ''));
            if (totalMovimientos > 0) descripcion.push(totalMovimientos + ' movimiento' + (totalMovimientos > 1 ? 's' : ''));
            if (totalCasosCreados > 0) descripcion.push(totalCasosCreados + ' caso' + (totalCasosCreados > 1 ? 's nuevo' + 's' : ' nuevo'));

            titulo.textContent = 'Notificaciones (' + total + ')';
            subtitulo.textContent = descripcion.length > 0 ? descripcion.join(' y ') : 'Revise sus notificaciones pendientes';
        }

        // Generar HTML de la lista de tareas
        var html = '';
        state.mensajes.forEach(function(mensaje) {
            // Detectar tipos de notificacion especiales - Tareas
            var esTareaCompletada = mensaje.tipo === 'TAREA_COMPLETADA';
            var esTareaCancelada = mensaje.tipo === 'TAREA_CANCELADA';
            var esTareaExpirada = mensaje.tipo === 'TAREA_EXPIRADA';

            // Detectar tipos de notificacion especiales - Movimientos
            var esMovimientoPendiente = mensaje.tipo === 'MOVIMIENTO_PENDIENTE';
            var esMovimientoAceptado = mensaje.tipo === 'MOVIMIENTO_ACEPTADO';
            var esMovimientoRechazado = mensaje.tipo === 'MOVIMIENTO_RECHAZADO';

            // Detectar tipo - Caso Creado
            var esCasoCreado = mensaje.tipo === 'CASO_CREADO';

            // Determinar urgencia para casos creados (3=alta, 2=media, 1=baja)
            var urgenciaCasoModal = esCasoCreado && mensaje.datos ? mensaje.datos.urgencia : null;
            var urgenciaClaseModal = '';
            if (esCasoCreado && urgenciaCasoModal) {
                if (urgenciaCasoModal == 3 || urgenciaCasoModal == '3') {
                    urgenciaClaseModal = 'caso-urgencia-alta';
                } else if (urgenciaCasoModal == 2 || urgenciaCasoModal == '2') {
                    urgenciaClaseModal = 'caso-urgencia-media';
                } else {
                    urgenciaClaseModal = 'caso-urgencia-baja';
                }
            }

            // Determinar clase de estado (prioridad: tipo > estado)
            var estadoClase = mensaje.bloqueado_por_otro ? 'bloqueado' :
                              esCasoCreado ? 'caso-creado ' + urgenciaClaseModal :
                              esTareaCompletada ? 'completada' :
                              esTareaCancelada ? 'cancelado' :
                              esTareaExpirada ? 'expirado' :
                              esMovimientoAceptado ? 'completada' :
                              esMovimientoRechazado ? 'cancelado' :
                              esMovimientoPendiente ? 'movimiento-pendiente' :
                              mensaje.estado === 'RESPONDIDO' ? 'respondido' :
                              mensaje.estado === 'CANCELADO' ? 'cancelado' :
                              mensaje.estado === 'EXPIRADO' ? 'expirado' :
                              mensaje.estado === 'EN_PROCESO' ? 'en-proceso' : 'pendiente';

            // Determinar texto de estado según urgencia
            var estadoTexto = esCasoCreado ? (urgenciaClaseModal === 'caso-urgencia-alta' ? 'Urgente' :
                                              urgenciaClaseModal === 'caso-urgencia-media' ? 'Media' : 'Normal') :
                              esTareaCompletada ? 'Completada' :
                              esTareaCancelada ? 'Cancelada' :
                              esTareaExpirada ? 'Expirada' :
                              esMovimientoAceptado ? 'Aceptado' :
                              esMovimientoRechazado ? 'Rechazado' :
                              esMovimientoPendiente ? 'Pendiente' :
                              mensaje.bloqueado_por_otro ? 'Bloqueado por ' + mensaje.nombre_bloqueador :
                              mensaje.estado === 'RESPONDIDO' ? 'Respondido' :
                              mensaje.estado === 'CANCELADO' ? 'Cancelado' :
                              mensaje.estado === 'EXPIRADO' ? 'Expirado' :
                              mensaje.estado === 'EN_PROCESO' ? 'En proceso' : 'Pendiente';

            var prioridadClase = 'tarea-prioridad-' + mensaje.prioridad.toLowerCase();
            var bloqueadoClass = mensaje.bloqueado_por_otro ? 'tarea-bloqueada' : '';

            // Clase de tipo segun tipo de mensaje y estado
            var tipoClass = esCasoCreado ? 'caso-creado-notif' :
                            esTareaCompletada ? 'tarea-completada-notif' :
                            esTareaCancelada ? 'tarea-cancelado-notif' :
                            esTareaExpirada ? 'tarea-expirado-notif' :
                            esMovimientoAceptado ? 'movimiento-aceptado-notif' :
                            esMovimientoRechazado ? 'movimiento-rechazado-notif' :
                            esMovimientoPendiente ? 'movimiento-pendiente-notif' :
                            mensaje.estado === 'RESPONDIDO' ? 'tarea-respondido-notif' :
                            mensaje.estado === 'CANCELADO' ? 'tarea-cancelado-notif' :
                            mensaje.estado === 'EXPIRADO' ? 'tarea-expirado-notif' : '';

            // Icono segun tipo de mensaje y estado
            var icono = esCasoCreado ? 'fa-folder-open' :
                        esTareaCompletada ? 'fa-check-circle' :
                        esTareaCancelada ? 'fa-times-circle' :
                        esTareaExpirada ? 'fa-clock-o' :
                        esMovimientoAceptado ? 'fa-check-circle' :
                        esMovimientoRechazado ? 'fa-times-circle' :
                        esMovimientoPendiente ? 'fa-exchange' :
                        mensaje.bloqueado_por_otro ? 'fa-lock' :
                        mensaje.estado === 'RESPONDIDO' ? 'fa-check-circle' :
                        mensaje.estado === 'CANCELADO' ? 'fa-times-circle' :
                        mensaje.estado === 'EXPIRADO' ? 'fa-clock-o' : 'fa-check-square-o';

            var iconoColor = esCasoCreado ? 'icon-caso-creado' :
                             esTareaCompletada ? 'icon-completada' :
                             esTareaCancelada ? 'icon-cancelado' :
                             esTareaExpirada ? 'icon-expirado' :
                             esMovimientoAceptado ? 'icon-completada' :
                             esMovimientoRechazado ? 'icon-cancelado' :
                             esMovimientoPendiente ? 'icon-movimiento' :
                             mensaje.estado === 'RESPONDIDO' ? 'icon-respondido' :
                             mensaje.estado === 'CANCELADO' ? 'icon-cancelado' :
                             mensaje.estado === 'EXPIRADO' ? 'icon-expirado' : '';

            // Botones segun tipo de mensaje y estado
            var botonesHtml = '';
            var esNotificacionFinal = esTareaCompletada || esTareaCancelada || esTareaExpirada ||
                                       esMovimientoAceptado || esMovimientoRechazado || esCasoCreado ||
                                       ['RESPONDIDO', 'CANCELADO', 'EXPIRADO'].indexOf(mensaje.estado) !== -1;

            if (esMovimientoPendiente) {
                // Para movimientos pendientes: mostrar botones Aceptar y Rechazar
                botonesHtml = mensaje.bloqueado_por_otro ?
                    '<button type="button" class="btn btn-tarea-bloqueada" disabled><i class="fa fa-lock"></i> No disponible</button>' :
                    `<button type="button" class="btn btn-movimiento-aceptar" onclick="MensajesSistema.aceptarMovimiento(${mensaje.id}, event); return false;">
                        <i class="fa fa-check"></i> Aceptar Caso
                    </button>
                    <button type="button" class="btn btn-movimiento-rechazar" onclick="MensajesSistema.rechazarMovimiento(${mensaje.id}, event); return false;">
                        <i class="fa fa-times"></i> Rechazar
                    </button>
                    <button type="button" class="btn btn-tarea-ver-caso" onclick="MensajesSistema.verCaso(${mensaje.id}); return false;">
                        <i class="fa fa-eye"></i> Ver Caso
                    </button>`;
            } else if (esNotificacionFinal) {
                // Para notificaciones de tipo especial (TAREA_COMPLETADA, MOVIMIENTO_ACEPTADO, etc.)
                // y estados finales (RESPONDIDO, CANCELADO, EXPIRADO)
                // Determinar texto del botón según tipo
                var textoMarcarLeido = (esMovimientoAceptado || esMovimientoRechazado) ? 'Marcar como Leido' : 'Marcar como Leido';
                botonesHtml = `
                    <button type="button" class="btn btn-tarea-ver-caso" onclick="MensajesSistema.verCaso(${mensaje.id})">
                        <i class="fa fa-eye"></i> Ver Caso
                    </button>
                    <button type="button" class="btn btn-tarea-marcar-leido" onclick="MensajesSistema.marcarLeido(${mensaje.id})">
                        <i class="fa fa-check"></i> ${textoMarcarLeido}
                    </button>
                `;
            } else {
                // Para tareas asignadas pendientes
                if (mensaje.bloqueado_por_otro) {
                    botonesHtml = '<button type="button" class="btn btn-tarea-bloqueada" disabled><i class="fa fa-lock"></i> No disponible</button>';
                } else {
                    botonesHtml = '<button type="button" class="btn btn-tarea-responder" onclick="MensajesSistema.responderTarea(' + mensaje.id + ')"><i class="fa fa-reply"></i> Responder Tarea</button>';
                    // Agregar botón de declinar - el ID de tarea se obtiene del servidor usando mensaje_id
                    botonesHtml += ' <button type="button" class="btn btn-tarea-declinar" onclick="MensajesSistema.declinarTarea(' + mensaje.id + ')"><i class="fa fa-ban"></i> Declinar Solicitud</button>';
                }
            }

            // Texto de estado para mostrar (usar estadoTexto que ya tiene la lógica correcta)
            var estadoMostrar = estadoTexto;

            // Construir texto de origen para el modal (usuario + sector en línea separada si existe)
            var usuarioOrigenHtml = escapeHtml(mensaje.usuario_origen || 'Sistema');
            var sectorOrigenHtml = mensaje.sector_origen ? `<span><i class="fa fa-building"></i> ${escapeHtml(mensaje.sector_origen)}</span>` : '';

            html += `
                <div class="mensaje-tarea-item ${prioridadClase} ${bloqueadoClass} ${tipoClass}" data-mensaje-id="${mensaje.id}" data-tipo="${mensaje.tipo}" data-estado="${mensaje.estado}">
                    <div class="mensaje-tarea-header">
                        <div class="mensaje-tarea-icon ${iconoColor}">
                            <i class="fa ${icono}"></i>
                        </div>
                        <div class="mensaje-tarea-info">
                            <div class="mensaje-tarea-titulo">${escapeHtml(mensaje.titulo)}</div>
                            <div class="mensaje-tarea-meta">
                                <span><i class="fa fa-folder"></i> ${escapeHtml(mensaje.datos ? mensaje.datos.caso_codigo : '-')}</span>
                                <span><i class="fa fa-user"></i> ${usuarioOrigenHtml}</span>
                                ${sectorOrigenHtml}
                                <span><i class="fa fa-calendar"></i> ${mensaje.fecha_creacion}</span>
                            </div>
                        </div>
                        <div class="mensaje-tarea-estado">
                            <span class="tarea-estado ${estadoClase}">${estadoMostrar}</span>
                        </div>
                    </div>
                    <div class="mensaje-tarea-contenido">
                        ${escapeHtml(mensaje.contenido)}
                    </div>
                    <div class="mensaje-tarea-acciones">
                        ${botonesHtml}
                    </div>
                </div>
            `;
        });

        listaTareas.innerHTML = html;

        // Mostrar modal
        elements.modal.classList.add('show');
    }

    /**
     * Responde a una tarea especifica de la lista
     */
    function responderTarea(mensajeId) {
        var mensaje = state.mensajes.find(function(m) {
            return m.id === mensajeId;
        });

        if (!mensaje) return;

        if (mensaje.bloqueado_por_otro) {
            Swal.fire({
                title: 'Notificación en proceso',
                text: mensaje.nombre_bloqueador + ' ya está respondiendo esta tarea',
                icon: 'warning',
                confirmButtonColor: (typeof ThemeSwitcher !== 'undefined') ? ThemeSwitcher.getPrimaryColor() : '#13304D'
            });
            return;
        }

        // Cerrar el modal inmediatamente antes de bloquear
        elements.modal.classList.remove('show');
        elements.modal.style.display = 'none';

        // Bloquear el mensaje y redirigir
        bloquearMensaje(mensajeId, function(success) {
            if (success) {
                state.mensajeActual = mensaje;

                // Construir URL de redireccion con mensaje_id
                var redirectUrl = '';
                if (mensaje.accion_url) {
                    // Agregar mensaje_id a la URL existente
                    redirectUrl = mensaje.accion_url;
                    if (redirectUrl.indexOf('?') !== -1) {
                        redirectUrl += '&mensaje_id=' + mensaje.id;
                    } else {
                        redirectUrl += '?mensaje_id=' + mensaje.id;
                    }
                } else if (mensaje.datos && mensaje.datos.caso_id) {
                    redirectUrl = '/casos/gestion_casos_verMas/' + mensaje.datos.caso_id + '/?from=tareas&mensaje_id=' + mensaje.id;
                }

                if (redirectUrl) {
                    window.location.href = redirectUrl;
                }
            } else {
                // Si falla, volver a mostrar el modal
                elements.modal.style.display = '';
                elements.modal.classList.add('show');
            }
        });
    }

    /**
     * Declinar una solicitud de tarea
     */
    function declinarTarea(mensajeId) {
        var mensaje = state.mensajes.find(function(m) {
            return m.id === mensajeId;
        });

        if (!mensaje) return;

        if (mensaje.bloqueado_por_otro) {
            Swal.fire({
                title: 'Notificación en proceso',
                text: mensaje.nombre_bloqueador + ' ya está gestionando esta tarea',
                icon: 'warning',
                confirmButtonColor: (typeof ThemeSwitcher !== 'undefined') ? ThemeSwitcher.getPrimaryColor() : '#13304D'
            });
            return;
        }

        // Cerrar el modal
        elements.modal.classList.remove('show');
        elements.modal.style.display = 'none';

        // Abrir el formulario de declinar tarea en el modal-lg
        // Usamos mensaje_id para que el backend obtenga el ID de la tarea asignada
        var formData = new FormData();
        formData.append('mensaje_id', mensajeId);
        formData.append('csrfmiddlewaretoken', config.csrfToken);

        $.ajax({
            url: '/casos/gestion_asignacion_tareas_cancelar_form',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(data) {
                if (!data.success) {
                    $("#modal-lg .modal-content").html(data.html_form);
                    $("#modal-lg").modal({backdrop: 'static', keyboard: false}).modal("show");
                } else {
                    // Si success es true, volver a mostrar el modal de mensajes
                    elements.modal.classList.add('show');
                    elements.modal.style.display = '';
                }
            },
            error: function() {
                // Volver a mostrar el modal de mensajes en caso de error
                elements.modal.classList.add('show');
                elements.modal.style.display = '';
                Swal.fire({
                    title: 'Error',
                    text: 'No se pudo cargar el formulario de declinación',
                    icon: 'error',
                    confirmButtonColor: (typeof ThemeSwitcher !== 'undefined') ? ThemeSwitcher.getPrimaryColor() : '#13304D'
                });
            }
        });
    }

    /**
     * Cierra el modal
     */
    function cerrarModal() {
        elements.modal.classList.remove('show');
        elements.modal.style.display = '';

        // Si habia bloqueado el mensaje, desbloquearlo
        if (state.mensajeActual && state.mensajeActual.estado === 'EN_PROCESO') {
            desbloquearMensaje(state.mensajeActual.id);
        }

        state.mensajeActual = null;
    }

    /**
     * Selecciona una tarea del flotante - abre el modal con la lista
     */
    function seleccionarTarea(mensajeId) {
        // Cerrar panel flotante
        cerrarPanel();

        // Mostrar modal con lista de tareas
        mostrarModalLista();
    }

    /**
     * Toggle del panel flotante
     */
    function togglePanel() {
        if (state.panelAbierto) {
            cerrarPanel();
        } else {
            abrirPanel();
        }
    }

    /**
     * Abre el panel flotante
     */
    function abrirPanel() {
        elements.flotantePanel.classList.add('show');
        state.panelAbierto = true;
    }

    /**
     * Cierra el panel flotante
     */
    function cerrarPanel() {
        elements.flotantePanel.classList.remove('show');
        state.panelAbierto = false;
    }

    /**
     * Bloquea un mensaje en el servidor
     */
    function bloquearMensaje(mensajeId, callback) {
        $.ajax({
            url: config.urls.bloquear,
            type: 'POST',
            data: {
                mensaje_id: mensajeId,
                csrfmiddlewaretoken: getCsrfToken()
            },
            success: function(response) {
                if (response.success) {
                    callback(true);
                } else {
                    if (response.error === 'bloqueado') {
                        Swal.fire({
                            title: 'Tarea en proceso',
                            text: response.mensaje,
                            icon: 'warning',
                            confirmButtonColor: (typeof ThemeSwitcher !== 'undefined') ? ThemeSwitcher.getPrimaryColor() : '#13304D'
                        });
                    }
                    callback(false);
                }
            },
            error: function() {
                callback(false);
            }
        });
    }

    /**
     * Desbloquea un mensaje en el servidor
     */
    function desbloquearMensaje(mensajeId) {
        $.ajax({
            url: config.urls.desbloquear,
            type: 'POST',
            data: {
                mensaje_id: mensajeId,
                csrfmiddlewaretoken: getCsrfToken()
            }
        });
    }

    /**
     * Marca un mensaje como respondido
     */
    function marcarRespondido(mensajeId, callback) {
        $.ajax({
            url: config.urls.respondido,
            type: 'POST',
            data: {
                mensaje_id: mensajeId,
                csrfmiddlewaretoken: getCsrfToken()
            },
            success: function(response) {
                if (callback) callback(response.success);
                // Actualizar lista
                consultarMensajes();
            }
        });
    }

    /**
     * Ver caso asociado a un mensaje
     */
    function verCaso(mensajeId) {
        var mensaje = state.mensajes.find(function(m) {
            return m.id === mensajeId;
        });

        if (!mensaje) return;

        // Cerrar modal
        elements.modal.classList.remove('show');
        elements.modal.style.display = 'none';

        // Determinar URL de destino
        var url = null;

        // Para movimientos, siempre ir al detalle del caso
        if (mensaje.tipo === 'MOVIMIENTO_PENDIENTE' || mensaje.tipo === 'MOVIMIENTO_ACEPTADO' || mensaje.tipo === 'MOVIMIENTO_RECHAZADO') {
            if (mensaje.datos && mensaje.datos.caso_id) {
                url = '/casos/gestion_casos_verMas/' + mensaje.datos.caso_id + '/';
            }
        } else if (mensaje.accion_url) {
            url = mensaje.accion_url;
        } else if (mensaje.datos && mensaje.datos.caso_id) {
            url = '/casos/gestion_casos_verMas/' + mensaje.datos.caso_id + '/';
        }

        // Para movimientos pendientes, NO marcar como leido (solo ver)
        if (mensaje.tipo === 'MOVIMIENTO_PENDIENTE') {
            if (url) {
                window.location.href = url;
            }
        } else {
            // Para otros tipos, marcar como leido y redirigir
            marcarLeido(mensajeId, function() {
                if (url) {
                    window.location.href = url;
                }
            });
        }
    }

    /**
     * Marca un mensaje como leido (para notificaciones informativas)
     */
    function marcarLeido(mensajeId, callback) {
        $.ajax({
            url: config.urls.descartar,
            type: 'POST',
            data: {
                mensaje_id: mensajeId,
                csrfmiddlewaretoken: getCsrfToken()
            },
            success: function(response) {
                if (response.success) {
                    // Remover de la lista local
                    state.mensajes = state.mensajes.filter(function(m) {
                        return m.id !== mensajeId;
                    });

                    // Actualizar UI
                    actualizarFlotante();

                    // Si no quedan mensajes, cerrar modal
                    if (state.mensajes.length === 0) {
                        cerrarModal();
                    } else {
                        // Actualizar lista en el modal
                        mostrarModalLista();
                    }

                    if (callback) callback(true);
                } else {
                    if (callback) callback(false);
                }
            },
            error: function() {
                if (callback) callback(false);
            }
        });
    }

    /**
     * Acepta un movimiento de caso
     */
    function aceptarMovimiento(mensajeId, event) {
        // Prevenir cualquier comportamiento por defecto
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }

        var mensaje = state.mensajes.find(function(m) {
            return m.id === mensajeId;
        });

        console.log('[MensajesSistema] aceptarMovimiento - mensaje:', mensaje);

        if (!mensaje) {
            Swal.fire({
                title: 'Error',
                text: 'No se encontró el mensaje',
                icon: 'error',
                confirmButtonColor: (typeof ThemeSwitcher !== 'undefined') ? ThemeSwitcher.getPrimaryColor() : '#13304D'
            });
            return false;
        }

        // Verificar datos del movimiento
        var movimientoId = mensaje.datos ? mensaje.datos.movimiento_id : null;
        console.log('[MensajesSistema] movimiento_id:', movimientoId, 'datos:', mensaje.datos);

        if (!movimientoId) {
            Swal.fire({
                title: 'Error',
                text: 'No se encontró la información del movimiento (ID: ' + mensajeId + ')',
                icon: 'error',
                confirmButtonColor: (typeof ThemeSwitcher !== 'undefined') ? ThemeSwitcher.getPrimaryColor() : '#13304D'
            });
            return false;
        }

        // Pausar consulta periódica mientras se muestra el diálogo
        if (state.intervalId) {
            clearInterval(state.intervalId);
            state.intervalId = null;
        }

        // Cerrar el modal de mensajes para que no interfiera con SweetAlert
        elements.modal.classList.remove('show');

        Swal.fire({
            title: 'Aceptar Caso',
            text: '¿Está seguro de aceptar el caso ' + (mensaje.datos.caso_codigo || '') + ' en su sector?',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: '<i class="fa fa-check"></i> Aceptar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#28a745',
            cancelButtonColor: '#6c757d'
        }).then(function(result) {
            if (result.isConfirmed) {
                console.log('[MensajesSistema] Enviando petición para aceptar movimiento:', movimientoId);
                $.ajax({
                    url: '/casos/gestion_legajos_movimientos_confirmar',
                    type: 'POST',
                    data: {
                        id: movimientoId,
                        csrfmiddlewaretoken: getCsrfToken()
                    },
                    success: function(response) {
                        console.log('[MensajesSistema] Respuesta aceptar movimiento:', response);
                        if (response.status) {
                            Swal.fire({
                                title: 'Caso Aceptado',
                                text: 'El caso ha sido transferido a su sector exitosamente.',
                                icon: 'success',
                                confirmButtonColor: (typeof ThemeSwitcher !== 'undefined') ? ThemeSwitcher.getPrimaryColor() : '#13304D'
                            });

                            // Remover mensaje de la lista
                            state.mensajes = state.mensajes.filter(function(m) {
                                return m.id !== mensajeId;
                            });
                            actualizarFlotante();

                            if (state.mensajes.length === 0) {
                                cerrarModal();
                            } else {
                                mostrarModalLista();
                            }

                            // Reiniciar consulta periódica
                            state.intervalId = setInterval(consultarMensajes, config.intervaloConsulta);
                        } else {
                            Swal.fire({
                                title: 'Error',
                                text: response.error || 'No se pudo aceptar el movimiento',
                                icon: 'error',
                                confirmButtonColor: (typeof ThemeSwitcher !== 'undefined') ? ThemeSwitcher.getPrimaryColor() : '#13304D'
                            });
                            // Reiniciar consulta periódica
                            state.intervalId = setInterval(consultarMensajes, config.intervaloConsulta);
                        }
                    },
                    error: function() {
                        Swal.fire({
                            title: 'Error',
                            text: 'Ocurrió un error al procesar la solicitud',
                            icon: 'error',
                            confirmButtonColor: (typeof ThemeSwitcher !== 'undefined') ? ThemeSwitcher.getPrimaryColor() : '#13304D'
                        });
                        // Reiniciar consulta periódica
                        state.intervalId = setInterval(consultarMensajes, config.intervaloConsulta);
                    }
                });
            } else {
                // Si el usuario cancela, reiniciar consulta periódica
                state.intervalId = setInterval(consultarMensajes, config.intervaloConsulta);
            }
        });

        return false;
    }

    /**
     * Rechaza un movimiento de caso
     */
    function rechazarMovimiento(mensajeId, event) {
        // Prevenir cualquier comportamiento por defecto
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }

        var mensaje = state.mensajes.find(function(m) {
            return m.id === mensajeId;
        });

        console.log('[MensajesSistema] rechazarMovimiento - mensaje:', mensaje);

        if (!mensaje) {
            Swal.fire({
                title: 'Error',
                text: 'No se encontró el mensaje',
                icon: 'error',
                confirmButtonColor: (typeof ThemeSwitcher !== 'undefined') ? ThemeSwitcher.getPrimaryColor() : '#13304D'
            });
            return false;
        }

        var movimientoId = mensaje.datos ? mensaje.datos.movimiento_id : null;
        console.log('[MensajesSistema] movimiento_id:', movimientoId);

        if (!movimientoId) {
            Swal.fire({
                title: 'Error',
                text: 'No se encontró la información del movimiento',
                icon: 'error',
                confirmButtonColor: (typeof ThemeSwitcher !== 'undefined') ? ThemeSwitcher.getPrimaryColor() : '#13304D'
            });
            return false;
        }

        // Pausar consulta periódica mientras se muestra el diálogo
        if (state.intervalId) {
            clearInterval(state.intervalId);
            state.intervalId = null;
        }

        // Cerrar el modal de mensajes para que no interfiera con SweetAlert
        elements.modal.classList.remove('show');

        Swal.fire({
            title: 'Rechazar Caso',
            text: '¿Está seguro de rechazar el caso ' + (mensaje.datos.caso_codigo || '') + '? El caso permanecerá en el sector de origen.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: '<i class="fa fa-times"></i> Rechazar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6c757d'
        }).then(function(result) {
            if (result.isConfirmed) {
                console.log('[MensajesSistema] Enviando petición para rechazar movimiento:', movimientoId);
                $.ajax({
                    url: '/casos/gestion_legajos_movimientos_cancelar',
                    type: 'POST',
                    data: {
                        id: movimientoId,
                        csrfmiddlewaretoken: getCsrfToken()
                    },
                    success: function(response) {
                        console.log('[MensajesSistema] Respuesta rechazar movimiento:', response);
                        if (response.status) {
                            Swal.fire({
                                title: 'Movimiento Rechazado',
                                text: 'El movimiento ha sido rechazado. El caso permanece en el sector de origen.',
                                icon: 'info',
                                confirmButtonColor: (typeof ThemeSwitcher !== 'undefined') ? ThemeSwitcher.getPrimaryColor() : '#13304D'
                            });

                            // Remover mensaje de la lista
                            state.mensajes = state.mensajes.filter(function(m) {
                                return m.id !== mensajeId;
                            });
                            actualizarFlotante();

                            if (state.mensajes.length === 0) {
                                cerrarModal();
                            } else {
                                mostrarModalLista();
                            }

                            // Reiniciar consulta periódica
                            state.intervalId = setInterval(consultarMensajes, config.intervaloConsulta);
                        } else {
                            Swal.fire({
                                title: 'Error',
                                text: response.error || 'No se pudo rechazar el movimiento',
                                icon: 'error',
                                confirmButtonColor: (typeof ThemeSwitcher !== 'undefined') ? ThemeSwitcher.getPrimaryColor() : '#13304D'
                            });
                            // Reiniciar consulta periódica
                            state.intervalId = setInterval(consultarMensajes, config.intervaloConsulta);
                        }
                    },
                    error: function() {
                        Swal.fire({
                            title: 'Error',
                            text: 'Ocurrió un error al procesar la solicitud',
                            icon: 'error',
                            confirmButtonColor: (typeof ThemeSwitcher !== 'undefined') ? ThemeSwitcher.getPrimaryColor() : '#13304D'
                        });
                        // Reiniciar consulta periódica
                        state.intervalId = setInterval(consultarMensajes, config.intervaloConsulta);
                    }
                });
            } else {
                // Si el usuario cancela, reiniciar consulta periódica
                state.intervalId = setInterval(consultarMensajes, config.intervaloConsulta);
            }
        });

        return false;
    }

    /**
     * Escapa HTML para prevenir XSS
     */
    function escapeHtml(text) {
        if (!text) return '';
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Fuerza una consulta de mensajes (útil después de responder)
     */
    function refrescar() {
        consultarMensajes();
    }

    // API pública
    return {
        init: init,
        refrescar: refrescar,
        seleccionarTarea: seleccionarTarea,
        responderTarea: responderTarea,
        declinarTarea: declinarTarea,
        marcarRespondido: marcarRespondido,
        marcarLeido: marcarLeido,
        verCaso: verCaso,
        aceptarMovimiento: aceptarMovimiento,
        rechazarMovimiento: rechazarMovimiento,
        consultarMensajes: consultarMensajes,
        mostrarModalLista: mostrarModalLista,
        limpiarMensajesVistos: limpiarMensajesVistos // Para llamar en logout
    };

})();
