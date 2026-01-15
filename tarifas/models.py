from django.db import models
from django.utils import timezone


class Tarifa(models.Model):
    titulo = models.CharField(
        max_length=200,
        verbose_name="Título"
    )
    descripcion = models.TextField(
        verbose_name="Descripción"
    )
    archivo_excel = models.FileField(
        upload_to='tarifas/',
        blank=True,
        null=True,
        verbose_name="Archivo Excel"
    )

    # Campo de estado para indicar si la tarifa está vigente
    status = models.BooleanField(
        default=False,
        verbose_name="Vigente",
        help_text="Marca esta tarifa como vigente. Solo puede haber una tarifa vigente a la vez."
    )

    # Campos de auditoría
    created = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name="Fecha de Creación"
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )

    class Meta:
        verbose_name = "Tarifa"
        verbose_name_plural = "Tarifas"
        ordering = ['-created']

    def __str__(self):
        estado = "✓ VIGENTE" if self.status else ""
        return f"{self.titulo} {estado}"

    def save(self, *args, **kwargs):
        """
        Al marcar una tarifa como vigente, automáticamente
        desmarca todas las demás tarifas e importa los trámites desde el Excel
        """
        # Verificar si estamos marcando como vigente
        marcando_como_vigente = self.status and (
            self.pk is None or  # Es nuevo
            Tarifa.objects.filter(pk=self.pk, status=False).exists()  # Cambió a vigente
        )

        if self.status:
            # Desmarcar todas las demás tarifas como vigentes
            Tarifa.objects.filter(status=True).exclude(pk=self.pk).update(status=False)

        super().save(*args, **kwargs)

        # Si se marcó como vigente y tiene archivo Excel, importar trámites
        if marcando_como_vigente and self.archivo_excel:
            self.importar_tramites()

    def importar_tramites(self):
        """
        Importa trámites desde el archivo Excel asociado a esta tarifa
        y crea automáticamente las configuraciones de taller
        """
        from talleres.utils import importar_tramites_desde_excel, crear_configuraciones_taller
        import os

        if not self.archivo_excel:
            print("No hay archivo Excel para importar")
            return

        archivo_path = self.archivo_excel.path
        if not os.path.exists(archivo_path):
            print(f"Archivo no encontrado: {archivo_path}")
            return

        print(f"Importando trámites desde: {archivo_path}")
        creados, errores, lista_errores = importar_tramites_desde_excel(archivo_path)

        print(f"Importación completada: {creados} trámites creados, {errores} errores")
        if lista_errores:
            for error in lista_errores:
                print(f"  - {error}")

        # Crear configuraciones de taller automáticamente
        print("\nCreando configuraciones de taller...")
        configs_creadas = crear_configuraciones_taller()
        print(f"Configuraciones creadas: {configs_creadas}")

        return (creados, errores, lista_errores)
