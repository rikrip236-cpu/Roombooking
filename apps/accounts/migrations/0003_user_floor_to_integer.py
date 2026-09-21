# Generated manually to convert 'floor' from free text (CharField) to a
# constrained integer field (PositiveSmallIntegerField), aligned with the
# floor selection already used on Room and Booking, and limited by the
# floor_count defined by the administrator in BuildingSettings.
#
# Done in careful steps to stay safe on MySQL:
#   1) The original column is CharField(blank=True) WITHOUT null=True, so in
#      MySQL it is defined NOT NULL with default ''. Setting it to NULL
#      before widening the column raises IntegrityError (1048: "Column
#      'floor' cannot be null") — that's the bug this migration fixes.
#   2) So we first ALTER the column to CharField(null=True, blank=True) —
#      still text, but now NULL-able — before touching any data.
#   3) Only then do we clean the existing text values (extract digits from
#      things like 'RDC', '2e étage', or blank them to NULL).
#   4) Finally we convert the column to PositiveSmallIntegerField.

from django.db import migrations, models
import re


def _clean_existing_floor_values(apps, schema_editor):
    """Les anciennes valeurs de 'floor' étaient du texte libre (ex: 'RDC',
    '2e étage', '3'). On tente d'en extraire un nombre ; sinon on met le
    champ à NULL plutôt que de planter la migration. À ce stade la colonne
    est déjà NULL-able (voir étape précédente), donc cette écriture est
    sûre."""
    User = apps.get_model('accounts', 'User')
    for user in User.objects.exclude(floor__isnull=True).exclude(floor=''):
        match = re.search(r'\d+', str(user.floor))
        user.floor = match.group() if match else None
        user.save(update_fields=['floor'])


def _noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_floor'),
    ]

    operations = [
        # 1) Rendre la colonne NULL-able tout en restant du texte, AVANT
        #    toute écriture de NULL (évite l'IntegrityError 1048).
        migrations.AlterField(
            model_name='user',
            name='floor',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Étage'),
        ),
        # 2) Nettoyer les valeurs texte existantes (colonne déjà NULL-able).
        migrations.RunPython(_clean_existing_floor_values, _noop_reverse),
        # 3) Convertir les chaînes vides restantes en NULL par sécurité
        #    (au cas où certaines lignes n'ont pas été touchées ci-dessus).
        migrations.RunSQL(
            "UPDATE accounts_user SET floor = NULL WHERE floor = ''",
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 4) Convertir le champ en entier.
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
