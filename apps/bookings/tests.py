from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta, datetime, time

from django.contrib.auth import get_user_model
from apps.rooms.models import Room, RoomAvailability
from apps.bookings.models import Booking
from apps.bookings.forms import BookingForm

User = get_user_model()


class BookingModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='pass')
        self.room = Room.objects.create(name='Salle A', capacity=8, is_active=True)
        RoomAvailability.objects.create(
            room=self.room, day_of_week=0,
            open_time='08:00', close_time='18:00', is_closed=False
        )
        self.tomorrow = timezone.now() + timedelta(days=1)
        while self.tomorrow.weekday() != 0:
            self.tomorrow += timedelta(days=1)

    def test_create_booking(self):
        booking = Booking.objects.create(
            user=self.user, room=self.room, title='Réunion test',
            start_datetime=self.tomorrow.replace(hour=9, minute=0),
            end_datetime=self.tomorrow.replace(hour=10, minute=0),
            status='confirmed'
        )
        self.assertEqual(booking.title, 'Réunion test')
        self.assertEqual(booking.duration_minutes, 60)

    def test_booking_overlap_detection(self):
        start = self.tomorrow.replace(hour=9, minute=0)
        end = self.tomorrow.replace(hour=10, minute=0)
        Booking.objects.create(
            user=self.user, room=self.room, title='Première',
            start_datetime=start, end_datetime=end, status='confirmed'
        )
        with self.assertRaises(ValidationError):
            booking2 = Booking(
                user=self.user, room=self.room, title='Conflit',
                start_datetime=start.replace(hour=9, minute=30),
                end_datetime=end.replace(hour=10, minute=30),
                status='confirmed'
            )
            booking2.full_clean()

    def test_booking_no_overlap_with_cancelled(self):
        start = self.tomorrow.replace(hour=9, minute=0)
        end = self.tomorrow.replace(hour=10, minute=0)
        Booking.objects.create(
            user=self.user, room=self.room, title='Annulée',
            start_datetime=start, end_datetime=end, status='cancelled'
        )
        booking2 = Booking(
            user=self.user, room=self.room, title='Remplacement',
            start_datetime=start, end_datetime=end, status='confirmed'
        )
        booking2.full_clean()
        booking2.save()

    def test_booking_inactive_room(self):
        self.room.is_active = False
        self.room.save()
        with self.assertRaises(ValidationError):
            booking = Booking(
                user=self.user, room=self.room, title='Impossible',
                start_datetime=self.tomorrow.replace(hour=9, minute=0),
                end_datetime=self.tomorrow.replace(hour=10, minute=0)
            )
            booking.full_clean()

    def test_booking_past_date(self):
        yesterday = timezone.now() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            booking = Booking(
                user=self.user, room=self.room, title='Passé',
                start_datetime=yesterday.replace(hour=9, minute=0),
                end_datetime=yesterday.replace(hour=10, minute=0)
            )
            booking.full_clean()

    def test_booking_end_before_start(self):
        with self.assertRaises(ValidationError):
            booking = Booking(
                user=self.user, room=self.room, title='Invalide',
                start_datetime=self.tomorrow.replace(hour=10, minute=0),
                end_datetime=self.tomorrow.replace(hour=9, minute=0)
            )
            booking.full_clean()

    def test_booking_cancel_method(self):
        booking = Booking.objects.create(
            user=self.user, room=self.room, title='À annuler',
            start_datetime=self.tomorrow.replace(hour=9, minute=0),
            end_datetime=self.tomorrow.replace(hour=10, minute=0)
        )
        admin = User.objects.create_user(username='admin', password='pass', role='admin')
        booking.cancel(admin)
        self.assertEqual(booking.status, 'cancelled')
        self.assertIsNotNone(booking.cancelled_at)
        self.assertEqual(booking.cancelled_by, admin)

    def test_booking_is_past_property(self):
        past = timezone.now() - timedelta(hours=2)
        booking = Booking.objects.create(
            user=self.user, room=self.room, title='Passée',
            start_datetime=past - timedelta(hours=1),
            end_datetime=past
        )
        self.assertTrue(booking.is_past)


class BookingFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user', password='pass')
        self.room = Room.objects.create(name='Salle Form', capacity=5, is_active=True)
        self.tomorrow = timezone.now() + timedelta(days=1)
        while self.tomorrow.weekday() != 0:
            self.tomorrow += timedelta(days=1)

    def test_valid_form(self):
        form = BookingForm(data={
            'room': self.room.id,
            'title': 'Test form',
            'date': self.tomorrow.date(),
            'start_time': '09:00',
            'end_time': '10:00'
        }, user=self.user)
        self.assertTrue(form.is_valid())

    def test_invalid_overlap_in_form(self):
        # La réservation existante doit être construite comme le ferait le
        # formulaire (heure locale Europe/Paris via make_aware), sinon elle
        # n'utilise pas le même référentiel horaire que start/end_time
        # saisis plus bas et le chevauchement n'est jamais détecté.
        start = timezone.make_aware(datetime.combine(self.tomorrow.date(), time(9, 0)))
        end = timezone.make_aware(datetime.combine(self.tomorrow.date(), time(10, 0)))
        Booking.objects.create(
            user=self.user, room=self.room, title='Existante',
            start_datetime=start, end_datetime=end
        )
        form = BookingForm(data={
            'room': self.room.id,
            'title': 'Chevauchement',
            'date': self.tomorrow.date(),
            'start_time': '09:30',
            'end_time': '10:30'
        }, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_end_before_start_in_form(self):
        form = BookingForm(data={
            'room': self.room.id,
            'title': 'Invalide',
            'date': self.tomorrow.date(),
            'start_time': '11:00',
            'end_time': '10:00'
        }, user=self.user)
        self.assertFalse(form.is_valid())


class BookingViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='user', password='pass')
        self.other = User.objects.create_user(username='other', password='pass')
        self.admin = User.objects.create_user(username='admin', password='pass', role='admin')
        self.room = Room.objects.create(name='Salle V', capacity=5, is_active=True)
        self.tomorrow = timezone.now() + timedelta(days=1)
        while self.tomorrow.weekday() != 0:
            self.tomorrow += timedelta(days=1)
        self.booking = Booking.objects.create(
            user=self.user, room=self.room, title='Ma résa',
            start_datetime=self.tomorrow.replace(hour=9, minute=0),
            end_datetime=self.tomorrow.replace(hour=10, minute=0)
        )

    def test_booking_list_requires_login(self):
        response = self.client.get(reverse('bookings:booking_list'))
        self.assertEqual(response.status_code, 302)

    def test_booking_list_shows_user_bookings(self):
        self.client.login(username='user', password='pass')
        response = self.client.get(reverse('bookings:booking_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ma résa')

    def test_user_cannot_edit_other_booking(self):
        self.client.login(username='other', password='pass')
        response = self.client.get(reverse('bookings:booking_update', args=[self.booking.pk]))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_edit_any_booking(self):
        self.client.login(username='admin', password='pass')
        response = self.client.get(reverse('bookings:booking_update', args=[self.booking.pk]))
        self.assertEqual(response.status_code, 200)

    def test_booking_create_post(self):
        self.client.login(username='user', password='pass')
        response = self.client.post(reverse('bookings:booking_create'), {
            'room': self.room.id,
            'title': 'Nouvelle résa',
            'date': (self.tomorrow + timedelta(days=1)).date(),
            'start_time': '14:00',
            'end_time': '15:00'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Booking.objects.filter(title='Nouvelle résa').exists())

    def test_calendar_view(self):
        self.client.login(username='user', password='pass')
        response = self.client.get(reverse('bookings:calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Calendrier')

    def test_api_bookings_json(self):
        self.client.login(username='user', password='pass')
        start = self.tomorrow.strftime('%Y-%m-%d')
        end = (self.tomorrow + timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.get(f"{reverse('bookings:api_bookings')}?start={start}&end={end}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Ma résa — Salle V')
