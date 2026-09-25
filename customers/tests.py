from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from customers.models import Customer

User = get_user_model()


class CustomerModelTests(TestCase):
    def test_customer_creation(self):
        c = Customer.objects.create(
            name='Safari Tech Ltd',
            phone='+254 700 111 222',
            email='info@safaritech.co.ke',
            address='Moi Avenue, Nairobi',
            notes='VIP corporate client'
        )
        self.assertEqual(str(c), 'Safari Tech Ltd (+254 700 111 222)')
        self.assertTrue(Customer.objects.filter(name='Safari Tech Ltd').exists())


class CustomerViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username='admin_c', password='password123', role=User.Role.ADMIN)
        self.cashier = User.objects.create_user(username='cashier_c', password='password123', role=User.Role.CASHIER)
        self.customer = Customer.objects.create(
            name='Alice Johnson',
            phone='0712345678',
            email='alice@example.com',
            address='Kenyatta Ave'
        )

    def test_both_admin_and_cashier_can_access_customers(self):
        # Cashier
        self.client.login(username='cashier_c', password='password123')
        response = self.client.get(reverse('customers:customer_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alice Johnson')

        # Admin
        self.client.login(username='admin_c', password='password123')
        response = self.client.get(reverse('customers:customer_list'))
        self.assertEqual(response.status_code, 200)

    def test_search_customer(self):
        self.client.login(username='cashier_c', password='password123')
        # Matching search
        response = self.client.get(reverse('customers:customer_list') + '?q=Alice')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alice Johnson')

        # Non-matching search
        response = self.client.get(reverse('customers:customer_list') + '?q=NonExistent')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Alice Johnson')

    def test_cashier_can_create_customer(self):
        self.client.login(username='cashier_c', password='password123')
        response = self.client.post(reverse('customers:customer_create'), {
            'name': 'Brian Omondi',
            'phone': '0722000000',
            'email': 'brian@example.com',
            'address': 'Westlands',
            'notes': '',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Customer.objects.filter(name='Brian Omondi').exists())

    def test_customer_json_search(self):
        self.client.login(username='cashier_c', password='password123')
        response = self.client.get(reverse('customers:customer_search_json') + '?term=0712')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['name'], 'Alice Johnson')
