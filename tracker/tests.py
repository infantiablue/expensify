import os
import json
import datetime
from PIL import Image
from django.conf import settings
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from .models import User, Transaction, Category, Balance
from django.test import TestCase, override_settings
from django.urls import reverse


# Override MEDIA_ROOT so that there is no conflict with the current media folder
@override_settings(MEDIA_ROOT=f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/media/test/media')
class UserTestCase(TestCase):
    def setUp(self):
        user1 = User.objects.create_user(
            'blue', 'truong.phan@outlook.com', '123456')
        self.client.login(username='blue', password='123456')
        self.response = self.client.get('/', follow=True)
        self.user = user1
        user2 = User.objects.create_user(
            'red', 'dangtruong@gmail.com', '123456')
        self.user2 = user2

    def test_unauthenticated_user(self):
        response = self.client.post('/api/transaction')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': 'You are not authorized.'}
        )
        response = self.client.post('/api/category')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': 'You are not authorized.'}
        )
        self.client.logout()
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('account'))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('categories'))
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/api/balance')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': 'You are not authorized.'}
        )
        response = self.client.get('/api/transaction')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': 'You are not authorized.'}
        )
        response = self.client.delete('/api/transaction')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': 'You are not authorized.'}
        )
        response = self.client.delete('/api/category')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': 'You are not authorized.'}
        )

    def test_index_view_logged_in(self):
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'blue')

    def test_account_view(self):
        response = self.client.get(reverse('account'))
        self.assertEqual(self.user.email, 'truong.phan@outlook.com')
        self.assertEqual(response.status_code, 200)

    def test_categories_view(self):
        cat_income = Category(title='Interest', user=self.user)
        cat_expense = Category(
            title='Utilities', source='expense', user=self.user)
        cat_income.save()
        cat_expense.save()
        response = self.client.get(reverse('categories'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('categories', response.context)

    def test_category_view(self):
        cat_income = Category(title='Interest', user=self.user)
        cat_expense = Category(
            title='Utilities', source='expense', user=self.user)
        cat_income.save()
        cat_expense.save()
        response = self.client.get(
            reverse('category', kwargs={'id': cat_income.id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('category', response.context)

    def test_report_view(self):
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reports', html=True)

    def test_authenticated_user(self):
        self.assertEqual(self.user.username, 'blue')

    def test_user_initial_balance(self):
        self.assertEqual(self.user.get_balance(), 0)
        transaction = Transaction(
            text='income1', amount=500, user=self.user)
        transaction.save()
        balance = Balance.objects.filter(user=self.user).first()
        self.assertEqual(str(balance), '$ 500.0')

    def test_income_transactions(self):
        transaction1 = Transaction(
            text='income1', amount=500, user=self.user)
        transaction2 = Transaction(
            text='income2', amount=500, user=self.user)
        transaction1.save()
        transaction2.save()
        self.assertEqual(self.user.get_balance(), 1000)
        self.assertEqual(self.user.get_total_income(), 1000)

    def test_expense_transactions(self):
        transaction1 = Transaction(
            text='income', amount=500, user=self.user)
        transaction2 = Transaction(
            text='expense1', amount=-100, user=self.user)
        transaction3 = Transaction(
            text='expense2', amount=-200, user=self.user)
        transaction1.save()
        transaction2.save()
        transaction3.save()

        self.assertEqual(self.user.get_balance(), 200)
        self.assertEqual(self.user.get_total_expense(), -300)

    def test_zero_transactions(self):
        transaction = Transaction(
            text='income', amount=0, user=self.user)
        with self.assertRaisesRegexp(ValidationError, 'The ammount should be different from 0.'):
            transaction.save()

    def test_auto_converted_transaction_with_category(self):
        cat_income = Category(title='Income', user=self.user, source='income')
        cat_expense = Category(
            title='Expense', user=self.user, source='expense')
        cat_income.save()
        cat_expense.save()
        transaction1 = Transaction(
            text='income', amount=-200, user=self.user, category=cat_income)
        transaction2 = Transaction(
            text='income', amount=100, user=self.user, category=cat_expense)
        transaction1.save()
        transaction2.save()

        self.assertEqual(self.user.get_balance(), 100)

    def test_expense_with_insufficient_account_transactions(self):
        transaction = Transaction(
            text='expense_1', amount=-200, user=self.user)
        with self.assertRaisesRegexp(ValidationError, 'Your balance is insufficient.'):
            transaction.save()

    def test_multiple_transactions(self):
        transaction1 = Transaction(
            text='income_1', amount=500, user=self.user)
        transaction2 = Transaction(
            text='expense_1', amount=-200, user=self.user)
        transaction1.save()
        transaction2.save()
        self.assertEqual(self.user.get_balance(), 300)

    def test_create_category(self):
        cat_income = Category(title='Interest', user=self.user)
        cat_expense = Category(
            title='Utilities', source='expense', user=self.user)
        cat_income.save()
        cat_expense.save()
        response = self.client.get('/categories')
        cat_titles = []
        for c in response.context['categories']:
            cat_titles.append(c.title)
        self.assertIn('Interest', cat_titles)
        self.assertIn('Utilities', cat_titles)
        self.assertEqual(str(cat_income), '(+) Interest')
        self.assertEqual(str(cat_expense), '(-) Utilities')

    def test_transactions_with_category(self):
        cat_income = Category(title='Interest', user=self.user)
        cat_expense = Category(
            title='Utilities', source='expense', user=self.user)
        cat_income.save()
        cat_expense.save()
        transaction1 = Transaction(
            text='income_1', amount=500, category=cat_income, user=self.user)
        transaction2 = Transaction(
            text='expense_1', amount=200, category=cat_expense, user=self.user)
        transaction1.save()
        transaction2.save()
        self.assertEqual(self.user.get_balance(), 300)

    def test_remove_transaction(self):
        transaction1 = Transaction(
            text='income_1', amount=500, user=self.user)
        transaction2 = Transaction(
            text='expense_1', amount=-200, user=self.user)
        transaction1.save()
        transaction2.save()
        self.assertEqual(self.user.get_balance(), 300)
        transaction2.delete()
        self.assertEqual(self.user.get_balance(), 500)

    def test_remove_transaction_with_insufficient_balance(self):
        transaction1 = Transaction(
            text='income_1', amount=500, user=self.user)
        transaction2 = Transaction(
            text='expense_1', amount=-200, user=self.user)
        transaction1.save()
        transaction2.save()
        self.assertEqual(self.user.get_balance(), 300)
        with self.assertRaisesRegexp(ValidationError, 'Your balance is insufficient.'):
            transaction1.delete()

    def test_remove_transactions_with_category(self):
        cat_income = Category(title='Interest', user=self.user)
        cat_expense = Category(
            title='Utilities', source='expense', user=self.user)
        cat_income.save()
        cat_expense.save()
        transaction1 = Transaction(
            text='income_1', amount=500, category=cat_income, user=self.user)
        transaction2 = Transaction(
            text='expense_1', amount=200, category=cat_expense, user=self.user)
        transaction3 = Transaction(
            text='expense_2', amount=100, category=cat_expense, user=self.user)
        transaction1.save()
        transaction2.save()
        transaction3.save()
        self.assertEqual(self.user.get_balance(), 200)
        cat_expense.delete()
        self.assertEqual(self.user.get_balance(), 500)

    def test_api_report_expense_transaction(self):
        cat_income = Category(title='Interest', user=self.user)
        cat_expense = Category(
            title='Utilities', source='expense', user=self.user)
        cat_income.save()
        cat_expense.save()
        transaction1 = Transaction(
            text='income_1', amount=500, category=cat_income, user=self.user)
        transaction2 = Transaction(
            text='expense_1', amount=200, category=cat_expense, user=self.user)
        transaction3 = Transaction(
            text='expense_2', amount=100, category=cat_expense, user=self.user)
        transaction1.save()
        transaction2.save()
        transaction3.save()
        response = self.client.get('/api/transaction')

        today = datetime.date.today()
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'amounts': [-300], 'time': [today.strftime("%Y-%m-%d")]}
        )

    def test_api_report_income_transaction(self):
        cat_income = Category(title='Interest', user=self.user)
        cat_expense = Category(
            title='Utilities', source='expense', user=self.user)
        cat_income.save()
        cat_expense.save()
        transaction1 = Transaction(
            text='income_1', amount=500, category=cat_income, user=self.user)
        transaction2 = Transaction(
            text='income_2', amount=200, category=cat_income, user=self.user)
        transaction3 = Transaction(
            text='expense_1', amount=100, category=cat_expense, user=self.user)
        transaction1.save()
        transaction2.save()
        transaction3.save()
        response = self.client.get('/api/transaction?source=income')

        today = datetime.date.today()
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'amounts': [700], 'time': [today.strftime("%Y-%m-%d")]}
        )

    def test_api_remove_transaction(self):
        cat_income = Category(title='Interest', user=self.user)
        cat_expense = Category(
            title='Utilities', source='expense', user=self.user)
        cat_income.save()
        cat_expense.save()
        transaction1 = Transaction(
            text='income_1', amount=500, category=cat_income, user=self.user)
        transaction2 = Transaction(
            text='income_2', amount=200, category=cat_income, user=self.user)
        transaction3 = Transaction(
            text='expense_1', amount=100, category=cat_expense, user=self.user)
        transaction1.save()
        transaction2.save()
        transaction3.save()
        self.assertEqual(self.user.get_balance(), 600)

        response = self.client.delete(
            '/api/transaction', json.dumps({'transaction_id': transaction3.id}),  format='json')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'message': 'Your transaction is removed.'})
        self.assertEqual(self.user.get_balance(), 700)

    def test_api_remove_category(self):
        cat_income = Category(title='Interest', user=self.user)
        cat_expense = Category(
            title='Utilities', source='expense', user=self.user)
        cat_income.save()
        cat_expense.save()
        transaction1 = Transaction(
            text='income_1', amount=500, category=cat_income, user=self.user)
        transaction2 = Transaction(
            text='income_2', amount=200, category=cat_income, user=self.user)
        transaction3 = Transaction(
            text='expense_1', amount=100, category=cat_expense, user=self.user)
        transaction1.save()
        transaction2.save()
        transaction3.save()
        self.assertEqual(self.user.get_balance(), 600)

        response = self.client.delete(
            '/api/category', json.dumps({'category_id': cat_expense.id}),  format='json')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'message': 'Your category is removed.'}
        )
        self.assertEqual(self.user.get_balance(), 700)

    def test_api_report_category_income(self):
        cat_1 = Category(title='Interest', user=self.user)
        cat_2 = Category(title='Jobs', user=self.user)
        cat_1.save()
        cat_2.save()
        transaction1 = Transaction(
            text='income_1', amount=500, category=cat_1, user=self.user)
        transaction2 = Transaction(
            text='income_2', amount=200, category=cat_2, user=self.user)
        transaction1.save()
        transaction2.save()
        response = self.client.get('/api/category?source=income')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)
                         ['titles'][1], 'Jobs')
        self.assertEqual(json.loads(response.content)
                         ['amounts'][0], 500)

    def test_api_report_category_expense(self):
        cat_1 = Category(title='Accessories', source='expense', user=self.user)
        cat_2 = Category(title='Utilities', source='expense', user=self.user)
        cat_1.save()
        cat_2.save()
        transaction0 = Transaction(
            text='income_1', amount=1000, user=self.user)
        transaction1 = Transaction(
            text='expense_1', amount=500, category=cat_1, user=self.user)
        transaction2 = Transaction(
            text='expense_2', amount=200, category=cat_2, user=self.user)
        transaction0.save()
        transaction1.save()
        transaction2.save()
        response = self.client.get('/api/category')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)
                         ['titles'][0], 'Accessories')
        self.assertEqual(json.loads(response.content)
                         ['amounts'][1], -200)

    def test_api_remove_category_from_unauthorized_user(self):
        cat_income = Category(title='Interest', user=self.user2)
        cat_income.save()
        response = self.client.delete(
            '/api/category', json.dumps({'category_id': cat_income.id}),  format='json')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': 'You are not authorized.'}
        )

    def test_api_remove_transaction_from_unauthorized_user(self):
        transaction1 = Transaction(
            text='income_1', amount=500, user=self.user2)
        transaction1.save()
        response = self.client.delete(
            '/api/transaction', json.dumps({'transaction_id': transaction1.id}),  format='json')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': 'You are not authorized.'}

        )

    def test_api_get_user_balance(self):
        transaction1 = Transaction(
            text='income', amount=500, user=self.user)
        transaction2 = Transaction(
            text='expense1', amount=-100, user=self.user)
        transaction3 = Transaction(
            text='expense2', amount=-200, user=self.user)
        transaction1.save()
        transaction2.save()
        transaction3.save()
        response = self.client.get('/api/balance')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'balance': 200}
        )
        self.assertEqual(self.user.get_balance(), 200)

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
            path='/register', data={'username': 'green', 'email': 'red@local.host', 'password': '123456', 'confirmation': '123456'})
        self.assertTrue(User.objects.filter(username='red').first())

    def test_form_register_new_user_wrong_confirmation(self):
        response = self.client.post(
            path='/register', data={'username': 'green', 'email': 'red@local.host', 'password': '123456', 'confirmation': '1234567'}, follow=True)
        self.assertContains(response, 'Passwords must match.', html=True)

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

    def test_create_user_with_duplicate_username(self):
        with self.assertRaisesRegexp(IntegrityError, 'UNIQUE constraint failed: tracker_user.username'):
            user = User.objects.create_user(
                'blue', 'truong.phan@abc.xyz', '123456')

    def test_create_user_with_duplicate_email(self):
        with self.assertRaisesRegexp(IntegrityError, 'UNIQUE constraint failed: tracker_user.email'):
            user = User.objects.create_user(
                'albert', 'truong.phan@outlook.com', '123456')
