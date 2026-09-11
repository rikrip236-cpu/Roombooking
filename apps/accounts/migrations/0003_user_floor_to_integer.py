# Generated manually to convert 'floor' from free text (CharField) to a
# constrained integer field (PositiveSmallIntegerField), aligned with the
# floor selection already used on Room and Booking, and limited by the
# floor_count defined by the administrator in BuildingSettings.
#
# Done in two steps to stay safe on MySQL: first clean the existing text
# values while the column is still a CharField (so a direct ALTER COLUMN to
# an integer type doesn't fail on non-numeric leftovers like 'RDC'), then
# alter the column type.

from django.db import migrations, models
import re


def _clean_existing_floor_values(apps, schema_editor):
    """Les anciennes valeurs de 'floor' étaient du texte libre (ex: 'RDC',
    '2e étage', '3'). On tente d'en extraire un nombre ; sinon on vide le
    champ plutôt que de planter la migration."""
    User = apps.get_model('accounts', 'User')
    for user in User.objects.exclude(floor__isnull=True).exclude(floor=''):
        match = re.search(r'\d+', str(user.floor))
        user.floor = match.group() if match else ''
        user.save(update_fields=['floor'])


def _noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_floor'),
    ]

    operations = [
        # 1) Nettoyer les valeurs texte existantes pendant que le champ est
        #    encore un CharField (évite les erreurs de cast SQL direct).
        migrations.RunPython(_clean_existing_floor_values, _noop_reverse),
        # 2) Convertir les chaînes vides restantes en NULL pour permettre le
        #    passage à un champ entier nullable.
        migrations.RunSQL(
            "UPDATE accounts_user SET floor = NULL WHERE floor = ''",
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 3) Convertir le champ en entier.
        migrations.AlterField(
            model_name='user',
            name='floor',
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                help_text="Étage où travaille cet utilisateur (0 = rez-de-chaussée).",
                verbose_name='Étage',
            ),
        ),
    ]
