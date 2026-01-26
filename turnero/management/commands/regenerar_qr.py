"""
Comando de Django para regenerar los códigos QR de los turnos existentes.
Útil cuando se actualiza el formato del QR o se implementa el sistema de tokens.

Uso:
    python manage.py regenerar_qr                    # Regenera todos los QR
    python manage.py regenerar_qr --pendientes       # Solo turnos pendientes
    python manage.py regenerar_qr --codigo TRN-ABC   # Un turno específico
    python manage.py regenerar_qr --dry-run          # Simular sin cambios
"""

from django.core.management.base import BaseCommand, CommandError
from turnero.models import Turno
import os


class Command(BaseCommand):
    help = 'Regenera los códigos QR de los turnos con el nuevo sistema de tokens de seguridad'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pendientes',
            action='store_true',
            help='Solo regenerar QR de turnos con estado PENDIENTE o CONFIRMADO',
        )
        parser.add_argument(
            '--codigo',
            type=str,
            help='Regenerar QR de un turno específico por su código (ej: TRN-ABC123)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular la regeneración sin hacer cambios reales',
        )
        parser.add_argument(
            '--mostrar-url',
            action='store_true',
            help='Mostrar la URL que contendrá cada QR regenerado',
        )

    def handle(self, *args, **options):
        pendientes = options['pendientes']
        codigo = options['codigo']
        dry_run = options['dry_run']
        mostrar_url = options['mostrar_url']

        # Obtener turnos a procesar
        if codigo:
            turnos = Turno.objects.filter(codigo=codigo)
            if not turnos.exists():
                raise CommandError(f'No se encontró turno con código: {codigo}')
        elif pendientes:
            turnos = Turno.objects.filter(estado__in=['PENDIENTE', 'CONFIRMADO'])
        else:
            turnos = Turno.objects.all()

        total = turnos.count()

        if total == 0:
            self.stdout.write(self.style.WARNING('No hay turnos para procesar.'))
            return

        self.stdout.write(self.style.HTTP_INFO(f'\n{"="*60}'))
        self.stdout.write(self.style.HTTP_INFO('REGENERACIÓN DE CÓDIGOS QR CON TOKENS DE SEGURIDAD'))
        self.stdout.write(self.style.HTTP_INFO(f'{"="*60}\n'))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO SIMULACIÓN - No se harán cambios reales\n'))

        self.stdout.write(f'Turnos a procesar: {total}\n')

        exitosos = 0
        errores = 0

        for i, turno in enumerate(turnos, 1):
            try:
                # Generar token para mostrar URL
                token = Turno.generar_token_verificacion(turno.codigo)

                # Obtener URL que se generará
                from django.conf import settings
                import socket
                hostname = socket.gethostname().lower()
                site_url_local = getattr(settings, 'SITE_URL_LOCAL', None)
                site_url_prod = getattr(settings, 'SITE_URL', 'https://rtvpioli.com.ar')
                es_produccion = '167.71.93.198' in hostname or 'rtvpioli' in hostname or site_url_local is None
                site_url = site_url_prod if es_produccion else site_url_local
                qr_url = f"{site_url}/turnero/verificar/{turno.codigo}/?t={token}"

                self.stdout.write(f'[{i}/{total}] {turno.codigo} - {turno.vehiculo.dominio} - {turno.estado}')

                if mostrar_url:
                    self.stdout.write(f'         URL: {qr_url}')

                if not dry_run:
                    # Eliminar QR anterior si existe
                    if turno.qr_code and turno.qr_code.name:
                        try:
                            old_path = turno.qr_code.path
                            if os.path.exists(old_path):
                                os.remove(old_path)
                        except Exception:
                            pass  # Ignorar errores al eliminar archivo viejo

                        turno.qr_code = None
                        turno.save(update_fields=['qr_code'])

                    # Regenerar QR con nuevo token
                    turno.generar_qr()

                    self.stdout.write(self.style.SUCCESS('         [OK] QR regenerado exitosamente'))
                else:
                    self.stdout.write(self.style.HTTP_INFO('         [SIM] Se regeneraria el QR'))

                exitosos += 1

            except Exception as e:
                errores += 1
                self.stdout.write(self.style.ERROR(f'         [ERROR] {str(e)}'))

        # Resumen final
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(self.style.SUCCESS(f'Procesados exitosamente: {exitosos}'))
        if errores > 0:
            self.stdout.write(self.style.ERROR(f'Con errores: {errores}'))
        self.stdout.write(f'{"="*60}\n')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '\nEste fue un dry-run. Ejecute sin --dry-run para aplicar cambios.'
            ))
