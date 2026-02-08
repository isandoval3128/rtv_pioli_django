"""
Comando de Django para marcar turnos vencidos como NO_ASISTIO.
Busca turnos PENDIENTE/CONFIRMADO cuya fecha+hora ya pasó y los actualiza.

Uso:
    python manage.py marcar_no_asistio              # Ejecutar
    python manage.py marcar_no_asistio --dry-run    # Simular sin cambios

Para automatizar, agregar al cron del servidor (ej: cada hora):
    0 * * * * cd /ruta/proyecto && python manage.py marcar_no_asistio
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from turnero.models import Turno, HistorialTurno


class Command(BaseCommand):
    help = 'Marca como NO_ASISTIO los turnos vencidos (fecha/hora pasada) que siguen en PENDIENTE o CONFIRMADO'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular sin hacer cambios reales',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        ahora = timezone.localtime()
        hoy = ahora.date()
        hora_actual = ahora.time()

        # Turnos de días anteriores que siguen pendientes/confirmados
        turnos_dias_pasados = Turno.objects.filter(
            estado__in=['PENDIENTE', 'CONFIRMADO'],
            fecha__lt=hoy,
        )

        # Turnos de hoy cuya hora_fin ya pasó
        turnos_hoy_vencidos = Turno.objects.filter(
            estado__in=['PENDIENTE', 'CONFIRMADO'],
            fecha=hoy,
            hora_fin__lt=hora_actual,
        )

        # Unir ambos querysets
        turnos_vencidos = turnos_dias_pasados | turnos_hoy_vencidos
        total = turnos_vencidos.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('No hay turnos vencidos para actualizar.'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING(f'[DRY-RUN] Se encontraron {total} turnos vencidos:'))
            for turno in turnos_vencidos:
                self.stdout.write(
                    f'  - {turno.codigo} | {turno.fecha} {turno.hora_inicio}-{turno.hora_fin} | '
                    f'{turno.estado} | {turno.cliente}'
                )
            return

        # Actualizar turnos
        actualizados = 0
        for turno in turnos_vencidos:
            estado_anterior = turno.estado
            turno.estado = 'NO_ASISTIO'
            turno.save(update_fields=['estado'])

            # Registrar en historial
            HistorialTurno.objects.create(
                turno=turno,
                accion='MARCADO_NO_ASISTIO',
                descripcion=f'Turno marcado como No Asistió (estado anterior: {estado_anterior})',
            )
            actualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'{actualizados} turno(s) marcados como NO_ASISTIO.'
        ))
