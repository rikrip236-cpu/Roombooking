# Generated manually to add the 'day_schedules' field
# (horaires personnalisés par jour pour les réservations multi-jours).
#
# IMPORTANT : cette migration est numérotée 0005 (et non 0004) afin de se
# placer APRÈS la migration de fusion 0004_merge_20260908_0720 déjà présente
# dans le projet. Deux migrations 0004 en parallèle créaient deux nœuds
# feuilles dans le graphe de migrations (erreur "Conflicting migrations
# detected; multiple leaf nodes"). Ici, le graphe redevient linéaire :
#   ... -> 0004_merge_20260908_0720 -> 0005_booking_day_schedules (unique feuille)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0004_merge_20260908_0720'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='day_schedules',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text=(
                    "Optionnel. Liste des créneaux quotidiens d'une réservation à "
                    "horaires variables, au format "
                    "[{'date': 'AAAA-MM-JJ', 'start': 'HH:MM', 'end': 'HH:MM'}, ...]. "
                    "Vide = même plage horaire (début → fin) répétée chaque jour."
                ),
                verbose_name='Horaires personnalisés par jour',
            ),
        ),
    ]
