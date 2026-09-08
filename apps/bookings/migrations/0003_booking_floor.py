# Generated manually to add the 'floor' field (étage de la réunion)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_booking_attendees_count_booking_requested_equipment_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='floor',
            field=models.PositiveSmallIntegerField(blank=True, default=0, help_text='Étage du bâtiment où se tient la réunion (0 = rez-de-chaussée)', verbose_name='Étage de la réunion'),
        ),
    ]
