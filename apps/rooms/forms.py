from django import forms
from .models import Room, Equipment, RoomType, BuildingSettings


# Choix d'icônes proposés pour le matériel, avec un aperçu visuel dans le
# formulaire (voir templates/rooms/equipment_form.html). Les valeurs déjà
# utilisées dans fixtures/demo.json (bi-projector, bi-easel, bi-camera-video,
# bi-wifi, bi-display, bi-easel2-fill, bi-snow, bi-plug) sont incluses pour
# rester compatibles avec les équipements existants.
EQUIPMENT_ICON_CHOICES = [
    ('', 'Aucune icône'),
    ('bi-projector', 'Projecteur'),
    ('bi-display', 'Écran'),
    ('bi-tv', 'Télévision'),
    ('bi-easel', 'Tableau blanc'),
    ('bi-easel2-fill', 'Paperboard'),
    ('bi-camera-video', 'Caméra / Visioconférence'),
    ('bi-mic', 'Micro'),
    ('bi-volume-up', 'Enceinte'),
    ('bi-wifi', 'Wi-Fi'),
    ('bi-plug', 'Prise électrique'),
    ('bi-usb-plug', 'Port USB'),
    ('bi-battery-charging', 'Chargeur'),
    ('bi-snow', 'Climatisation'),
    ('bi-lightbulb', 'Éclairage'),
    ('bi-printer', 'Imprimante'),
    ('bi-telephone', 'Téléphone'),
    ('bi-lock', 'Verrou / Sécurité'),
    ('bi-cup-hot', 'Café / Boissons'),
    ('bi-water', 'Eau'),
    ('bi-tools', 'Autre'),
]


class RoomForm(forms.ModelForm):
    floor = forms.TypedChoiceField(
        coerce=int,
        label='Étage',
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Étage du bâtiment où se trouve cette salle."
    )

    class Meta:
        model = Room
        fields = ['name', 'room_type', 'capacity', 'floor', 'description', 'equipment', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'equipment': forms.CheckboxSelectMultiple(),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Liste des étages proposée dynamiquement selon le nombre d'étages
        # défini par l'administrateur (BuildingSettings), comme pour le
        # formulaire de réservation.
        building_settings = BuildingSettings.load()
        self.fields['floor'].choices = building_settings.floor_choices()
        if self.instance and self.instance.pk:
            self.fields['floor'].initial = self.instance.floor

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity is not None and capacity < 1:
            raise forms.ValidationError('La capacité doit être supérieure à 0.')
        return capacity


class EquipmentForm(forms.ModelForm):
    icon = forms.ChoiceField(
        choices=EQUIPMENT_ICON_CHOICES,
        required=False,
        widget=forms.RadioSelect,
        label='Icône',
        help_text="Choisissez l'icône qui représente le mieux ce matériel."
    )

    class Meta:
        model = Equipment
        fields = ['name', 'description', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class RoomTypeForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = ['name', 'description', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex : Salle de réunion'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: bi-easel'}),
        }


class BuildingSettingsForm(forms.ModelForm):
    class Meta:
        model = BuildingSettings
        fields = ['floor_count', 'ground_floor_label']
        widgets = {
            'floor_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 200}),
            'ground_floor_label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex : Rez-de-chaussée'}),
        }

    def clean_floor_count(self):
        floor_count = self.cleaned_data.get('floor_count')
        if floor_count is not None and floor_count > 200:
            raise forms.ValidationError("Le nombre d'étages semble trop élevé.")
        return floor_count
