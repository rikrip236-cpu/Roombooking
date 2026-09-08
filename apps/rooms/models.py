from django.db import models


class Equipment(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Nom')
    description = models.TextField(blank=True, verbose_name='Description')
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Classe d'icône Bootstrap (ex: bi-projector)",
        verbose_name='Icône'
    )

    class Meta:
        verbose_name = 'Équipement'
        verbose_name_plural = 'Équipements'
        ordering = ['name']

    def __str__(self):
        return self.name


class RoomType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Nom du type')
    description = models.TextField(blank=True, verbose_name='Description')
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Classe d'icône Bootstrap (ex: bi-easel)",
        verbose_name='Icône'
    )

    class Meta:
        verbose_name = 'Type de salle'
        verbose_name_plural = 'Types de salle'
        ordering = ['name']

    def __str__(self):
        return self.name


class BuildingSettings(models.Model):
    """Paramètres globaux du bâtiment, définis par l'administrateur.

    Singleton (une seule ligne, pk=1) : permet à l'admin de définir le
    nombre d'étages du bâtiment. Ce nombre est ensuite utilisé pour
    proposer la liste des étages disponibles lors d'une réservation.
    """
    floor_count = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Nombre d'étages du bâtiment",
        help_text="Ex : 3 → Rez-de-chaussée + Étage 1, 2 et 3 seront proposés à la réservation."
    )
    ground_floor_label = models.CharField(
        max_length=50,
        default='Rez-de-chaussée',
        blank=True,
        verbose_name='Libellé du rez-de-chaussée'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Paramètre du bâtiment'
        verbose_name_plural = 'Paramètres du bâtiment'

    def __str__(self):
        return f"Bâtiment — {self.floor_count} étage(s)"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj

    def floor_choices(self):
        """Retourne la liste (valeur, libellé) des étages disponibles,
        du rez-de-chaussée (0) jusqu'au dernier étage défini par l'admin."""
        choices = [(0, self.ground_floor_label or 'Rez-de-chaussée')]
        for i in range(1, self.floor_count + 1):
            choices.append((i, f'Étage {i}'))
        return choices


class Room(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Nom de la salle')
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.PROTECT,
        related_name='rooms',
        null=True,
        blank=True,
        verbose_name='Type de salle'
    )
    capacity = models.PositiveIntegerField(verbose_name='Capacité')
    description = models.TextField(blank=True, verbose_name='Description')
    equipment = models.ManyToManyField(
        Equipment,
        blank=True,
        related_name='rooms',
        verbose_name='Équipements disponibles'
    )
    is_active = models.BooleanField(default=True, verbose_name='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Salle'
        verbose_name_plural = 'Salles'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.capacity} pers.)"


class RoomAvailability(models.Model):
    DAYS = [
        (0, 'Lundi'), (1, 'Mardi'), (2, 'Mercredi'),
        (3, 'Jeudi'), (4, 'Vendredi'), (5, 'Samedi'), (6, 'Dimanche'),
    ]
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='availabilities',
        verbose_name='Salle'
    )
    day_of_week = models.PositiveSmallIntegerField(
        choices=DAYS,
        verbose_name='Jour de la semaine'
    )
    open_time = models.TimeField(default='08:00', verbose_name='Ouverture')
    close_time = models.TimeField(default='18:00', verbose_name='Fermeture')
    is_closed = models.BooleanField(default=False, verbose_name='Fermé ce jour')

    class Meta:
        verbose_name = 'Disponibilité'
        verbose_name_plural = 'Disponibilités'
        unique_together = ['room', 'day_of_week']
        ordering = ['day_of_week']

    def __str__(self):
        return f"{self.room.name} — {self.get_day_of_week_display()}"
