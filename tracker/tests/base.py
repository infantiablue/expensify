from django.test import TestCase
from tracker.models import User


class BaseTestCase(TestCase):
    def setUp(self):
        user1 = User.objects.create_user(
            'blue', 'truong.phan@outlook.com', '123456')
        self.client.login(username='blue', password='123456')
        self.response = self.client.get('/', follow=True)
        self.user = user1
        user2 = User.objects.create_user(
            'red', 'dangtruong@gmail.com', '123456')
        self.user2 = user2
