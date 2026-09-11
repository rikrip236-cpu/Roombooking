# Generated manually to add the 'floor' field (étage de la salle)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0002_buildingsettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='floor',
            field=models.PositiveSmallIntegerField(default=0, help_text="Étage du bâtiment où se trouve cette salle (0 = rez-de-chaussée).", verbose_name='Étage'),
        ),
    ]
