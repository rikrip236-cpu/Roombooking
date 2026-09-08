from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime

from .models import Booking
from apps.rooms.models import Room, RoomAvailability, Equipment, BuildingSettings


class BookingForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Date'
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label='Heure de début'
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label='Heure de fin'
    )
    requested_equipment = forms.ModelMultipleChoiceField(
        queryset=Equipment.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Matériel demandé'
    )
    floor = forms.TypedChoiceField(
        coerce=int,
        label='Étage de la réunion',
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Sélectionnez l'étage où se tiendra la réunion."
    )

    class Meta:
        model = Booking
        fields = [
            'room', 'title', 'date', 'start_time', 'end_time', 'floor',
            'attendees_count', 'requested_equipment', 'responsible_person',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex : Réunion équipe projet'}),
            'room': forms.Select(attrs={'class': 'form-select'}),
            'attendees_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'responsible_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la personne responsable du matériel'
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
            self.fields['date'].initial = self.instance.start_datetime.date()
            self.fields['start_time'].initial = self.instance.start_datetime.time()
            self.fields['end_time'].initial = self.instance.end_datetime.time()
            if self.instance.is_past:
                for name in ('room', 'date', 'start_time', 'end_time'):
                    self.fields[name].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        room = cleaned_data.get('room')
        attendees_count = cleaned_data.get('attendees_count')
        if not all([date, start_time, end_time, room]):
            return cleaned_data

        if room and attendees_count and attendees_count > room.capacity:
            raise ValidationError(
                f'Cette salle ne peut accueillir que {room.capacity} personne(s) maximum.'
            )

        if self.instance.pk and self.instance.is_past:
            # Réservation passée : on n'autorise pas de changement d'horaire/salle.
            return cleaned_data

        start_datetime = timezone.make_aware(datetime.combine(date, start_time))
        end_datetime = timezone.make_aware(datetime.combine(date, end_time))

        if end_datetime <= start_datetime:
            raise ValidationError("L'heure de fin doit être après l'heure de début.")
        if start_datetime < timezone.now() and not self.instance.pk:
            raise ValidationError('Impossible de réserver dans le passé.')
        if not room.is_active:
            raise ValidationError('Cette salle est inactive et ne peut pas être réservée.')

        # Vérifie les horaires d'ouverture déclarés pour la salle, si définis.
        try:
            avail = RoomAvailability.objects.get(room=room, day_of_week=start_datetime.weekday())
            if avail.is_closed:
                raise ValidationError('La salle est fermée ce jour-là.')
            if start_time < avail.open_time or end_time > avail.close_time:
                raise ValidationError(
                    f'La salle est ouverte de {avail.open_time.strftime("%H:%M")} '
                    f'à {avail.close_time.strftime("%H:%M")} ce jour.'
                )
        except RoomAvailability.DoesNotExist:
            pass

        overlapping = Booking.objects.filter(
            room=room,
            status='confirmed',
            start_datetime__lt=end_datetime,
            end_datetime__gt=start_datetime,
        )
        if self.instance and self.instance.pk:
            overlapping = overlapping.exclude(pk=self.instance.pk)
        if overlapping.exists():
            raise ValidationError('Cette salle est déjà réservée sur ce créneau.')

        cleaned_data['start_datetime'] = start_datetime
        cleaned_data['end_datetime'] = end_datetime
        # 'start_datetime'/'end_datetime' ne font pas partie de Meta.fields, donc
        # Django ne les reporte jamais automatiquement sur self.instance. Sans cette
        # affectation, ModelForm._post_clean() appelle self.instance.full_clean()
        # avec des dates encore à None, ce qui fait planter Booking.clean().
        self.instance.start_datetime = start_datetime
        self.instance.end_datetime = end_datetime
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
