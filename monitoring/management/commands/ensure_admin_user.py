from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Garantiza que exista el usuario admin/admin solicitado para las demos."

    def handle(self, *args, **options):
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@igp.gob.pe',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        user.set_password('admin')
        user.is_staff = True
        user.is_superuser = True
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS('Usuario admin creado con contraseña "admin".'))
        else:
            self.stdout.write(self.style.SUCCESS('Usuario admin actualizado con la contraseña definida.'))
