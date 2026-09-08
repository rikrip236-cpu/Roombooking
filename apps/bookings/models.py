from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import User
from apps.rooms.models import Room, Equipment


class Booking(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmée'),
        ('cancelled', 'Annulée'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Utilisateur'
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Salle'
    )
    title = models.CharField(max_length=200, verbose_name='Motif / Titre')
    floor = models.PositiveSmallIntegerField(
        default=0,
        blank=True,
        verbose_name='Étage de la réunion',
        help_text="Étage du bâtiment où se tient la réunion (0 = rez-de-chaussée)"
    )
    attendees_count = models.PositiveIntegerField(
        default=1,
        blank=True,
        verbose_name='Nombre de personnes',
        help_text='Nombre de personnes attendues autour de la table'
    )
    requested_equipment = models.ManyToManyField(
        Equipment,
        blank=True,
        related_name='booking_requests',
        verbose_name='Matériel demandé',
        help_text='Matériel supplémentaire nécessaire (webcam, écran, tablette...)'
    )
    responsible_person = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Personne en charge du matériel',
        help_text='Nom de la personne responsable / à contacter pour le matériel demandé'
    )
    start_datetime = models.DateTimeField(verbose_name='Début')
    end_datetime = models.DateTimeField(verbose_name='Fin')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='confirmed',
        verbose_name='Statut'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name="Date d'annulation")
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_bookings',
        verbose_name='Annulé par'
    )

    class Meta:
        verbose_name = 'Réservation'
        verbose_name_plural = 'Réservations'
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['room', 'start_datetime', 'end_datetime', 'status']),
        ]

    def __str__(self):
        return f"{self.title} — {self.room.name} ({self.start_datetime:%d/%m %H:%M})"

    def clean(self):
        super().clean()
        # room_id peut être vide si le champ n'a pas été soumis/validé : dans ce cas
        # une erreur de champ existe déjà (via clean_fields), inutile d'aller plus loin.
        if not self.room_id:
            return
        if not self.room.is_active:
            raise ValidationError({'room': 'Cette salle est inactive et ne peut pas être réservée.'})
        if self.attendees_count and self.attendees_count > self.room.capacity:
            raise ValidationError({
                'attendees_count': f'Cette salle ne peut accueillir que {self.room.capacity} personne(s).'
            })
        # start_datetime/end_datetime peuvent être absents à ce stade (ex: champs
        # personnalisés 'date'/'start_time'/'end_time' du formulaire non encore valides,
        # ou exclusion de full_clean) : on ne compare que si les deux sont renseignés.
        if self.start_datetime is None or self.end_datetime is None:
            return
        if self.end_datetime <= self.start_datetime:
            raise ValidationError({'end_datetime': 'La date de fin doit être postérieure à la date de début.'})
        if self.start_datetime < timezone.now() and self._state.adding:
            raise ValidationError({'start_datetime': 'Impossible de réserver dans le passé.'})
        self._check_room_availability()
        if self.status == 'confirmed':
            self._check_overlapping()

    def _check_room_availability(self):
        from apps.rooms.models import RoomAvailability
        day = self.start_datetime.weekday()
        try:
            avail = RoomAvailability.objects.get(room=self.room, day_of_week=day)
        except RoomAvailability.DoesNotExist:
            return
        if avail.is_closed:
            raise ValidationError({'start_datetime': 'La salle est fermée ce jour-là.'})
        start_time = self.start_datetime.time()
        end_time = self.end_datetime.time()
        if start_time < avail.open_time or end_time > avail.close_time:
            raise ValidationError({
                'start_datetime': f'La salle est ouverte de {avail.open_time} à {avail.close_time} ce jour.'
            })

    def _check_overlapping(self):
        overlapping = Booking.objects.filter(
            room=self.room,
            status='confirmed',
            start_datetime__lt=self.end_datetime,
            end_datetime__gt=self.start_datetime,
        )
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)
        if overlapping.exists():
            raise ValidationError({
                '__all__': 'Cette salle est déjà réservée sur ce créneau horaire.'
            })

    def cancel(self, cancelled_by_user):
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.cancelled_by = cancelled_by_user
        self.save(update_fields=['status', 'cancelled_at', 'cancelled_by', 'updated_at'])

    @property
    def duration_minutes(self):
        delta = self.end_datetime - self.start_datetime
        return int(delta.total_seconds() // 60)

    @property
    def is_past(self):
        return self.end_datetime < timezone.now()

    def get_floor_display(self):
        """Libellé lisible de l'étage (ex: 'Rez-de-chaussée', 'Étage 2'),
        basé sur les paramètres du bâtiment définis par l'administrateur."""
        from apps.rooms.models import BuildingSettings
        settings_obj = BuildingSettings.load()
        choices = dict(settings_obj.floor_choices())
        return choices.get(self.floor, f'Étage {self.floor}')

    @property
    def urgency_level(self):
        """Niveau d'urgence selon la proximité de la date de début, utilisé
        pour la mise en couleur dans les listes/calendrier :
        - 'past'   : réservation déjà passée
        - 'red'    : dans moins de 24h (imminent)
        - 'yellow' : dans moins de 3 jours (proche)
        - 'blue'   : plus lointain
        """
        if self.status == 'cancelled':
            return 'cancelled'
        now = timezone.now()
        if self.end_datetime < now:
            return 'past'
        delta = self.start_datetime - now
        hours = delta.total_seconds() / 3600
        if hours <= 24:
            return 'red'
        if hours <= 72:
            return 'yellow'
        return 'blue'
