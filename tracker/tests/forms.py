import os
from PIL import Image
from django.conf import settings
from tracker.models import User
from django.test import override_settings
from tracker.tests.base import BaseTestCase


# Override MEDIA_ROOT so that there is no conflict with the current media folder
@override_settings(MEDIA_ROOT=f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/tests/fixtures/media')
class FormsTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_form_create_new_transaction(self):
        self.client.post('/', {'text': 'Freelance', 'amount': 500})
        self.client.post('/', {'text': 'Starbucks', 'amount': -50})
        self.assertEqual(self.user.get_balance(), 450)

    def test_form_add_new_category(self):
        self.client.post(
            '/categories', {'title': 'Jobs', 'source': 'income'})
        self.client.post(
            '/categories', {'title': 'Drinks', 'source': 'expense'})
        response = self.client.get('/categories')
        self.assertContains(response, "Jobs", html=True)
        self.assertContains(response, "Drinks", html=True)

    def test_form_change_name(self):
        self.client.post(
            path='/account', data={'first_name': 'Truong', 'last_name': 'Phan', 'email': 'dangtruong@gmail.com'})
        user = User.objects.get(pk=1)
        self.assertEqual(user.first_name, 'Truong')
        self.assertEqual(user.last_name, 'Phan')
        self.assertEqual(user.username, 'blue')

    def test_form_upload_avatar(self):
        with open(f'{settings.MEDIA_ROOT}/test/valid.png', 'rb')as fp:
            self.client.post(
                '/account', data={'first_name': 'Truong', 'last_name': 'Phan', 'avatar': fp})
        user = User.objects.get(pk=1)
        img = Image.open(f'{settings.MEDIA_ROOT}/{user.avatar.name}')
        fw, fh = img.size
        self.assertEqual(fw, 128)
        self.assertEqual(fh, 128)
        self.assertEqual(user.avatar.name, 'user_1/avatar/md.png')

    def test_form_register_new_user(self):
        self.client.post(
            path='/register', data={'username': 'green', 'email': 'green@local.host', 'password': '123456', 'confirmation': '123456'})
        self.assertTrue(User.objects.filter(username='green').first())

    def test_form_register_new_user_wrong_confirmation(self):
        response = self.client.post(
            path='/register', data={'username': 'green', 'email': 'green@local.host', 'password': '123456', 'confirmation': '1234567'}, follow=True)
        self.assertContains(response, 'Passwords must match.')

    def test_form_register_new_user_duplicate_username(self):
        self.client.logout()
        response = self.client.post(
            path='/register', data={'username': 'blue', 'email': 'red@local.host', 'password': '123456', 'confirmation': '123456'}, follow=True)
        self.assertContains(
            response, 'Username already taken.', html=True)

    def test_form_register_new_user_duplicate_email(self):
        self.client.logout()
        response = self.client.post(
            path='/register', data={'username': 'green', 'email': 'truong.phan@outlook.com', 'password': '123456', 'confirmation': '123456'}, follow=True)
        self.assertContains(
            response, 'Username already taken.', html=True)

    def test_form_login_user(self):
        response = self.client.post(
            path='/login', data={'username': 'blue', 'password': '123456'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'blue')

    def test_form_new_transaction(self):
        response = self.client.post(
            path='/', data={'text': 'Jobs', 'amount': '3000', 'user': self.user}, follow=True)
        self.assertContains(
            response, 'Your transaction has been recorded.')

    def test_form_new_transaction_insufficient_balance(self):
        response = self.client.post(
            path='/', data={'text': 'Macbook', 'amount': '-3000', 'user': self.user}, follow=True)
        self.assertContains(
            response, 'Your balance is insufficient.')

    def test_form_login_user_wrong(self):
        response = self.client.post(
            path='/login', data={'username': 'blue', 'password': '12345678'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, 'Invalid username and/or password.', html=True)
        response = self.client.post(
            path='/login', data={'username': 'blueT', 'password': '123456'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, 'Invalid username and/or password.', html=True)

    def test_form_upload_invalid_avatars(self):
        with open(f'{settings.MEDIA_ROOT}/test/large.jpg', 'rb')as fp:
            response = self.client.post(
                '/account', data={'first_name': 'Albert', 'last_name': 'Phan', 'avatar': fp})
            self.assertContains(
                response, 'Height or Width is larger than what is allowed (1920x1920)', html=True)

        with open(f'{settings.MEDIA_ROOT}/test/small.jpg', 'rb')as fp:
            response = self.client.post(
                '/account', data={'first_name': 'Albert', 'last_name': 'Phan', 'avatar': fp})
            self.assertContains(
                response, 'Height or Width is smaller than what is allowed (128x128)', html=True)

        with open(f'{settings.MEDIA_ROOT}/test/oversize.jpg', 'rb')as fp:
            response = self.client.post(
                '/account', data={'first_name': 'Albert', 'last_name': 'Phan', 'avatar': fp})
            self.assertContains(
                response, 'Image size is larger than what is allowed (2048 KBs)', html=True)

        with open(f'{settings.MEDIA_ROOT}/test/notalllowed.pdf', 'rb')as fp:
            response = self.client.post(
                '/account', data={'first_name': 'Albert', 'last_name': 'Phan', 'avatar': fp})
            self.assertContains(
                response, 'Upload a valid image. The file you uploaded was either not an image or a corrupted image.', html=True)
