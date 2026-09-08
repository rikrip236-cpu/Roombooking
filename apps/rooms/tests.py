from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.rooms.models import Room, Equipment, RoomAvailability

User = get_user_model()


class RoomModelTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            name='Salle Test',
            capacity=10,
            description='Une salle de test',
            is_active=True
        )
        self.equipment = Equipment.objects.create(
            name='Projecteur',
            description='HD',
            icon='bi-projector'
        )
        self.room.equipment.add(self.equipment)

    def test_room_str(self):
        self.assertIn('Salle Test', str(self.room))
        self.assertIn('10 pers.', str(self.room))

    def test_room_equipment_relation(self):
        self.assertEqual(self.room.equipment.count(), 1)
        self.assertEqual(self.room.equipment.first().name, 'Projecteur')

    def test_room_ordering(self):
        Room.objects.create(name='Salle Alpha', capacity=5, is_active=True)
        rooms = list(Room.objects.all())
        self.assertEqual(rooms[0].name, 'Salle Alpha')
        self.assertEqual(rooms[1].name, 'Salle Test')


class RoomAvailabilityTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(name='Salle A', capacity=8, is_active=True)
        self.avail = RoomAvailability.objects.create(
            room=self.room,
            day_of_week=0,
            open_time='08:00',
            close_time='18:00',
            is_closed=False
        )

    def test_availability_str(self):
        self.assertIn('Salle A', str(self.avail))
        self.assertIn('Lundi', str(self.avail))

    def test_unique_together(self):
        with self.assertRaises(Exception):
            RoomAvailability.objects.create(
                room=self.room,
                day_of_week=0,
                open_time='09:00',
                close_time='17:00'
            )


class RoomViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='user', password='pass')
        self.admin = User.objects.create_user(username='admin', password='pass', role='admin')
        self.room = Room.objects.create(name='Salle Vue', capacity=5, is_active=True)

    def test_room_list_requires_login(self):
        response = self.client.get(reverse('rooms:room_list'))
        self.assertEqual(response.status_code, 302)

    def test_room_list_accessible_when_logged(self):
        self.client.login(username='user', password='pass')
        response = self.client.get(reverse('rooms:room_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Salle Vue')

    def test_room_create_requires_admin(self):
        self.client.login(username='user', password='pass')
        response = self.client.get(reverse('rooms:room_create'))
        self.assertEqual(response.status_code, 403)

    def test_room_create_accessible_to_admin(self):
        self.client.login(username='admin', password='pass')
        response = self.client.get(reverse('rooms:room_create'))
        self.assertEqual(response.status_code, 200)

    def test_room_create_post(self):
        self.client.login(username='admin', password='pass')
        response = self.client.post(reverse('rooms:room_create'), {
            'name': 'Nouvelle Salle',
            'capacity': 15,
            'description': 'Test',
            'is_active': True
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Room.objects.filter(name='Nouvelle Salle').exists())
