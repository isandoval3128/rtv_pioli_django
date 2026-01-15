function convertirFecha(fechaISO) {
    // Crea un objeto de fecha a partir de la cadena ISO
    const fecha = new Date(fechaISO);

    // Nombres de meses abreviados en español
    const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

    // Obtiene los componentes de la fecha
    const dia = String(fecha.getUTCDate()).padStart(2, '0');
    const mes = meses[fecha.getUTCMonth()];
    const anio = fecha.getUTCFullYear();

    // Construye la cadena con el formato: "DD Mmm YYYY" (ej: "15 Ene 2025")
    const fechaFormateada = `${dia} ${mes} ${anio}`;

    return fechaFormateada;
}

function convertirFechaHora(fechaISO) {
    // Crea un objeto de fecha a partir de la cadena ISO
    const fecha = new Date(fechaISO);

    // Nombres de meses abreviados en español
    const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

    // Obtiene los componentes de la fecha
    const dia = String(fecha.getUTCDate()).padStart(2, '0');
    const mes = meses[fecha.getUTCMonth()];
    const anio = fecha.getUTCFullYear();

    // Obtiene los componentes de la hora
    const horas = String(fecha.getUTCHours()).padStart(2, '0');
    const minutos = String(fecha.getUTCMinutes()).padStart(2, '0');

    // Construye la cadena con el formato: "DD Mmm YYYY HH:mm" (ej: "15 Ene 2025 14:30")
    const fechaFormateada = `${dia} ${mes} ${anio} ${horas}:${minutos}`;

    return fechaFormateada;
}

function cargarCKEditor(id){
    CKEDITOR.replace(id, {
        height: 300,
        toolbar: [
           { name: 'basicstyles', items: ['Bold', 'Italic', 'Underline', 'Strike'] },
           { name: 'paragraph', items: ['BulletedList', 'NumberedList'] },
           { name: 'insert', items: ['Table'] },
           { name: 'tools', items: ['Maximize'] },
           { name: 'clipboard', items: ['Undo', 'Redo'] }
        ]
    });

    // cuando cambia el contenido, actualiza el textarea automáticamente
    CKEDITOR.instances[id].on('change', function() {
        CKEDITOR.instances[id].updateElement();
    });
}

// Solo registrar el evento si CKEDITOR está definido
if (typeof CKEDITOR !== 'undefined') {
  CKEDITOR.on('instanceReady', function (ev) {
    var editor = ev.editor;
    function sync() {
      editor.updateElement();
      $('#' + editor.name).trigger('input');
    }
    editor.on('change', sync);
    editor.on('key', sync);
    editor.on('afterPaste', sync);
    editor.on('blur', sync);
  });
}

function syncEditors() {
  if (window.CKEDITOR && CKEDITOR.instances) {
    Object.values(CKEDITOR.instances).forEach(inst => inst.updateElement());
  }
  if (window.__ck5Editors) {
    for (const [fieldId, editor] of Object.entries(window.__ck5Editors)) {
      const textarea = document.getElementById(fieldId);
      if (textarea) textarea.value = editor.getData();
    }
  }
}

function cargarSelect2(modal) {
  // Destruir instancias existentes de Select2 para evitar conflictos con el scroll
  $(modal).find('.select2').each(function() {
    if ($(this).hasClass('select2-hidden-accessible')) {
      $(this).select2('destroy');
    }
  });

  // Inicializar Select2 con el dropdownParent correcto para que funcione dentro del modal
  $(modal).find('.select2').select2({
    theme: 'bootstrap4',
    dropdownParent: $(modal),
    width: '100%',
  });

  // Asegurar que el scroll del modal funcione después de cerrar el dropdown de Select2
  $(modal).find('.select2').on('select2:close', function() {
    // Restaurar el scroll del modal body después de cerrar Select2
    var $modalBody = $(modal).find('.modal-body');
    if ($modalBody.length) {
      $modalBody.css('overflow-y', 'auto');
    }
  });

}

function validarPassword(cadena) {
  const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.;])[A-Za-z\d!@#$%^&*(),.;]{8,}$/;
  return regex.test(cadena);
}


function vistaDocumento(archivo, csrf_token) {
    const ext = archivo.split('.').pop().toLowerCase();
    let modalId = 'modal-fullscreen';

    const modalElement = document.getElementById(modalId);
    const modalInstance = new bootstrap.Modal(modalElement);
    const url = `${archivo}`;
    var contenido = '';

        if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'bmp', 'tiff', 'tif', 'webp'].includes(ext)) {
            contenido = `<img src="${url}" class="img-fluid" style="max-height:90vh; object-fit:contain; display:block; margin:0 auto;">`;
        } else if (ext === 'pdf') {
            contenido = `<div class="ratio ratio-16x9">
                            <iframe src="${url}" frameborder="0" allowfullscreen></iframe>
                         </div>`;
        }

    var formData = new FormData();

  formData.append('contenido', contenido);
  formData.append('csrfmiddlewaretoken', csrf_token);

  $.ajax({
    url: 'casos/gestion_legajoGrommingTareas_documento_verMas',
    type: 'POST',
    data: formData,
    processData: false,
    contentType: false,
    success: function (data) {

            var formHTML = data.html_form;

            $("#modal-fullscreen .modal-content").html(formHTML);
            $("#modal-fullscreen").modal({backdrop: 'static', keyboard: false}).modal("show");

    }
  });
}
