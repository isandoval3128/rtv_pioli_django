# Guía de Despliegue a Producción - RTV Pioli Django

## Resumen de Cambios Implementados

### Nuevas Funcionalidades:
1. **Sistema de Reserva Temporal de Horarios** - Evita conflictos cuando múltiples usuarios seleccionan el mismo horario
2. **Página de Impresión de Turnos Pública** - `/turnero/imprimir/<codigo>/`
3. **Botones móviles para Imprimir/PDF/Compartir** - En páginas de impresión
4. **Scroll automático a resultados** - En consulta de turnos
5. **Mejoras de UI** - Logo con hover en login, WhatsApp deshabilitado temporalmente

---

## Paso 1: Preparar el entorno

### 1.1 Activar entorno virtual en el servidor
```bash
# En Linux/Mac
source venv/bin/activate

# En Windows
venv\Scripts\activate
```

### 1.2 Actualizar código desde repositorio
```bash
git pull origin master
```

---

## Paso 2: Instalar dependencias

### 2.1 Verificar requirements.txt
El archivo `requirements.txt` actual incluye todas las dependencias necesarias:
- Django==6.0.1
- pillow==12.1.0 (para imágenes/QR)
- qrcode==8.2 (generación de códigos QR)
- psycopg2-binary==2.9.11 (PostgreSQL)
- openpyxl==3.1.5 (Excel)
- pandas==2.3.3 (procesamiento de datos)

### 2.2 Instalar dependencias
```bash
pip install -r requirements.txt
```

---

## Paso 3: Ejecutar Migraciones

### 3.1 Verificar migraciones pendientes
```bash
python manage.py showmigrations
```

### 3.2 Aplicar migraciones
```bash
python manage.py migrate
```

### Migraciones importantes del turnero:
- `turnero/0001_initial.py` - Modelos base (Turno, HistorialTurno)
- `turnero/0002_turno_token_expiracion_turno_token_reprogramacion.py` - Tokens para reprogramación
- `turnero/0003_add_reserva_temporal.py` - **NUEVA** Modelo ReservaTemporal para reservas de horarios

---

## Paso 4: Recopilar archivos estáticos

```bash
python manage.py collectstatic --noinput
```

---

## Paso 5: Verificar configuración

### 5.1 Verificar configuración de Email (para envío de confirmaciones)
Asegurarse de que existe un registro en `EmailConfig` con:
- `email_host` - Servidor SMTP
- `email_port` - Puerto (587 para TLS)
- `email_host_user` - Usuario/email
- `email_host_password` - Contraseña
- `email_use_tls` - True
- `default_from_email` - Email remitente

### 5.2 Verificar configuración de talleres
Para que funcione la reserva temporal, cada taller debe tener:
- `ConfiguracionTaller` con `turnos_simultaneos` definido por tipo de vehículo

---

## Paso 6: Reiniciar servicios

### Con Gunicorn:
```bash
sudo systemctl restart gunicorn
```

### Con uWSGI:
```bash
sudo systemctl restart uwsgi
```

### Con Supervisor:
```bash
sudo supervisorctl restart rtv_pioli
```

---

## Paso 7: Verificar funcionamiento

### 7.1 Verificar turnero público
- [ ] Acceder a `/turnero/` - Home del turnero
- [ ] Crear un turno completo (pasos 1-5)
- [ ] Verificar que se envía email de confirmación
- [ ] Verificar que el QR se genera correctamente

### 7.2 Verificar consulta de turnos
- [ ] Acceder a `/turnero/consultar/`
- [ ] Buscar un turno existente
- [ ] Verificar scroll automático a resultados
- [ ] Probar botón "Imprimir" → debe abrir `/turnero/imprimir/<codigo>/`

### 7.3 Verificar impresión
- [ ] En la página de impresión verificar los 3 botones:
  - Imprimir (verde)
  - Guardar PDF (rojo)
  - Compartir (azul) - Solo visible en móviles

### 7.4 Verificar reserva temporal
- [ ] Abrir dos navegadores/pestañas
- [ ] Ir al paso 4 (selección de fecha/hora) en ambos
- [ ] Seleccionar el mismo horario en ambos
- [ ] Verificar que el segundo usuario recibe error de "horario no disponible"

---

## Archivos Nuevos/Modificados

### Archivos Python (turnero/):
- `models.py` - Agregado modelo `ReservaTemporal`
- `views.py` - Agregadas vistas:
  - `reservar_horario_ajax` - Reserva temporal de horarios
  - `imprimir_turno_publico` - Página de impresión pública
- `urls.py` - Nuevas rutas:
  - `/turnero/imprimir/<codigo>/`
  - `/turnero/ajax/reservar-horario/`

### Templates:
- `templates/turnero/imprimir_turno.html` - **NUEVO** Página de impresión
- `templates/turnero/step4_fecha_hora.html` - Sistema de reserva temporal
- `templates/turnero/consultar_turno.html` - Scroll automático a resultados
- `templates/panel/gestion_turnos_imprimir.html` - Botones móviles
- `templates/panel/login.html` - Hover en logo
- `templates/panel/gestion_turnos.html` - WhatsApp deshabilitado

---

## Comandos útiles

### Limpiar reservas temporales expiradas (ejecutar periódicamente)
```bash
python manage.py shell -c "from turnero.models import ReservaTemporal; ReservaTemporal.limpiar_expiradas()"
```

### Verificar estado de migraciones
```bash
python manage.py showmigrations turnero
```

### Verificar errores de configuración
```bash
python manage.py check
```

---

## Configuración de Cron (Opcional pero recomendado)

Para limpiar reservas temporales expiradas automáticamente:

```bash
# Editar crontab
crontab -e

# Agregar línea (ejecutar cada 5 minutos)
*/5 * * * * cd /path/to/rtv_pioli_django && /path/to/venv/bin/python manage.py shell -c "from turnero.models import ReservaTemporal; ReservaTemporal.limpiar_expiradas()"
```

---

## Rollback (si es necesario)

### Revertir migración de ReservaTemporal:
```bash
python manage.py migrate turnero 0002_turno_token_expiracion_turno_token_reprogramacion
```

### Revertir código:
```bash
git checkout HEAD~1 -- turnero/
git checkout HEAD~1 -- templates/turnero/
git checkout HEAD~1 -- templates/panel/
```

---

## Resumen de Comandos para Despliegue Rápido

```bash
# 1. Activar entorno virtual
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 2. Actualizar código
git pull origin master

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Aplicar migraciones
python manage.py migrate

# 5. Recopilar estáticos
python manage.py collectstatic --noinput

# 6. Reiniciar servicio
sudo systemctl restart gunicorn
```

---

## Contacto y Soporte

Para problemas durante el despliegue, verificar:
1. Logs de Django: `tail -f /var/log/gunicorn/error.log`
2. Logs de Nginx: `tail -f /var/log/nginx/error.log`
3. Estado de servicios: `sudo systemctl status gunicorn`
