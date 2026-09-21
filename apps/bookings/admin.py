from datetime import timedelta

from django.conf import settings
from django.contrib import admin
from django.utils import timezone

from .models import Booking


class BookingPeriodFilter(admin.SimpleListFilter):
    """Filtre par période calculé côté Python.

    Remplace la hiérarchie de dates ET le filtre natif sur ``start_datetime`` :
    ces deux fonctions demandent à MySQL de convertir les fuseaux horaires
    (``CONVERT_TZ``), ce qui exige les tables système ``mysql.time_zone*`` —
    absentes par défaut sur une installation Laragon/Windows. C'est l'origine
    de l'erreur « Database returned an invalid datetime value. Are time zone
    definitions for your database installed? ».
    """

    title = 'période'
    parameter_name = 'periode'

    def lookups(self, request, model_admin):
        return (
            ('today', "Aujourd'hui"),
            ('week', '7 prochains jours'),
            ('month', '30 prochains jours'),
            ('past', 'Passées'),
        )

    def queryset(self, request, queryset):
        # Comparaisons sur des datetime « aware » : aucune fonction de fuseau
        # n'est générée en SQL, MySQL se contente de comparer la valeur.
        now = timezone.localtime(timezone.now())
        value = self.value()
        if value == 'today':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            return queryset.filter(start_datetime__gte=start, start_datetime__lt=end)
        if value == 'week':
            return queryset.filter(start_datetime__gte=now, start_datetime__lt=now + timedelta(days=7))
        if value == 'month':
            return queryset.filter(start_datetime__gte=now, start_datetime__lt=now + timedelta(days=30))
        if value == 'past':
            return queryset.filter(end_datetime__lt=now)
        return queryset


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['title', 'room', 'user', 'attendees_count', 'start_datetime', 'end_datetime', 'status']
    # 'start_datetime' retiré de list_filter : le filtre natif sur un
    # DateTimeField déclenche lui aussi une conversion de fuseau en SQL
    # (tables tz requises). Remplacé par un filtre par période en Python.
    list_filter = ['status', 'room', BookingPeriodFilter]
    search_fields = ['title', 'user__username', 'user__email', 'responsible_person']
    readonly_fields = ['created_at', 'updated_at', 'cancelled_at']
    filter_horizontal = ['requested_equipment']

    # Hiérarchie de dates (drill-down année → mois → jour) : génère un
    # CONVERT_TZ() côté MySQL, donc dépend des tables de fuseaux horaires.
    # Désactivée par défaut pour que l'admin fonctionne immédiatement sous
    # Laragon. Pour la réactiver : chargez les tables tz dans MySQL, puis
    # définissez MYSQL_TIMEZONE_TABLES_INSTALLED = True dans settings.py.
    if getattr(settings, 'MYSQL_TIMEZONE_TABLES_INSTALLED', False):
        date_hierarchy = 'start_datetime'

    def has_delete_permission(self, request, obj=None):
        return request.user.is_admin()
