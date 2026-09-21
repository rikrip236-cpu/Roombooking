import datetime

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
    day_schedules = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Horaires personnalisés par jour',
        help_text=
            "Optionnel. Liste des créneaux quotidiens d'une réservation à "
            "horaires variables, au format "
            "[{'date': 'AAAA-MM-JJ', 'start': 'HH:MM', 'end': 'HH:MM'}, ...]. "
            "Vide = même plage horaire (début → fin) répétée chaque jour."
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
        # personnalisés 'start_date'/'end_date'/'start_time'/'end_time' du formulaire
        # non encore valides, ou exclusion de full_clean) : on ne compare que si les
        # deux sont renseignés.
        if self.start_datetime is None or self.end_datetime is None:
            return
        if self.end_datetime <= self.start_datetime:
            raise ValidationError({'end_datetime': 'La date de fin doit être postérieure à la date de début.'})
        # Réservation à plage unique (mode par défaut) : l'heure de fin doit
        # toujours être postérieure à l'heure de début, même si les dates
        # diffèrent (ex. 09:00 → 17:00 du lundi au mercredi).
        if not self.day_schedules and self.daily_end_time() <= self.daily_start_time():
            raise ValidationError({
                'end_datetime': "Chaque jour, l'heure de fin doit être postérieure à l'heure de début."
            })
        # Horaires personnalisés : chaque créneau quotidien doit être valide.
        for slot in self.day_slots():
            if slot['end'] <= slot['start']:
                raise ValidationError({
                    'end_datetime': f"Le {slot['date'].strftime('%d/%m/%Y')} : "
                                    "l'heure de fin doit être postérieure à l'heure de début."
                })
        if self.start_datetime < timezone.now() and self._state.adding:
            raise ValidationError({'start_datetime': 'Impossible de réserver dans le passé.'})
        self._check_room_availability()
        if self.status == 'confirmed':
            self._check_overlapping()

    def _check_room_availability(self):
        """Vérifie les horaires d'ouverture pour CHAQUE jour de la réservation,
        en utilisant les créneaux quotidiens réels (plage unique répétée ou
        horaires personnalisés par jour)."""
        from apps.rooms.models import RoomAvailability
        for slot in self.day_slots():
            try:
                avail = RoomAvailability.objects.get(room=self.room, day_of_week=slot['date'].weekday())
            except RoomAvailability.DoesNotExist:
                continue
            if avail.is_closed:
                raise ValidationError({
                    'start_datetime': f"La salle est fermée le {slot['date'].strftime('%d/%m/%Y')}."
                })
            if slot['start'] < avail.open_time or slot['end'] > avail.close_time:
                raise ValidationError({
                    'start_datetime': f"La salle est ouverte de {avail.open_time} à {avail.close_time} "
                                       f"le {slot['date'].strftime('%d/%m/%Y')}."
                })

    def _check_overlapping(self):
        """Détecte un chevauchement jour par jour : chaque créneau quotidien
        réel de la réservation est comparé aux réservations confirmées."""
        tz = timezone.get_current_timezone()
        for slot in self.day_slots():
            # NB : models.py fait `import datetime` (le MODULE) → il faut
            # datetime.datetime.combine(...) et non datetime.combine(...),
            # sinon AttributeError: module 'datetime' has no attribute 'combine'.
            slot_start = timezone.make_aware(
                datetime.datetime.combine(slot['date'], slot['start']), tz
            )
            slot_end = timezone.make_aware(
                datetime.datetime.combine(slot['date'], slot['end']), tz
            )
            overlapping = Booking.objects.filter(
                room=self.room,
                status='confirmed',
                start_datetime__lt=slot_end,
                end_datetime__gt=slot_start,
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            if overlapping.exists():
                raise ValidationError({
                    '__all__': f"Cette salle est déjà réservée le {slot['date'].strftime('%d/%m/%Y')} "
                               f"de {slot['start'].strftime('%H:%M')} à {slot['end'].strftime('%H:%M')}."
                })

    def cancel(self, cancelled_by_user):
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.cancelled_by = cancelled_by_user
        self.save(update_fields=['status', 'cancelled_at', 'cancelled_by', 'updated_at'])

    def _local(self, value):
        """Convertit un datetime stocké (UTC) vers le fuseau d'affichage actif
        (Europe/Paris par défaut via TimezoneDisplayMiddleware)."""
        return timezone.localtime(value, timezone.get_current_timezone())

    @property
    def start_local(self):
        return self._local(self.start_datetime)

    @property
    def end_local(self):
        return self._local(self.end_datetime)

    def daily_start_time(self):
        """Heure de début (locale) appliquée à CHAQUE jour de la réservation."""
        return self._local(self.start_datetime).time()

    def daily_end_time(self):
        """Heure de fin (locale) appliquée à CHAQUE jour de la réservation."""
        return self._local(self.end_datetime).time()

    @property
    def is_multi_day(self):
        """Vrai si la réservation couvre plusieurs jours calendaires."""
        return self._local(self.start_datetime).date() != self._local(self.end_datetime).date()

    @property
    def duration_days(self):
        """Nombre de jours réellement réservés.

        En mode horaires personnalisés, certains jours peuvent être absents :
        on compte donc les créneaux quotidiens définis. Sinon, il s'agit du
        nombre de jours calendaires couverts (bornes incluses)."""
        if self.day_schedules:
            return len(self.day_slots())
        start = self._local(self.start_datetime).date()
        end = self._local(self.end_datetime).date()
        return (end - start).days + 1

    @property
    def has_custom_schedule(self):
        """Vrai si des horaires personnalisés par jour sont définis."""
        return bool(self.day_schedules)

    def day_slots(self):
        """Retourne la liste ordonnée des créneaux quotidiens de la
        réservation : [{'date': date, 'start': time, 'end': time}, ...].

        - Si des horaires personnalisés sont définis (day_schedules), ils sont
          utilisés tels quels (un créneau par jour saisi) ;
        - Sinon, la plage horaire unique (start → end) est répétée à
          l'identique sur chaque jour de la période (comportement historique).
        Les horaires sont renvoyés en heure locale d'affichage."""
        tz = timezone.get_current_timezone()
        if self.day_schedules:
            slots = []
            for item in self.day_schedules:
                try:
                    slot_date = datetime.date.fromisoformat(item['date'])
                    slot_start = datetime.time.fromisoformat(item['start'])
                    slot_end = datetime.time.fromisoformat(item['end'])
                except (KeyError, ValueError, TypeError):
                    # Entrée malformée ignorée : une seule ligne corrompue ne
                    # doit pas faire échouer l'affichage complet du calendrier.
                    continue
                slots.append({'date': slot_date, 'start': slot_start, 'end': slot_end})
            slots.sort(key=lambda s: s['date'])
            if slots:
                return slots
        # Repli (mode par défaut) : plage unique répétée sur toute la période.
        start_local = timezone.localtime(self.start_datetime, tz)
        end_local = timezone.localtime(self.end_datetime, tz)
        daily_start = start_local.time()
        daily_end = end_local.time()
        slots = []
        day = start_local.date()
        last = end_local.date()
        while day <= last:
            slots.append({'date': day, 'start': daily_start, 'end': daily_end})
            day += datetime.timedelta(days=1)
        return slots

    @property
    def duration_minutes(self):
        """Durée du créneau QUOTIDIEN, identique pour chaque jour du range.

        Pour une réservation multi-jours (ex. 09:00 → 17:00 du lundi au
        mercredi), il s'agit de la durée d'une journée (8h), et non de la
        durée cumulée sur toute la période."""
        if not self.start_datetime or not self.end_datetime:
            return 0
        base = datetime.date.min
        delta = (
            datetime.datetime.combine(base, self.daily_end_time())
            - datetime.datetime.combine(base, self.daily_start_time())
        )
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
