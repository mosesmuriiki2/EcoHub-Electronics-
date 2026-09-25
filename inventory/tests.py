from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from inventory.models import Category, Product, StockMovement

User = get_user_model()


class InventoryModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin_inv', password='password123', role=User.Role.ADMIN)
        self.category = Category.objects.create(name='Accessories', description='Cables and chargers')

    def test_product_creation_and_sku(self):
        product = Product.objects.create(
            name='USB-C Cable',
            sku='CABLE-001',
            category=self.category,
            cost_price=3.50,
            selling_price=10.00,
            reorder_level=5
        )
        self.assertEqual(product.quantity_in_stock, 0)
        self.assertTrue(product.is_out_of_stock)
        self.assertFalse(product.is_low_stock)

    def test_stock_movement_atomic_updates(self):
        product = Product.objects.create(
            name='HDMI Cable',
            sku='HDMI-001',
            selling_price=12.00,
            reorder_level=5
        )
        # 1. Stock In: 20 units
        StockMovement.objects.create(
            product=product,
            movement_type=StockMovement.MovementType.STOCK_IN,
            quantity=20,
            reference='Batch 1',
            created_by=self.user
        )
        product.refresh_from_db()
        self.assertEqual(product.quantity_in_stock, 20)
        self.assertFalse(product.is_low_stock)
        self.assertFalse(product.is_out_of_stock)

        # 2. Sale deduction: 16 units -> leaves 4 units (<= reorder level 5)
        StockMovement.objects.create(
            product=product,
            movement_type=StockMovement.MovementType.SALE,
            quantity=16,
            reference='Sale #1',
            created_by=self.user
        )
        product.refresh_from_db()
        self.assertEqual(product.quantity_in_stock, 4)
        self.assertTrue(product.is_low_stock)
        self.assertFalse(product.is_out_of_stock)

        # 3. Sale deduction: 4 units -> leaves 0
        StockMovement.objects.create(
            product=product,
            movement_type=StockMovement.MovementType.SALE,
            quantity=4,
            reference='Sale #2',
            created_by=self.user
        )
        product.refresh_from_db()
        self.assertEqual(product.quantity_in_stock, 0)
        self.assertTrue(product.is_out_of_stock)


class InventoryViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username='admin_user', password='password123', role=User.Role.ADMIN)
        self.cashier = User.objects.create_user(username='cashier_user', password='password123', role=User.Role.CASHIER)
        self.product = Product.objects.create(
            name='Wireless Mouse',
            sku='MOUSE-001',
            cost_price=8.00,
            selling_price=20.00,
            reorder_level=5
        )

    def test_both_admin_and_cashier_can_view_inventory(self):
        # Cashier
        self.client.login(username='cashier_user', password='password123')
        response = self.client.get(reverse('inventory:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Wireless Mouse')

        # Admin
        self.client.login(username='admin_user', password='password123')
        response = self.client.get(reverse('inventory:product_list'))
        self.assertEqual(response.status_code, 200)

    def test_cashier_cannot_create_product(self):
        self.client.login(username='cashier_user', password='password123')
        response = self.client.get(reverse('inventory:product_create'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_admin_create_product_with_initial_stock(self):
        self.client.login(username='admin_user', password='password123')
        response = self.client.post(reverse('inventory:product_create'), {
            'name': 'Keyboard RGB',
            'sku': 'KB-RGB-01',
            'cost_price': '25.00',
            'selling_price': '45.00',
            'reorder_level': 3,
            'initial_stock': 15,
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        kb = Product.objects.get(sku='KB-RGB-01')
        self.assertEqual(kb.quantity_in_stock, 15)
        # Ensure StockMovement was recorded
        self.assertTrue(StockMovement.objects.filter(product=kb, movement_type='stock_in', quantity=15).exists())

    def test_admin_stock_in_view(self):
        self.client.login(username='admin_user', password='password123')
        response = self.client.post(reverse('inventory:stock_in'), {
            'product': self.product.pk,
            'quantity': 25,
            'reference': 'Supplier PO-9921',
        })
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, 25)
