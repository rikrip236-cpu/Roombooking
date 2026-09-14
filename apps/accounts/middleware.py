"""
Middleware d'activation du fuseau horaire d'affichage.

Avec USE_TZ=True et TIME_ZONE='UTC' (voir config/settings.py), Django stocke
toutes les dates en UTC dans la base — ce qui évite de dépendre des tables
système mysql.time_zone* (souvent absentes sur une installation Laragon
Windows, cause de l'erreur "Database returned an invalid datetime value.
Are time zone definitions for your database installed?").

Ce middleware active, pour la durée de chaque requête, le fuseau horaire
d'AFFICHAGE défini par TIME_ZONE_DISPLAY (Europe/Paris par défaut). Django
convertit alors automatiquement les dates UTC stockées en base vers l'heure
de Paris pour tous les templates, formulaires et l'admin — sans toucher au
fuseau de stockage.
"""
from django.utils import timezone
from django.conf import settings


class TimezoneDisplayMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.display_tz = getattr(settings, 'TIME_ZONE_DISPLAY', 'Europe/Paris')

    def __call__(self, request):
        timezone.activate(self.display_tz)
        try:
            response = self.get_response(request)
        finally:
            timezone.deactivate()
        return response
