/**
 * Script para mejorar la experiencia de agregar fechas no laborables
 */

(function() {
    'use strict';

    // Esperar a que el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initFechasNoLaborables);
    } else {
        initFechasNoLaborables();
    }

    function initFechasNoLaborables() {
        const textarea = document.querySelector('#id_fechas_no_laborables_text');

        if (!textarea) {
            return;
        }

        console.log('Inicializando gestor de fechas no laborables');

        // Crear contenedor de ayuda
        const helpDiv = document.createElement('div');
        helpDiv.style.cssText = 'margin-top: 10px; padding: 10px; background: #e3f2fd; border-left: 4px solid #2196F3; border-radius: 4px;';
        helpDiv.innerHTML = `
            <strong style="color: #1976D2;"><i class="fas fa-info-circle"></i> Ayuda:</strong>
            <ul style="margin: 5px 0 0 0; padding-left: 20px; color: #0d47a1;">
                <li>Ingresá cada fecha en una línea nueva</li>
                <li>Formato requerido: <strong>YYYY-MM-DD</strong> (Ej: 2024-12-25)</li>
                <li>Las fechas duplicadas se eliminarán automáticamente</li>
                <li>Las fechas se ordenarán de forma automática</li>
            </ul>
        `;

        // Insertar ayuda después del textarea
        textarea.parentNode.insertBefore(helpDiv, textarea.nextSibling);

        // Crear botón para agregar fecha actual
        const btnContainer = document.createElement('div');
        btnContainer.style.cssText = 'margin-top: 10px;';

        const btnAgregarHoy = document.createElement('button');
        btnAgregarHoy.type = 'button';
        btnAgregarHoy.className = 'button';
        btnAgregarHoy.innerHTML = '<i class="fas fa-calendar-plus"></i> Agregar Hoy';
        btnAgregarHoy.style.cssText = 'margin-right: 10px;';

        const btnOrdenar = document.createElement('button');
        btnOrdenar.type = 'button';
        btnOrdenar.className = 'button';
        btnOrdenar.innerHTML = '<i class="fas fa-sort-amount-down"></i> Ordenar y Limpiar';

        btnContainer.appendChild(btnAgregarHoy);
        btnContainer.appendChild(btnOrdenar);
        helpDiv.appendChild(btnContainer);

        // Evento: Agregar fecha de hoy
        btnAgregarHoy.addEventListener('click', function() {
            const hoy = new Date();
            const fechaStr = hoy.toISOString().split('T')[0];

            const valor = textarea.value.trim();
            if (valor) {
                textarea.value = valor + '\n' + fechaStr;
            } else {
                textarea.value = fechaStr;
            }

            // Mostrar notificación
            mostrarNotificacion('Fecha de hoy agregada: ' + fechaStr, 'success');
        });

        // Evento: Ordenar y limpiar
        btnOrdenar.addEventListener('click', function() {
            const texto = textarea.value.trim();
            if (!texto) {
                mostrarNotificacion('No hay fechas para ordenar', 'warning');
                return;
            }

            const lineas = texto.split('\n');
            const fechasValidas = new Set();
            const fechasInvalidas = [];

            lineas.forEach(function(linea) {
                linea = linea.trim();
                if (!linea) return;

                // Validar formato YYYY-MM-DD
                if (/^\d{4}-\d{2}-\d{2}$/.test(linea)) {
                    // Validar que sea una fecha real
                    const partes = linea.split('-');
                    const fecha = new Date(partes[0], partes[1] - 1, partes[2]);

                    if (fecha.getFullYear() == partes[0] &&
                        fecha.getMonth() == partes[1] - 1 &&
                        fecha.getDate() == partes[2]) {
                        fechasValidas.add(linea);
                    } else {
                        fechasInvalidas.push(linea);
                    }
                } else {
                    fechasInvalidas.push(linea);
                }
            });

            // Ordenar fechas
            const fechasOrdenadas = Array.from(fechasValidas).sort();
            textarea.value = fechasOrdenadas.join('\n');

            // Notificar
            if (fechasInvalidas.length > 0) {
                mostrarNotificacion(
                    'Fechas ordenadas. Se encontraron ' + fechasInvalidas.length + ' fechas inválidas que fueron eliminadas.',
                    'warning'
                );
            } else {
                mostrarNotificacion(
                    'Fechas ordenadas correctamente. Total: ' + fechasOrdenadas.length,
                    'success'
                );
            }
        });

        // Validación en tiempo real
        textarea.addEventListener('blur', function() {
            const texto = textarea.value.trim();
            if (!texto) return;

            const lineas = texto.split('\n');
            let tieneErrores = false;

            lineas.forEach(function(linea) {
                linea = linea.trim();
                if (!linea) return;

                if (!/^\d{4}-\d{2}-\d{2}$/.test(linea)) {
                    tieneErrores = true;
                }
            });

            if (tieneErrores) {
                mostrarNotificacion(
                    'Algunas fechas tienen formato incorrecto. Usá el botón "Ordenar y Limpiar" para validar.',
                    'warning'
                );
            }
        });
    }

    function mostrarNotificacion(mensaje, tipo) {
        // Crear notificación temporal
        const notif = document.createElement('div');
        notif.style.cssText = 'position: fixed; top: 20px; right: 20px; padding: 15px 20px; border-radius: 4px; z-index: 9999; box-shadow: 0 2px 8px rgba(0,0,0,0.2); font-weight: 500;';

        if (tipo === 'success') {
            notif.style.background = '#4caf50';
            notif.style.color = 'white';
        } else if (tipo === 'warning') {
            notif.style.background = '#ff9800';
            notif.style.color = 'white';
        } else {
            notif.style.background = '#2196F3';
            notif.style.color = 'white';
        }

        notif.textContent = mensaje;
        document.body.appendChild(notif);

        // Remover después de 3 segundos
        setTimeout(function() {
            notif.style.transition = 'opacity 0.3s';
            notif.style.opacity = '0';
            setTimeout(function() {
                document.body.removeChild(notif);
            }, 300);
        }, 3000);
    }
})();
