# Guia de Despliegue a Produccion - RTV Pioli Django

## Resumen de Cambios Implementados (v1.6)

### Nuevas Funcionalidades (v1.6):
1. **Gestion Sitio** - Panel con 9 pestanas para configurar el sitio web publico (general, hero, header, fondo, contacto, servicios, redes sociales, tipografia, footer)
2. **Configuraciones del Turnero** - Panel con 5 pestanas para parametrizar talleres, tipos de tramite, capacidad, fechas no laborables y franjas anuladas
3. **Feriados nacionales rapidos** - Botones para agregar feriados argentinos con un click
4. **Motivos predefinidos en franjas anuladas** - Select2 con opciones comunes (mantenimiento, capacitacion, etc.)
5. **Reorganizacion de menus** - Configuraciones movido al menu Turnos, Configuracion IA al final de su menu
6. **Fix menu lateral** - Desactivacion de metisMenu para evitar bloqueo de clicks

### Funcionalidades Anteriores (v1.4-v1.5):
1. **Flujo de 4 pasos** - Reducido de 5 a 4 pasos
2. **2 tipos de tramite** - Unificados a Vehiculos Livianos y Vehiculos Pesados
3. **Intervalos diferenciados** - Livianos: 10 min / 2 simultaneos. Pesados: 20 min / 1 simultaneo
4. **Franjas horarias anuladas** - Bloqueo de rangos de horarios especificos por dia y taller
5. **Soporte DNI/CUIT** - Busqueda y registro de clientes por DNI o CUIT
6. **KB Asistente IA** - Base de conocimiento con tarifas y horarios
7. **Sistema de Reserva Temporal de Horarios** - Evita conflictos de seleccion simultanea

### Pasos Post-Deploy:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py inicializar_menu_produccion --force
sudo systemctl restart gunicorn
```

---

## Paso 1: Preparar el entorno

### 1.1 Activar entorno virtual en el servidor
```bash
# En Linux/Mac
source venv/bin/activate

