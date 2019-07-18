from django.db import connection
from django.test import TestCase
from .models import User


class UserTestCase(TestCase):
    def setUp(self):
        User.objects.create(name="Test UserA", email="test1@pleio.nl")
        User.objects.create(name="Test UserB", email="test2@pleio.nl")
        User.objects.create(name="Test UserC", email="test3@pleio.nl")

    def test_users(self):
        userA = User.objects.get(name="Test UserB")

        self.assertEqual(userA.email, 'test2@pleio.nl')
        self.assertEqual(userA.guid, 'user:2')
        self.assertEqual(userA.get_full_name(), 'Test UserB')
        self.assertEqual(User.objects.all().count(), 3)
