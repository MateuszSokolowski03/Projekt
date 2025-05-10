from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_default_groups(sender, **kwargs):
    from django.contrib.auth.models import Group, Permission  # Import wewnątrz funkcji
    from django.contrib.contenttypes.models import ContentType
    from .models import Team, Player, Match, MatchEvent,Round, League

    # Tworzenie grup
    organizers_group, _ = Group.objects.get_or_create(name='Organizers')
    guests_group, _ = Group.objects.get_or_create(name='Guests')

    # Uprawnienia dla organizatorów (pełny dostęp do modeli)
    models = [Team, Player, Match, MatchEvent,Round, League]
    for model in models:
        content_type = ContentType.objects.get_for_model(model)
        permissions = Permission.objects.filter(content_type=content_type)
        organizers_group.permissions.add(*permissions)

    # Uprawnienia dla gości (tylko przeglądanie)
    view_permissions = Permission.objects.filter(codename__startswith='view_')
    guests_group.permissions.add(*view_permissions)

class PlanerAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.planner'

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(create_default_groups, sender=self)