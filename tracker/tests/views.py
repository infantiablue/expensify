import os
from tracker.models import Category
from django.test import override_settings
from django.urls import reverse
from tracker.tests.base import BaseTestCase


# Override MEDIA_ROOT so that there is no conflict with the current media folder
@override_settings(MEDIA_ROOT=f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/tests/fixtures/media')
class ViewsTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_unauthenticated_user(self):
        response = self.client.get(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('transactions'))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('account'))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('categories'))
        self.assertEqual(response.status_code, 302)

    def test_transactions_view(self):
        response = self.client.get(reverse('transactions'))
        self.assertNotContains(response, self.user.username)
        self.assertNotContains(response, 'BALANCE')
        self.assertNotContains(response, 'More')

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
        self.assertContains(response, 'Reports')
