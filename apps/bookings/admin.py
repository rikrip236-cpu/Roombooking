from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['title', 'room', 'user', 'attendees_count', 'start_datetime', 'end_datetime', 'status']
    list_filter = ['status', 'room', 'start_datetime']
    search_fields = ['title', 'user__username', 'user__email', 'responsible_person']
    date_hierarchy = 'start_datetime'
    readonly_fields = ['created_at', 'updated_at', 'cancelled_at']
    filter_horizontal = ['requested_equipment']

    def has_delete_permission(self, request, obj=None):
        return request.user.is_admin()
