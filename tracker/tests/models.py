from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from tracker.models import User, Transaction, Category, Balance
from tracker.tests.base import BaseTestCase


class ModelsTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

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

    def test_create_user_with_duplicate_username(self):
        with self.assertRaisesRegexp(IntegrityError, 'UNIQUE constraint failed: tracker_user.username'):
            user = User.objects.create_user(
                'blue', 'truong.phan@abc.xyz', '123456')

    def test_create_user_with_duplicate_email(self):
        with self.assertRaisesRegexp(IntegrityError, 'UNIQUE constraint failed: tracker_user.email'):
            user = User.objects.create_user(
                'albert', 'truong.phan@outlook.com', '123456')
