from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import ProtectedError

from .models import Room, Equipment, RoomType, BuildingSettings
from .forms import RoomForm, EquipmentForm, RoomTypeForm, BuildingSettingsForm


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin()


class RoomListView(LoginRequiredMixin, ListView):
    model = Room
    template_name = 'rooms/room_list.html'
    context_object_name = 'rooms'
    paginate_by = 12

    def get_queryset(self):
        qs = super().get_queryset()
        if not (self.request.user.is_authenticated and self.request.user.is_admin()):
            qs = qs.filter(is_active=True)
        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(name__icontains=search)
        min_capacity = self.request.GET.get('capacity')
        if min_capacity:
            try:
                qs = qs.filter(capacity__gte=int(min_capacity))
            except ValueError:
                pass
        room_type = self.request.GET.get('type')
        if room_type:
            qs = qs.filter(room_type_id=room_type)
        return qs.select_related('room_type').order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['min_capacity'] = self.request.GET.get('capacity', '')
        context['selected_type'] = self.request.GET.get('type', '')
        context['room_types'] = RoomType.objects.all()
        return context


class RoomDetailView(LoginRequiredMixin, DetailView):
    model = Room
    template_name = 'rooms/room_detail.html'
    context_object_name = 'room'


class RoomCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Room
    form_class = RoomForm
    template_name = 'rooms/room_form.html'
    success_url = reverse_lazy('rooms:room_list')

    def form_valid(self, form):
        messages.success(self.request, 'Salle créée avec succès.')
        return super().form_valid(form)


class RoomUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Room
    form_class = RoomForm
    template_name = 'rooms/room_form.html'
    success_url = reverse_lazy('rooms:room_list')

    def form_valid(self, form):
        messages.success(self.request, 'Salle modifiée avec succès.')
        return super().form_valid(form)


class RoomDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Room
    template_name = 'rooms/room_confirm_delete.html'
    success_url = reverse_lazy('rooms:room_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Salle supprimée avec succès.')
        return super().delete(request, *args, **kwargs)


class EquipmentListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Equipment
    template_name = 'rooms/equipment_list.html'
    context_object_name = 'equipments'


class EquipmentCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Equipment
    form_class = EquipmentForm
    template_name = 'rooms/equipment_form.html'
    success_url = reverse_lazy('rooms:equipment_list')

    def form_valid(self, form):
        messages.success(self.request, 'Équipement ajouté.')
        return super().form_valid(form)


class EquipmentUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Equipment
    form_class = EquipmentForm
    template_name = 'rooms/equipment_form.html'
    success_url = reverse_lazy('rooms:equipment_list')

    def form_valid(self, form):
        messages.success(self.request, 'Équipement modifié.')
        return super().form_valid(form)


class EquipmentDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Equipment
    template_name = 'rooms/equipment_confirm_delete.html'
    success_url = reverse_lazy('rooms:equipment_list')


class RoomTypeListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = RoomType
    template_name = 'rooms/roomtype_list.html'
    context_object_name = 'room_types'


class RoomTypeCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = RoomType
    form_class = RoomTypeForm
    template_name = 'rooms/roomtype_form.html'
    success_url = reverse_lazy('rooms:roomtype_list')

    def form_valid(self, form):
        messages.success(self.request, 'Type de salle ajouté.')
        return super().form_valid(form)


class RoomTypeUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = RoomType
    form_class = RoomTypeForm
    template_name = 'rooms/roomtype_form.html'
    success_url = reverse_lazy('rooms:roomtype_list')

    def form_valid(self, form):
        messages.success(self.request, 'Type de salle modifié.')
        return super().form_valid(form)


class RoomTypeDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = RoomType
    template_name = 'rooms/roomtype_confirm_delete.html'
    success_url = reverse_lazy('rooms:roomtype_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
        except ProtectedError:
            messages.error(
                request,
                f'Impossible de supprimer "{self.object.name}" : '
                f'{self.object.rooms.count()} salle(s) utilisent encore ce type.'
            )
            return redirect('rooms:roomtype_list')
        messages.success(request, 'Type de salle supprimé.')
        return redirect(self.success_url)


class BuildingSettingsUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Permet à l'administrateur de définir le nombre d'étages du bâtiment.
    Ce nombre détermine ensuite les étages proposés aux utilisateurs lors
    d'une réservation de salle."""
    model = BuildingSettings
    form_class = BuildingSettingsForm
    template_name = 'rooms/building_settings_form.html'
    success_url = reverse_lazy('rooms:building_settings')

    def get_object(self, queryset=None):
        return BuildingSettings.load()

    def form_valid(self, form):
        messages.success(self.request, "Paramètres du bâtiment mis à jour.")
        return super().form_valid(form)
