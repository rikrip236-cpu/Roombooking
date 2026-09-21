from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, date, time as dt_time, timedelta
import json

from .models import Booking
from apps.rooms.models import Room, RoomAvailability, BuildingSettings


class BookingForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Date de début'
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Date de fin',
        help_text=(
            "Identique à la date de début pour une réunion sur une seule journée. "
            "Pour plusieurs jours, choisissez la répartition des horaires ci-dessous."
        )
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label='Heure de début'
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label='Heure de fin'
    )
    # Mode de répartition des horaires :
    #   'same'   → une même plage horaire (début → fin) répétée chaque jour ;
    #   'custom' → un créneau distinct par jour, saisi dans un tableau.
    schedule_mode = forms.ChoiceField(
        required=False,
        initial='same',
        choices=[
            ('same', 'Horaires identiques chaque jour'),
            ('custom', 'Horaires personnalisés par jour'),
        ],
        label='Répartition des horaires',
        widget=forms.RadioSelect(),
    )
    # Charge utile JSON (remplie par le tableau per-jour côté navigateur) :
    # [{"date": "AAAA-MM-JJ", "start": "HH:MM", "end": "HH:MM"}, ...]
    day_schedules_json = forms.CharField(required=False, widget=forms.HiddenInput())
    floor = forms.TypedChoiceField(
        coerce=int,
        required=False,
        label='Étage de la réunion',
        widget=forms.Select(attrs={'class': 'form-select', 'disabled': 'disabled'}),
        help_text="Déterminé automatiquement par l'étage de la salle choisie."
    )

    class Meta:
        model = Booking
        fields = [
            'room', 'title', 'start_date', 'end_date', 'start_time', 'end_time', 'floor',
            'attendees_count', 'responsible_person',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex : Réunion équipe projet'}),
            'room': forms.Select(attrs={'class': 'form-select'}),
            'attendees_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'responsible_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la personne responsable de la réunion'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Liste des étages proposée dynamiquement selon le nombre d'étages
        # défini par l'administrateur (BuildingSettings).
        building_settings = BuildingSettings.load()
        self.fields['floor'].choices = building_settings.floor_choices()
        if self.instance and self.instance.pk:
            self.fields['floor'].initial = self.instance.floor
        active_rooms = Room.objects.filter(is_active=True)
        if self.instance and self.instance.pk and self.instance.room_id:
            # Garde la salle actuelle dans la liste même si elle vient d'être désactivée,
            # pour ne pas casser l'affichage/édition d'une réservation existante.
            active_rooms = (active_rooms | Room.objects.filter(pk=self.instance.room_id)).distinct()
        self.fields['room'].queryset = active_rooms
        if self.instance and self.instance.pk:
            # Dates/heures initiales exprimées en heure locale d'affichage.
            self.fields['start_date'].initial = self.instance.start_local.date()
            self.fields['end_date'].initial = self.instance.end_local.date()
            self.fields['start_time'].initial = self.instance.daily_start_time()
            self.fields['end_time'].initial = self.instance.daily_end_time()
            # Pré-remplit le mode d'horaires et le tableau per-jour en édition.
            # On renseigne AUSSI self.initial : le rendu du widget lit la valeur
            # via form.initial (construit pendant super().__init__()), donc
            # modifier seulement field.initial ne suffit pas à pré-cocher le
            # bon bouton radio ni à pré-remplir le JSON du tableau.
            if self.instance.day_schedules:
                mode_value = 'custom'
                json_value = json.dumps(self.instance.day_schedules)
            else:
                mode_value = 'same'
                json_value = '[]'
            self.fields['schedule_mode'].initial = mode_value
            self.fields['day_schedules_json'].initial = json_value
            self.initial['schedule_mode'] = mode_value
            self.initial['day_schedules_json'] = json_value
            if self.instance.is_past:
                for name in ('room', 'start_date', 'end_date', 'start_time', 'end_time'):
                    self.fields[name].disabled = True

    @staticmethod
    def _parse_day_schedules(raw_json):
        """Convertit la charge JSON du tableau per-jour en liste de créneaux
        {date, start, end}. Les entrées malformées sont ignorées."""
        try:
            data = json.loads(raw_json) if raw_json else []
        except (ValueError, TypeError):
            raise ValidationError("Le format des horaires personnalisés est invalide.")
        if not isinstance(data, list):
            return []
        slots = []
        for item in data:
            if not isinstance(item, dict):
                continue
            try:
                slot_date = date.fromisoformat(item['date'])
                slot_start = dt_time.fromisoformat(item['start'])
                slot_end = dt_time.fromisoformat(item['end'])
            except (KeyError, ValueError, TypeError):
                continue
            slots.append({'date': slot_date, 'start': slot_start, 'end': slot_end})
        slots.sort(key=lambda s: s['date'])
        return slots

    @staticmethod
    def _check_slots_availability(room, slots):
        """Contrôle les horaires d'ouverture pour CHAQUE jour réservé."""
        for slot in slots:
            try:
                avail = RoomAvailability.objects.get(room=room, day_of_week=slot['date'].weekday())
            except RoomAvailability.DoesNotExist:
                continue
            if avail.is_closed:
                raise ValidationError(f"La salle est fermée le {slot['date'].strftime('%d/%m/%Y')}.")
            if slot['start'] < avail.open_time or slot['end'] > avail.close_time:
                raise ValidationError(
                    f"La salle est ouverte de {avail.open_time.strftime('%H:%M')} "
                    f"à {avail.close_time.strftime('%H:%M')} le {slot['date'].strftime('%d/%m/%Y')}."
                )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        room = cleaned_data.get('room')
        attendees_count = cleaned_data.get('attendees_count')
        schedule_mode = cleaned_data.get('schedule_mode') or 'same'
        raw_json = cleaned_data.get('day_schedules_json') or ''
        if not all([start_date, end_date, start_time, end_time, room]):
            return cleaned_data

        if room and attendees_count and attendees_count > room.capacity:
            raise ValidationError(
                f'Cette salle ne peut accueillir que {room.capacity} personne(s) maximum.'
            )

        # L'étage de la réunion suit automatiquement l'étage réel de la salle
        # choisie : le champ est affiché en lecture seule côté formulaire,
        # mais on force ici la valeur cohérente indépendamment de ce que le
        # navigateur aurait pu soumettre.
        if room:
            cleaned_data['floor'] = room.floor
            self.instance.floor = room.floor

        if self.instance.pk and self.instance.is_past:
            # Réservation passée : on n'autorise pas de changement d'horaire/salle.
            return cleaned_data

        if end_date < start_date:
            raise ValidationError('La date de fin doit être identique ou postérieure à la date de début.')

        if not room.is_active:
            raise ValidationError('Cette salle est inactive et ne peut pas être réservée.')

        # ---------------------------------------------------------------
        # Construction des créneaux quotidiens réels de la réservation.
        # Les deux modes produisent la même structure `slots`, réutilisée
        # ensuite par les contrôles de disponibilité et de chevauchement :
        #   - 'same'   : un créneau identique pour chaque jour de la période ;
        #   - 'custom' : un créneau par jour saisi (jours non réservés exclus).
        # ---------------------------------------------------------------
        slots = []
        if schedule_mode == 'custom':
            slots = self._parse_day_schedules(raw_json)
            if not slots:
                raise ValidationError(
                    "Mode « horaires personnalisés » : indiquez au moins un jour réservé "
                    "avec une heure de début et de fin."
                )
            for slot in slots:
                if slot['date'] < start_date or slot['date'] > end_date:
                    raise ValidationError(
                        f"Le {slot['date'].strftime('%d/%m/%Y')} est en dehors de la période "
                        f"{start_date.strftime('%d/%m/%Y')} – {end_date.strftime('%d/%m/%Y')}."
                    )
                if slot['end'] <= slot['start']:
                    raise ValidationError(
                        f"Le {slot['date'].strftime('%d/%m/%Y')} : l'heure de fin doit être "
                        "postérieure à l'heure de début."
                    )
            slots.sort(key=lambda s: s['date'])
            first_slot = slots[0]
            last_slot = slots[-1]
            start_datetime = timezone.make_aware(datetime.combine(first_slot['date'], first_slot['start']))
            end_datetime = timezone.make_aware(datetime.combine(last_slot['date'], last_slot['end']))
            # Aligne les champs simples (masqués en mode personnalisé mais
            # requis) sur la première et la dernière journée.
            cleaned_data['start_time'] = first_slot['start']
            cleaned_data['end_time'] = last_slot['end']
        else:
            start_datetime = timezone.make_aware(datetime.combine(start_date, start_time))
            end_datetime = timezone.make_aware(datetime.combine(end_date, end_time))
            if end_datetime <= start_datetime:
                raise ValidationError("La date/heure de fin doit être après la date/heure de début.")
            # Plage unique : l'heure de fin doit toujours suivre l'heure de début.
            if end_time <= start_time:
                raise ValidationError(
                    "Chaque jour de la réservation doit avoir la même plage horaire : "
                    "l'heure de fin doit être postérieure à l'heure de début."
                )
            current = start_date
            while current <= end_date:
                slots.append({'date': current, 'start': start_time, 'end': end_time})
                current += timedelta(days=1)

        if start_datetime < timezone.now() and not self.instance.pk:
            raise ValidationError('Impossible de réserver dans le passé.')

        # Horaires d'ouverture de la salle, vérifiés jour par jour.
        self._check_slots_availability(room, slots)

        # Chevauchement : comparé créneau par créneau (et non sur toute la
        # période), pour ne pas bloquer à tort les jours réellement libres.
        for slot in slots:
            slot_start = timezone.make_aware(datetime.combine(slot['date'], slot['start']))
            slot_end = timezone.make_aware(datetime.combine(slot['date'], slot['end']))
            overlapping = Booking.objects.filter(
                room=room,
                status='confirmed',
                start_datetime__lt=slot_end,
                end_datetime__gt=slot_start,
            )
            if self.instance and self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                raise ValidationError(
                    f"Cette salle est déjà réservée le {slot['date'].strftime('%d/%m/%Y')} "
                    f"de {slot['start'].strftime('%H:%M')} à {slot['end'].strftime('%H:%M')}."
                )

        cleaned_data['start_datetime'] = start_datetime
        cleaned_data['end_datetime'] = end_datetime
        # 'start_datetime'/'end_datetime' ne font pas partie de Meta.fields, donc
        # Django ne les reporte jamais automatiquement sur self.instance. Sans cette
        # affectation, ModelForm._post_clean() appelle self.instance.full_clean()
        # avec des dates encore à None, ce qui fait planter Booking.clean().
        self.instance.start_datetime = start_datetime
        self.instance.end_datetime = end_datetime
        # Persiste les horaires par jour : vides en mode « identiques »
        # (comportement historique inchangé), renseignés en mode personnalisé.
        if schedule_mode == 'custom':
            self.instance.day_schedules = [
                {
                    'date': slot['date'].isoformat(),
                    'start': slot['start'].strftime('%H:%M'),
                    'end': slot['end'].strftime('%H:%M'),
                }
                for slot in slots
            ]
        else:
            self.instance.day_schedules = []
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if 'start_datetime' in self.cleaned_data:
            instance.start_datetime = self.cleaned_data['start_datetime']
        if 'end_datetime' in self.cleaned_data:
            instance.end_datetime = self.cleaned_data['end_datetime']
        if self.user and not instance.pk:
            instance.user = self.user
        if commit:
            instance.save()
            self.save_m2m()
        return instance
