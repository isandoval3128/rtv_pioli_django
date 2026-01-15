from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from panel_administracion.models import UserProfile, GroupProfile


class Command(BaseCommand):
    help = 'Crea perfiles del panel para todos los usuarios y grupos existentes'

    def handle(self, *args, **options):
        # Crear perfiles para usuarios existentes
        users_created = 0
        for user in User.objects.all():
            profile, created = UserProfile.objects.get_or_create(user=user)
            if created:
                users_created += 1
                self.stdout.write(f'  Creado perfil para usuario: {user.username}')

        # Crear perfiles para grupos existentes
        groups_created = 0
        for group in Group.objects.all():
            profile, created = GroupProfile.objects.get_or_create(group=group)
            if created:
                groups_created += 1
                self.stdout.write(f'  Creado perfil para grupo: {group.name}')

        self.stdout.write(self.style.SUCCESS(
            f'\nResumen:'
            f'\n  - Perfiles de usuario creados: {users_created}'
            f'\n  - Perfiles de grupo creados: {groups_created}'
        ))
