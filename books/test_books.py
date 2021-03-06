from datetime import datetime
from unittest import mock

from django.core.urlresolvers import reverse
from django.test import Client
from django.test import TestCase

import pytz

from books.factories import DebtLoanFactory
from books.factories import TransactionFactory
from books.factories import UserFactory
from books.models import DebtLoan
from books.models import Transaction
from books import services


class TransactionTests(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_create_model(self):
        self.assertEqual(0, Transaction.objects.count())
        TransactionFactory(title='first')
        self.assertEqual(1, Transaction.objects.count())
        self.assertEqual(str(Transaction.objects.latest('id')), 'first')

    def test_transaction_create_get(self):
        c = Client()
        logged_in = c.login(username=self.user.username, password='secret')
        self.assertTrue(logged_in)

        response = c.get(reverse('transaction_create'))
        self.assertEqual(200, response.status_code)

    def test_transaction_create_post(self):
        c = Client()
        logged_in = c.login(username=self.user.username, password='secret')
        self.assertTrue(logged_in)

        self.assertEqual(0, Transaction.objects.count())
        response = c.post(reverse('transaction_create'),
                          {'title': 'forty-two',
                           'amount': 42,
                           'category': Transaction.EXPENSE},
                          follow=True)
        self.assertRedirects(response, reverse('transaction_list'))
        self.assertEqual(1, Transaction.objects.count())
        self.assertEqual('forty-two', Transaction.objects.latest('id').title)
        self.assertEqual(42, Transaction.objects.latest('id').amount)

    def test_transaction_update_get(self):
        c = Client()
        logged_in = c.login(username=self.user.username, password='secret')
        self.assertTrue(logged_in)

        t = TransactionFactory(title='first',
                               amount=1,
                               category=Transaction.EXPENSE)
        self.assertEqual(1, Transaction.objects.count())

        response = c.get(reverse('transaction_update', args=[t.id]))
        self.assertEqual(200, response.status_code)

    def test_transaction_update_post(self):
        c = Client()
        logged_in = c.login(username=self.user.username, password='secret')
        self.assertTrue(logged_in)

        t = TransactionFactory(title='first',
                               amount=1,
                               category=Transaction.EXPENSE)
        self.assertEqual(1, Transaction.objects.count())

        response = c.post(reverse('transaction_update', args=[t.id]),
                          {'title': 'forty-two',
                           'amount': 42,
                           'category': Transaction.EXPENSE},
                          follow=True)
        self.assertRedirects(response, reverse('transaction_list'))
        self.assertEqual(1, Transaction.objects.count())
        self.assertEqual('forty-two', Transaction.objects.latest('id').title)
        self.assertEqual(42, Transaction.objects.latest('id').amount)

    def test_transaction_delete(self):
        c = Client()
        logged_in = c.login(username=self.user.username, password='secret')
        self.assertTrue(logged_in)

        t = TransactionFactory(title='first',
                               amount=1,
                               category=Transaction.EXPENSE)
        self.assertEqual(1, Transaction.objects.count())
        self.assertTrue(Transaction.objects.all()[0].active)

        response = c.get(reverse('transaction_delete', args=[t.id]))
        self.assertRedirects(response, reverse('transaction_list'))

        self.assertEqual(1, Transaction.objects.count())
        self.assertFalse(Transaction.objects.all()[0].active)


class TransactionFilterTests(TestCase):
    def setUp(self):
        self.user = UserFactory()

        self.this_month = TransactionFactory(
            title='this_month',
            created=datetime(2015, 4, 23, tzinfo=pytz.utc),
            user=self.user,
        )

        self.last_month = TransactionFactory(
            title='last_month',
            created=datetime(2015, 3, 23, tzinfo=pytz.utc),
            user=self.user,
        )

        self.this_year = TransactionFactory(
            title='this_year',
            created=datetime(2015, 1, 23, tzinfo=pytz.utc),
            user=self.user,
        )

        self.last_year = TransactionFactory(
            title='this_year',
            created=datetime(2014, 1, 23, tzinfo=pytz.utc),
            user=self.user,
        )


    def test_this_months_transactions(self):
        with mock.patch('books.services.timezone') as mock_now:
            mock_now.now.return_value = datetime(2015, 4, 23, tzinfo=pytz.utc)

            transactions = services.get_months_transactions(self.user)
            # make test deterministic
            transactions = transactions.order_by("-created")

            self.assertEqual(len(transactions), 1)
            self.assertEqual(transactions[0].title, 'this_month')

    def test_this_months_transactions_list(self):
        with mock.patch('books.services.timezone') as mock_now:
            mock_now.now.return_value = datetime(2015, 4, 23, tzinfo=pytz.utc)

            c = Client()
            logged_in = c.login(username=self.user.username, password='secret')
            self.assertTrue(logged_in)

            response = c.get(reverse('transaction_list'))
            self.assertEqual(200, response.status_code)

            qs = response.context['transactions']
            self.assertSequenceEqual(qs, [self.this_month])

    def test_last_months_transactions(self):
        with mock.patch('books.services.timezone') as mock_now:
            mock_now.now.return_value = datetime(2015, 4, 23, tzinfo=pytz.utc)

            transactions = services.get_last_months_transactions(self.user)
            # make test deterministic
            transactions = transactions.order_by("-created")

            self.assertEqual(len(transactions), 2)
            self.assertEqual(transactions[0].title, 'this_month')
            self.assertEqual(transactions[1].title, 'last_month')

    def test_last_months_transactions_list(self):
        with mock.patch('books.services.timezone') as mock_now:
            mock_now.now.return_value = datetime(2015, 4, 23, tzinfo=pytz.utc)

            c = Client()
            logged_in = c.login(username=self.user.username, password='secret')
            self.assertTrue(logged_in)

            response = c.get(reverse('transaction_list_filter'),
                             {'filter': 'last_month'},
                             follow=True)
            self.assertRedirects(response, reverse('transaction_list'))

            qs = response.context['transactions']
            self.assertSequenceEqual(qs, [self.this_month, self.last_month])

    def test_this_years_transactions(self):
        with mock.patch('books.services.timezone') as mock_now:
            mock_now.now.return_value = datetime(2015, 4, 23, tzinfo=pytz.utc)

            transactions = services.get_this_years_transactions(self.user)
            # make test deterministic
            transactions = transactions.order_by("-created")

            self.assertEqual(len(transactions), 3)
            self.assertEqual(transactions[0].title, 'this_month')
            self.assertEqual(transactions[1].title, 'last_month')
            self.assertEqual(transactions[2].title, 'this_year')

    def test_this_years_transactions_list(self):
        with mock.patch('books.services.timezone') as mock_now:
            mock_now.now.return_value = datetime(2015, 4, 23, tzinfo=pytz.utc)

            c = Client()
            logged_in = c.login(username=self.user.username, password='secret')
            self.assertTrue(logged_in)

            response = c.get(reverse('transaction_list_filter'),
                             {'filter': 'this_year'},
                             follow=True)
            self.assertRedirects(response, reverse('transaction_list'))

            qs = response.context['transactions']
            self.assertSequenceEqual(
                qs,
                [self.this_month, self.last_month, self.this_year]
            )

    def test_all_time_transactions_list(self):
        with mock.patch('books.services.timezone') as mock_now:
            mock_now.now.return_value = datetime(2015, 4, 23, tzinfo=pytz.utc)

            c = Client()
            logged_in = c.login(username=self.user.username, password='secret')
            self.assertTrue(logged_in)

            response = c.get(reverse('transaction_list_filter'),
                             {'filter': 'all_time'},
                             follow=True)
            self.assertRedirects(response, reverse('transaction_list'))

            qs = response.context['transactions']
            self.assertSequenceEqual(
                qs,
                [self.this_month, self.last_month, self.this_year, self.last_year]
            )


class DebtLoanTests(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_create_model(self):
        self.assertEqual(0, DebtLoan.objects.count())
        DebtLoanFactory(title='first')
        self.assertEqual(1, DebtLoan.objects.count())
        self.assertEqual(str(DebtLoan.objects.latest('id')), 'ACME co.: first')

        DebtLoanFactory(title=None)
        self.assertEqual(2, DebtLoan.objects.count())
        self.assertEqual(str(DebtLoan.objects.latest('id')), 'ACME co.')

    def test_debt_loan_create_get(self):
        c = Client()
        logged_in = c.login(username=self.user.username, password='secret')
        self.assertTrue(logged_in)

        response = c.get(reverse('debt_loan_create'))
        self.assertEqual(200, response.status_code)

    def test_debt_loan_create_post(self):
        c = Client()
        logged_in = c.login(username=self.user.username, password='secret')
        self.assertTrue(logged_in)

        self.assertEqual(0, DebtLoan.objects.count())
        response = c.post(reverse('debt_loan_create'),
                          {'with_who': 'FooBar inc.',
                           'title': 'forty-two',
                           'amount': 42,
                           'category': DebtLoan.LOAN},
                          follow=True)
        self.assertRedirects(response, reverse('debt_loan_list'))
        self.assertEqual(1, DebtLoan.objects.count())
        self.assertEqual('forty-two', DebtLoan.objects.latest('id').title)
        self.assertEqual(42, DebtLoan.objects.latest('id').amount)

    def test_debt_loan_update_get(self):
        c = Client()
        logged_in = c.login(username=self.user.username, password='secret')
        self.assertTrue(logged_in)

        t = DebtLoanFactory(title='first',
                            amount=1,
                            category=DebtLoan.LOAN)
        self.assertEqual(1, DebtLoan.objects.count())

        response = c.get(reverse('debt_loan_update', args=[t.id]))
        self.assertEqual(200, response.status_code)

    def test_debt_loan_update_post(self):
        c = Client()
        logged_in = c.login(username=self.user.username, password='secret')
        self.assertTrue(logged_in)

        t = DebtLoanFactory(title='first',
                            amount=1,
                            category=DebtLoan.LOAN)
        self.assertEqual(1, DebtLoan.objects.count())

        response = c.post(reverse('debt_loan_update', args=[t.id]),
                          {'with_who': 'FooBar inc.',
                           'title': 'forty-two',
                           'amount': 42,
                           'category': DebtLoan.LOAN},
                          follow=True)
        self.assertRedirects(response, reverse('debt_loan_list'))
        self.assertEqual(1, DebtLoan.objects.count())
        self.assertEqual('forty-two', DebtLoan.objects.latest('id').title)
        self.assertEqual(42, DebtLoan.objects.latest('id').amount)

    def test_debt_loan_delete(self):
        c = Client()
        logged_in = c.login(username=self.user.username, password='secret')
        self.assertTrue(logged_in)

        t = DebtLoanFactory(title='first',
                            amount=1,
                            category=DebtLoan.LOAN)
        self.assertEqual(1, DebtLoan.objects.count())
        self.assertTrue(DebtLoan.objects.all()[0].active)

        response = c.get(reverse('debt_loan_delete', args=[t.id]))
        self.assertRedirects(response, reverse('debt_loan_list'))

        self.assertEqual(1, DebtLoan.objects.count())
        self.assertFalse(DebtLoan.objects.all()[0].active)
