from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTest(TestCase):
    def test_create_cashier(self):
        user = User.objects.create_user(
            username='cashier1',
            password='password123',
            role=User.Role.CASHIER
        )
        self.assertEqual(user.role, User.Role.CASHIER)
        self.assertTrue(user.is_cashier_role)
        self.assertFalse(user.is_admin_role)

    def test_create_admin(self):
        user = User.objects.create_user(
            username='admin_staff',
            password='password123',
            role=User.Role.ADMIN
        )
        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertTrue(user.is_admin_role)
        self.assertFalse(user.is_cashier_role)

    def test_superuser_is_admin_role(self):
        superuser = User.objects.create_superuser(
            username='superuser',
            password='password123',
            email='superuser@example.com'
        )
        self.assertEqual(superuser.role, User.Role.ADMIN)
        self.assertTrue(superuser.is_admin_role)


class StaffManagementViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin_boss',
            password='password123',
            role=User.Role.ADMIN,
            is_staff=True
        )
        self.cashier_user = User.objects.create_user(
            username='cashier_alice',
            password='password123',
            role=User.Role.CASHIER
        )

    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_cashier_cannot_access_staff_management(self):
        self.client.login(username='cashier_alice', password='password123')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_admin_can_access_staff_management(self):
        self.client.login(username='admin_boss', password='password123')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cashier_alice')
        self.assertContains(response, 'admin_boss')

    def test_admin_create_new_cashier(self):
        self.client.login(username='admin_boss', password='password123')
        response = self.client.post(reverse('accounts:user_create'), {
            'username': 'bob_cashier',
            'first_name': 'Bob',
            'last_name': 'Smith',
            'email': 'bob@example.com',
            'role': User.Role.CASHIER,
            'password': 'ComplexPassword123!',
            'confirm_password': 'ComplexPassword123!',
        })
        self.assertRedirects(response, reverse('accounts:user_list'))
        bob = User.objects.get(username='bob_cashier')
        self.assertEqual(bob.first_name, 'Bob')
        self.assertEqual(bob.role, User.Role.CASHIER)
        self.assertTrue(bob.check_password('ComplexPassword123!'))

    def test_admin_toggle_user_status(self):
        self.client.login(username='admin_boss', password='password123')
        self.assertTrue(self.cashier_user.is_active)
        
        # Deactivate
        response = self.client.post(reverse('accounts:user_toggle_status', args=[self.cashier_user.pk]))
        self.assertRedirects(response, reverse('accounts:user_list'))
        self.cashier_user.refresh_from_db()
        self.assertFalse(self.cashier_user.is_active)

        # Activate again
        response = self.client.post(reverse('accounts:user_toggle_status', args=[self.cashier_user.pk]))
        self.assertRedirects(response, reverse('accounts:user_list'))
        self.cashier_user.refresh_from_db()
        self.assertTrue(self.cashier_user.is_active)

    def test_admin_cannot_deactivate_self(self):
        self.client.login(username='admin_boss', password='password123')
        response = self.client.post(reverse('accounts:user_toggle_status', args=[self.admin_user.pk]))
        self.assertRedirects(response, reverse('accounts:user_list'))
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_active)

    def test_user_logout(self):
        self.client.login(username='cashier_alice', password='password123')
        response = self.client.post(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('accounts:login'))
