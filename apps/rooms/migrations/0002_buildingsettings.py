# Generated manually for BuildingSettings (nombre d'étages du bâtiment)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BuildingSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('floor_count', models.PositiveSmallIntegerField(default=1, help_text="Ex : 3 → Rez-de-chaussée + Étage 1, 2 et 3 seront proposés à la réservation.", verbose_name="Nombre d'étages du bâtiment")),
                ('ground_floor_label', models.CharField(blank=True, default='Rez-de-chaussée', max_length=50, verbose_name='Libellé du rez-de-chaussée')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Paramètre du bâtiment',
                'verbose_name_plural': 'Paramètres du bâtiment',
            },
        ),
    ]
