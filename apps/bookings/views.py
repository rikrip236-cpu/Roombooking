from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from datetime import datetime, timedelta
import calendar

from .models import Booking
from .forms import BookingForm
from apps.rooms.models import Room


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin()


class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 10

    def get_queryset(self):
        qs = Booking.objects.select_related('room', 'user')
        if not self.request.user.is_admin():
            qs = qs.filter(user=self.request.user)
        room_id = self.request.GET.get('room')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        status = self.request.GET.get('status')
        if room_id:
            qs = qs.filter(room_id=room_id)
        if date_from:
            qs = qs.filter(start_datetime__date__gte=date_from)
        if date_to:
            qs = qs.filter(end_datetime__date__lte=date_to)
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-start_datetime')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rooms'] = Room.objects.filter(is_active=True)
        return context


class BookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'bookings/booking_form.html'
    success_url = reverse_lazy('bookings:booking_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Réservation créée avec succès.')
        return super().form_valid(form)


class BookingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Booking
    form_class = BookingForm
    template_name = 'bookings/booking_form.html'
    success_url = reverse_lazy('bookings:booking_list')

    def test_func(self):
        booking = self.get_object()
        return self.request.user.is_admin() or self.request.user == booking.user

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status == 'cancelled':
            messages.error(request, 'Impossible de modifier une réservation annulée.')
            return redirect('bookings:booking_detail', pk=self.object.pk)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status == 'cancelled':
            messages.error(request, 'Impossible de modifier une réservation annulée.')
            return redirect('bookings:booking_detail', pk=self.object.pk)
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Réservation modifiée avec succès.')
        return super().form_valid(form)


class BookingDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Booking
    template_name = 'bookings/booking_detail.html'
    context_object_name = 'booking'

    def test_func(self):
        booking = self.get_object()
        return self.request.user.is_admin() or self.request.user == booking.user


class BookingCancelView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Booking
    template_name = 'bookings/booking_cancel.html'
    success_url = reverse_lazy('bookings:booking_list')

    def test_func(self):
        booking = self.get_object()
        return self.request.user.is_admin() or self.request.user == booking.user

    def get(self, request, *args, **kwargs):
        booking = self.get_object()
        if booking.status == 'cancelled':
            messages.info(request, 'Cette réservation est déjà annulée.')
            return redirect('bookings:booking_detail', pk=booking.pk)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        booking = self.get_object()
        if booking.status == 'cancelled':
            messages.info(request, 'Cette réservation est déjà annulée.')
            return redirect('bookings:booking_detail', pk=booking.pk)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        # IMPORTANT : depuis Django 4.0, DeleteView.post() passe par form_valid()
        # et non plus par delete(). Il ne faut donc PAS supprimer l'enregistrement
        # ici (self.object.delete() effacerait définitivement la réservation) :
        # on se contente de l'annuler (statut 'cancelled'), comme prévu.
        self.object.cancel(self.request.user)
        messages.success(self.request, 'Réservation annulée.')
        return redirect(self.get_success_url())


class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'bookings/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))
        room_filter = self.request.GET.get('room')
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        cal = calendar.Calendar()
        month_days = cal.monthdayscalendar(year, month)
        start_of_month = timezone.make_aware(datetime(year, month, 1))
        if month == 12:
            end_of_month = timezone.make_aware(datetime(year + 1, 1, 1))
        else:
            end_of_month = timezone.make_aware(datetime(year, month + 1, 1))
        bookings_qs = Booking.objects.filter(
            status='confirmed',
            start_datetime__gte=start_of_month,
            start_datetime__lt=end_of_month
        ).select_related('room', 'user')
        if room_filter:
            bookings_qs = bookings_qs.filter(room_id=room_filter)
        bookings_by_day = {}
        for booking in bookings_qs:
            day = booking.start_datetime.day
            if day not in bookings_by_day:
                bookings_by_day[day] = []
            bookings_by_day[day].append(booking)
        context.update({
            'year': year, 'month': month,
            'month_name': calendar.month_name[month],
            'month_days': month_days,
            'bookings_by_day': bookings_by_day,
            'prev_month': prev_month, 'prev_year': prev_year,
            'next_month': next_month, 'next_year': next_year,
            'rooms': Room.objects.filter(is_active=True),
            'selected_room': room_filter,
        })
        return context


def api_bookings_json(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    room_id = request.GET.get('room')
    qs = Booking.objects.filter(status='confirmed')

    def parse_and_localize(value):
        # parse_datetime() accepte aussi une simple date ("2026-09-14") et renvoie
        # alors un datetime naïf (minuit) : sans le rendre "aware", Django compare
        # ce datetime naïf à des champs timezone-aware de façon non fiable
        # (avertissement RuntimeWarning + résultats potentiellement décalés selon
        # le fuseau du serveur). On le rend donc explicitement aware.
        parsed = parse_datetime(value)
        if parsed is None:
            parsed_date = parse_date(value)
            if parsed_date is None:
                return None
            parsed = datetime.combine(parsed_date, datetime.min.time())
        if timezone.is_naive(parsed):
            parsed = timezone.make_aware(parsed)
        return parsed

    if start:
        parsed_start = parse_and_localize(start)
        if parsed_start:
            qs = qs.filter(start_datetime__gte=parsed_start)
    if end:
        parsed_end = parse_and_localize(end)
        if parsed_end:
            qs = qs.filter(end_datetime__lte=parsed_end)
    if room_id:
        qs = qs.filter(room_id=room_id)
    # Code couleur selon la proximité de la date de la réunion :
    # rouge = imminent (< 24h), jaune = proche (< 3 jours), bleu ciel = lointain.
    urgency_colors = {
        'red': '#ef4444',
        'yellow': '#f1c40f',
        'blue': '#87ceeb',
        'past': '#9ca3af',
        'cancelled': '#9ca3af',
    }
    events = []
    for booking in qs.select_related('room', 'user'):
        events.append({
            'id': booking.id,
            'title': f"{booking.title} — {booking.room.name}",
            'start': booking.start_datetime.isoformat(),
            'end': booking.end_datetime.isoformat(),
            'extendedProps': {
                'room': booking.room.name,
                'user': booking.user.get_full_name() or booking.user.username,
                'capacity': booking.room.capacity,
                'floor': booking.get_floor_display(),
            },
            'backgroundColor': urgency_colors.get(booking.urgency_level, '#3b82f6'),
            'borderColor': urgency_colors.get(booking.urgency_level, '#3b82f6'),
        })
    return JsonResponse(events, safe=False)
