#!/bin/bash
# ==============================================
# Script de Despliegue a Producción - RTV Pioli
# ==============================================
# Uso: ./deploy.sh
# ==============================================

set -e  # Detener si hay errores

echo "=============================================="
echo "  DESPLIEGUE A PRODUCCIÓN - RTV PIOLI"
echo "=============================================="
echo ""

# Colores para mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # Sin color

# Función para mostrar mensajes
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    log_error "No se encontró manage.py. Asegurate de ejecutar este script desde el directorio del proyecto."
    exit 1
fi

# Paso 1: Actualizar código desde repositorio
echo ""
log_info "Paso 1: Actualizando código desde repositorio..."
git pull origin main
echo ""

# Paso 2: Activar entorno virtual (si existe)
if [ -d "venv" ]; then
    log_info "Paso 2: Activando entorno virtual..."
    source venv/bin/activate
elif [ -d "env" ]; then
    log_info "Paso 2: Activando entorno virtual..."
    source env/bin/activate
else
    log_warn "No se encontró entorno virtual (venv o env). Continuando sin activar..."
fi
echo ""

# Paso 3: Instalar dependencias
log_info "Paso 3: Instalando dependencias..."
pip install -r requirements.txt
echo ""

# Paso 4: Ejecutar migraciones
log_info "Paso 4: Ejecutando migraciones de base de datos..."
python manage.py migrate --noinput
echo ""

# Paso 5: Recopilar archivos estáticos
log_info "Paso 5: Recopilando archivos estáticos..."
python manage.py collectstatic --noinput
echo ""

# Paso 6: Inicializar menú del panel (grupos, perfiles y menús)
log_info "Paso 6: Inicializando menú del panel..."
python manage.py inicializar_menu_produccion
echo ""

# Paso 7: Limpiar reservas temporales expiradas
log_info "Paso 7: Limpiando reservas temporales expiradas..."
python manage.py shell -c "from turnero.models import ReservaTemporal; ReservaTemporal.limpiar_expiradas()" 2>/dev/null || log_warn "No se pudo limpiar reservas temporales (puede que el modelo no exista aún)"
echo ""

# Paso 8: Verificar configuración
log_info "Paso 8: Verificando configuración de Django..."
python manage.py check
echo ""

# Paso 9: Reiniciar servicio (detectar cuál está disponible)
log_info "Paso 9: Reiniciando servicio web..."
if command -v systemctl &> /dev/null; then
    if systemctl is-active --quiet gunicorn; then
        sudo systemctl restart gunicorn
        log_info "Gunicorn reiniciado correctamente."
    elif systemctl is-active --quiet uwsgi; then
        sudo systemctl restart uwsgi
        log_info "uWSGI reiniciado correctamente."
    elif command -v supervisorctl &> /dev/null; then
        sudo supervisorctl restart rtv_pioli
        log_info "Supervisor reiniciado correctamente."
    else
        log_warn "No se detectó servicio web activo (gunicorn/uwsgi/supervisor)."
        log_warn "Reiniciá el servicio manualmente."
    fi
else
    log_warn "systemctl no disponible. Reiniciá el servicio manualmente."
fi

echo ""
echo "=============================================="
echo -e "${GREEN}  DESPLIEGUE COMPLETADO EXITOSAMENTE${NC}"
echo "=============================================="
echo ""
echo "Verificá que todo funcione correctamente:"
echo "  - Acceder a /turnero/"
echo "  - Crear un turno de prueba"
echo "  - Verificar el panel de administración"
echo ""
