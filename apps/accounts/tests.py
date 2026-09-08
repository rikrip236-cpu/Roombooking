from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Jean',
            last_name='Dupont',
            role='user'
        )
        self.admin = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        self.superuser = User.objects.create_superuser(
            username='superuser',
            email='super@example.com',
            password='superpass123'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.role, 'user')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_is_admin_for_standard_user(self):
        self.assertFalse(self.user.is_admin())

    def test_is_admin_for_admin_role(self):
        self.assertTrue(self.admin.is_admin())

    def test_is_admin_for_superuser(self):
        self.assertTrue(self.superuser.is_admin())

    def test_is_standard_user(self):
        self.assertTrue(self.user.is_standard_user())
        self.assertFalse(self.admin.is_standard_user())
        self.assertFalse(self.superuser.is_standard_user())

    def test_full_name(self):
        self.assertEqual(self.user.get_full_name(), 'Jean Dupont')


class UserAuthViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

    def test_login_view(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_successful_login(self):
        response = self.client.post('/accounts/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)

    def test_register_view(self):
        response = self.client.get('/accounts/register/')
        self.assertEqual(response.status_code, 200)

    def test_successful_registration(self):
        response = self.client.post('/accounts/register/', {
            'username': 'newuser',
            'first_name': 'Marie',
            'last_name': 'Curie',
            'email': 'marie@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
