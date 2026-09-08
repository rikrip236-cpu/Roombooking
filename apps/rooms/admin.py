from django.contrib import admin
from .models import Room, Equipment, RoomAvailability, RoomType, BuildingSettings


class RoomAvailabilityInline(admin.TabularInline):
    model = RoomAvailability
    extra = 7
    max_num = 7


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'room_type', 'capacity', 'is_active', 'created_at']
    list_filter = ['is_active', 'room_type', 'equipment']
    search_fields = ['name', 'description']
    filter_horizontal = ['equipment']
    inlines = [RoomAvailabilityInline]


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']
    search_fields = ['name']


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']
    search_fields = ['name']


@admin.register(BuildingSettings)
class BuildingSettingsAdmin(admin.ModelAdmin):
    list_display = ['floor_count', 'ground_floor_label', 'updated_at']

    def has_add_permission(self, request):
        # Singleton : une seule ligne de paramètres.
        return not BuildingSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
