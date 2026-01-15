/**
 * Admin de Taller - Manejo dinámico de campos según selección de planta
 */

(function() {
    'use strict';

    // Esperar a que el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTallerAdmin);
    } else {
        initTallerAdmin();
    }

    function initTallerAdmin() {
        // Buscar el campo de planta (puede ser select o autocomplete)
        const plantaField = document.querySelector('#id_planta');
        const nombreField = document.querySelector('#id_nombre');

        if (!plantaField) {
            console.log('Campo planta no encontrado');
            return;
        }

        console.log('Inicializando admin de Taller - control de campos según planta');

        // Función para obtener el nombre de la planta seleccionada
        function getNombrePlanta() {
            const plantaId = plantaField.value;

            if (!plantaId) {
                return null;
            }

            // Si es un select normal, obtener el texto de la opción seleccionada
            const selectedOption = plantaField.querySelector(`option[value="${plantaId}"]`);
            if (selectedOption) {
                return selectedOption.textContent.trim();
            }

            // Si es autocomplete, buscar en el span que muestra el texto
            const autocompleteText = document.querySelector('.select2-selection__rendered');
            if (autocompleteText && autocompleteText.textContent.trim() !== '---------') {
                return autocompleteText.textContent.trim();
            }

            return null;
        }

        // Función para actualizar el campo nombre
        function actualizarNombreTaller() {
            if (!nombreField) return;

            const plantaId = plantaField.value;

            if (plantaId) {
                // Hay planta seleccionada - obtener su nombre
                const nombrePlanta = getNombrePlanta();

                if (nombrePlanta) {
                    // Actualizar el campo nombre con el nombre de la planta
                    nombreField.value = nombrePlanta;
                    nombreField.style.backgroundColor = '#e8f5e9';
                    nombreField.setAttribute('readonly', 'readonly');

                    console.log('Campo nombre actualizado con:', nombrePlanta);
                } else {
                    // Si no podemos obtener el nombre del select, hacer una petición AJAX
                    fetch('/ubicacion/api/' + plantaId + '/')
                        .then(response => response.json())
                        .then(data => {
                            if (data.nombre) {
                                nombreField.value = data.nombre;
                                nombreField.style.backgroundColor = '#e8f5e9';
                                nombreField.setAttribute('readonly', 'readonly');
                                console.log('Campo nombre actualizado vía API con:', data.nombre);
                            }
                        })
                        .catch(error => {
                            console.error('Error al obtener datos de la planta:', error);
                        });
                }
            } else {
                // No hay planta - permitir edición del nombre
                nombreField.style.backgroundColor = '';
                nombreField.removeAttribute('readonly');
            }
        }

        // Función para mostrar/ocultar campos según si hay planta
        function toggleCamposPropios() {
            const plantaSeleccionada = plantaField.value;
            const fieldset = document.querySelector('.datos-propios-taller');

            if (!fieldset) {
                console.log('Fieldset de datos propios no encontrado');
                return;
            }

            // Actualizar el campo nombre
            actualizarNombreTaller();

            if (plantaSeleccionada) {
                // HAY planta seleccionada - ocultar y deshabilitar campos propios
                console.log('Planta seleccionada:', plantaSeleccionada, '- Ocultando campos propios');

                // Colapsar el fieldset si está expandido
                if (!fieldset.classList.contains('collapsed')) {
                    // Buscar el toggle del collapse
                    const collapseToggle = fieldset.querySelector('.collapse-toggle');
                    if (collapseToggle) {
                        collapseToggle.click();
                    }
                }

                // Deshabilitar campos para que no se envíen
                const inputs = fieldset.querySelectorAll('input, select, textarea');
                inputs.forEach(input => {
                    if (input.id !== 'id_planta') {  // No deshabilitar el campo planta
                        input.disabled = true;
                        input.style.backgroundColor = '#f5f5f5';
                    }
                });

                // Agregar mensaje informativo
                let mensaje = fieldset.querySelector('.planta-info-message');
                if (!mensaje) {
                    mensaje = document.createElement('div');
                    mensaje.className = 'planta-info-message';
                    mensaje.style.cssText = 'background: #e3f2fd; border-left: 4px solid #2196F3; padding: 12px; margin: 10px 0; border-radius: 4px; color: #0d47a1;';
                    mensaje.innerHTML = '<strong><i class="fas fa-info-circle"></i> Usando datos de la planta seleccionada</strong><br>Los campos de ubicación y contacto se tomarán automáticamente de la planta.';
                    fieldset.insertBefore(mensaje, fieldset.firstChild);
                }

            } else {
                // NO hay planta - habilitar campos propios
                console.log('Sin planta seleccionada - Habilitando campos propios');

                // Habilitar campos
                const inputs = fieldset.querySelectorAll('input, select, textarea');
                inputs.forEach(input => {
                    input.disabled = false;
                    input.style.backgroundColor = '';
                });

                // Remover mensaje informativo
                const mensaje = fieldset.querySelector('.planta-info-message');
                if (mensaje) {
                    mensaje.remove();
                }

                // Expandir el fieldset si está colapsado
                if (fieldset.classList.contains('collapsed')) {
                    const collapseToggle = fieldset.querySelector('.collapse-toggle');
                    if (collapseToggle) {
                        collapseToggle.click();
                    }
                }
            }
        }

        // Ejecutar al cargar la página
        toggleCamposPropios();

        // Ejecutar cuando cambie la selección de planta
        plantaField.addEventListener('change', toggleCamposPropios);

        // Para autocomplete, también escuchar el evento cuando se selecciona
        plantaField.addEventListener('input', function() {
            // Esperar un momento para que se complete la selección
            setTimeout(toggleCamposPropios, 100);
        });

        // Escuchar eventos de Django autocomplete
        if (window.django && window.django.jQuery) {
            window.django.jQuery(plantaField).on('select2:select select2:unselect', function() {
                setTimeout(toggleCamposPropios, 100);
            });
        }
    }
})();