# En Windows
venv\Scripts\activate
```

### 1.2 Actualizar codigo desde repositorio
```bash
git pull origin master
```

---

## Paso 2: Instalar dependencias

### 2.1 Verificar requirements.txt
El archivo `requirements.txt` actual incluye todas las dependencias necesarias:
- Django==6.0.1
- pillow==12.1.0 (para imagenes/QR)
- qrcode==8.2 (generacion de codigos QR)
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

### Migraciones nuevas v1.4:

#### talleres/
- `0018_unificar_tipos_tramite.py` - Activa solo 2 TipoVehiculo (Livianos y Pesados), desactiva el resto
- `0019_ajustar_intervalos_lineas.py` - Configura Livianos=10min/2 simultaneos, Pesados=20min/1 simultaneo
- `0020_franja_anulada.py` - Nuevo modelo FranjaAnulada (taller, fecha, hora_inicio, hora_fin, motivo, status)

#### asistente/
- `0011_actualizar_kb_tarifas_horarios.py` - Actualiza system_prompt del asistente y crea 2 DocumentoKB (horarios y tarifas)

#### turnero/ (anteriores)
- `0001_initial.py` - Modelos base (Turno, HistorialTurno)
- `0002_turno_token_expiracion_turno_token_reprogramacion.py` - Tokens para reprogramacion
- `0003_add_reserva_temporal.py` - Modelo ReservaTemporal para reservas de horarios

---

## Paso 4: Recopilar archivos estaticos

```bash
python manage.py collectstatic --noinput
```

---

## Paso 5: Verificar configuracion

### 5.1 Verificar configuracion de Email (para envio de confirmaciones)
Asegurarse de que existe un registro en `EmailConfig` con:
- `email_host` - Servidor SMTP
- `email_port` - Puerto (587 para TLS)
- `email_host_user` - Usuario/email
- `email_host_password` - Contrasena
- `email_use_tls` - True
- `default_from_email` - Email remitente

> **Nota v1.4:** Los emails ahora incluyen headers Message-ID, X-Mailer y Precedence para mejorar entregabilidad en Hotmail/Outlook. Si los emails siguen sin llegar, verificar SPF/DKIM en el DNS del dominio remitente.

### 5.2 Verificar configuracion de talleres
Para que funcione correctamente:
- `ConfiguracionTaller` con `turnos_simultaneos` e `intervalo_minutos` por tipo de vehiculo
- Las migraciones 0018/0019 configuran automaticamente los intervalos correctos
- Verificar que existan exactamente 2 TipoVehiculo activos (Livianos y Pesados)

### 5.3 Verificar Asistente IA
- Verificar que el system_prompt fue actualizado (prioriza info de pagina web y KB)
- Verificar que existen 2 DocumentoKB activos: "Horarios de atencion por planta" y "Tarifas y tipos de tramite RTO"

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

### 7.1 Verificar turnero publico
- [ ] Acceder a `/turnero/` - Home del turnero
- [ ] Verificar que aparecen botones por cada planta activa
- [ ] Seleccionar planta → verificar que muestra 2 tipos de tramite (Livianos/Pesados)
- [ ] Verificar leyenda informativa al seleccionar tramite
- [ ] Crear un turno completo (4 pasos)
- [ ] Verificar busqueda por CUIT en Paso 1
- [ ] Verificar que acepta patentes de motos en Paso 2
- [ ] Verificar que se envia email de confirmacion
- [ ] Verificar que el QR se genera correctamente

### 7.2 Verificar consulta de turnos
- [ ] Acceder a `/turnero/consultar/`
- [ ] Buscar un turno existente por patente
- [ ] Verificar scroll automatico a resultados
- [ ] Probar boton "Imprimir" → debe abrir `/turnero/imprimir/<codigo>/`

### 7.3 Verificar impresion
- [ ] Verificar que el **logo de RTV Pioli** aparece en el encabezado
- [ ] En la pagina de impresion verificar los 3 botones:
  - Imprimir (verde)
  - Guardar PDF (rojo)
  - Compartir (azul) - Solo visible en moviles

### 7.4 Verificar reserva temporal
- [ ] Abrir dos navegadores/pestanas
- [ ] Ir al paso 3 (seleccion de fecha/hora) en ambos
- [ ] Seleccionar el mismo horario en ambos
- [ ] Verificar que el segundo usuario recibe error de "horario no disponible"

### 7.5 Verificar franjas horarias anuladas
- [ ] Crear una FranjaAnulada desde el admin para un taller/fecha/rango de hora
- [ ] Verificar que los horarios dentro de la franja no aparecen como disponibles

### 7.6 Verificar email en Hotmail
- [ ] Crear un turno con email @hotmail.com u @outlook.com
- [ ] Verificar que el email llega correctamente (revisar spam si es necesario)

---

## Archivos Nuevos/Modificados (v1.4)

### Archivos Python:

#### turnero/
- `views.py` - Nueva `SeleccionarTramiteView`, flujo de 4 pasos, busqueda DNI/CUIT, filtro franjas anuladas
- `forms.py` - Tipo documento DNI/CUIT, validacion patentes motos
- `urls.py` - Nueva ruta `/planta/<int:taller_id>/`
- `utils.py` - Refactorizado envio email con headers para Hotmail

#### talleres/
- `models.py` - Nuevo modelo `FranjaAnulada`
- `admin.py` - Registrado `FranjaAnuladaAdmin`
- `migrations/0018_unificar_tipos_tramite.py` - Data migration
- `migrations/0019_ajustar_intervalos_lineas.py` - Data migration
- `migrations/0020_franja_anulada.py` - Schema migration

#### asistente/
- `migrations/0011_actualizar_kb_tarifas_horarios.py` - Data migration

### Templates:
- `templates/turnero/home.html` - Botones por planta, 4 pasos en timeline
- `templates/turnero/base.html` - Sidebar con 4 pasos
- `templates/turnero/seleccionar_tramite.html` - **NUEVO** Pre-seleccion de tramite
- `templates/turnero/imprimir_turno.html` - Logo en header

---

## Comandos utiles

### Limpiar reservas temporales expiradas (ejecutar periodicamente)
```bash
python manage.py shell -c "from turnero.models import ReservaTemporal; ReservaTemporal.limpiar_expiradas()"
```

### Verificar estado de migraciones
```bash
python manage.py showmigrations talleres asistente turnero
```

### Verificar errores de configuracion
```bash
python manage.py check
```

---

## Configuracion de Cron (Opcional pero recomendado)

Para limpiar reservas temporales expiradas automaticamente:

```bash
# Editar crontab
crontab -e

# Agregar linea (ejecutar cada 5 minutos)
*/5 * * * * cd /path/to/rtv_pioli_django && /path/to/venv/bin/python manage.py shell -c "from turnero.models import ReservaTemporal; ReservaTemporal.limpiar_expiradas()"
```

---

## Rollback (si es necesario)

### Revertir migraciones v1.4:
```bash
# Revertir franjas anuladas
python manage.py migrate talleres 0017_taller_email_operador

# Revertir KB asistente
python manage.py migrate asistente 0010_add_email_cliente_derivacion
```

### Revertir codigo:
```bash
git checkout HEAD~1 -- turnero/ talleres/ asistente/ templates/
```

---

## Resumen de Comandos para Despliegue Rapido

```bash
# 1. Activar entorno virtual
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 2. Actualizar codigo
git pull origin master

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Aplicar migraciones
python manage.py migrate

# 5. Recopilar estaticos
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
