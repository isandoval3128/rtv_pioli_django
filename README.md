# RTV Pioli Django

Proyecto web profesional desarrollado con Django.

## Descripción
Sistema para gestión y presentación de servicios, portfolio y contacto, con diseño responsivo y despliegue en producción.

## Características principales
- Backend en Django
- Frontend con Bootstrap y CSS personalizado
- Gestión de servicios, portfolio y equipo
- Formulario de contacto
- Despliegue con Gunicorn
- Configuración profesional de .gitignore y manejo de migraciones

## Instalación y despliegue
1. Clona el repositorio:
   ```sh
git clone https://github.com/isandoval3128/rtv_pioli_django.git
```
2. Instala dependencias:
   ```sh
pip install -r requirements.txt
```
3. Realiza migraciones:
   ```sh
python manage.py migrate
```
4. Recopila archivos estáticos:
   ```sh
python manage.py collectstatic
```
5. Arranca el servidor:
   ```sh
gunicorn config.wsgi:application
```

## Estructura del proyecto
- `core/` - App principal
- `templates/` - Archivos HTML
- `static/` - Archivos estáticos
- `media/` - Archivos subidos
- `config/` - Configuración Django

## Contribución
1. Haz un fork del repositorio
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Realiza tus cambios y haz commit
4. Envía un pull request

## Licencia
Este proyecto está bajo la licencia MIT.
