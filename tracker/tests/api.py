import json
import datetime
from tracker.models import Transaction, Category
from tracker.tests.base import BaseTestCase


class ApiTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_unauthorized_user_api(self):
        response = self.client.post('/api/transaction')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': 'You are not authorized.'}
        )
        response = self.client.post('/api/reports')
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
        response = self.client.post('/api/transactions')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': 'You are not authorized.'}
        )

    def test_unauthenticated_user_api(self):
        self.client.logout()
        response = self.client.get('/api/balance')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': 'You are not authenticated.'}
        )
        response = self.client.post('/api/transactions')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': 'You are not authenticated.'}
        )
        response = self.client.get('/api/transaction')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': 'You are not authenticated.'}
        )
        response = self.client.delete('/api/transaction')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': 'You are not authenticated.'}
        )
        response = self.client.delete('/api/transactions')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': 'You are not authenticated.'}
        )
        response = self.client.delete('/api/category')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': 'You are not authenticated.'}
        )

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
        response = self.client.get('/api/reports')

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
        response = self.client.get('/api/reports?source=income')

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

    def test_get_transactions_per_page(self):
        t = {}
        '''Quickly create 11 transactions'''
        for i in range(1, 12):
            t[i] = Transaction(text=f'income{i}', amount=50*i, user=self.user)
            t[i].save()
        response = self.client.get('/api/transactions')
        self.assertEqual(response.status_code, 200)
        '''The latest transaction is sorted by time created'''
        self.assertEqual(json.loads(response.content)[0]['text'], 'income11')
        self.assertEqual(json.loads(response.content)[0]['amount'], 50 * 11)
        self.assertEqual(json.loads(response.content)[4]['text'], 'income7')
        self.assertEqual(json.loads(response.content)[4]['amount'], 50 * 7)

        with self.assertRaisesRegexp(IndexError, 'list index out of range'):
            self.assertEqual(json.loads(response.content)
                             [5]['text'], 'income6')
        response = self.client.get('/api/transactions?page=2')
        self.assertEqual(json.loads(response.content)[0]['text'], 'income6')
        self.assertEqual(json.loads(response.content)[0]['amount'], 50 * 6)
        response = self.client.get('/api/transactions?page=4')
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': 'End of transactions.'}
        )

    def test_get_transactions_per_page_with_category(self):
        t = {}
        cat_income = Category(title='Interest', user=self.user2)
        cat_income.save()
        '''Quickly create 11 transactions'''
        for i in range(1, 11):
            t[i] = Transaction(
                text=f'income{i}', amount=50*i, category=cat_income, user=self.user)
            t[i].save()
        response = self.client.get('/api/transactions')
        self.assertEqual(response.status_code, 200)
        '''The latest transaction is sorted by time created'''
        self.assertEqual(json.loads(response.content)[0]['text'], 'income10')
        self.assertEqual(json.loads(response.content)
                         [0]['category_title'], 'Interest')
