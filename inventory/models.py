from django.db import models, transaction
from django.conf import settings
import uuid


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, unique=True, help_text="Unique Stock Keeping Unit or Barcode")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,null=True, blank=True, help_text="Purchase/Cost price")
    selling_price = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True,help_text="Retail selling price")
    quantity_in_stock = models.IntegerField(default=0, help_text="Current available stock; modified only via StockMovement")
    reorder_level = models.IntegerField(default=5, help_text="Minimum threshold before triggering low-stock alert")
    is_active = models.BooleanField(default=True, help_text="Active products appear in sales and catalog")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def is_low_stock(self) -> bool:
        """Returns True if stock is at or below reorder level (and > 0)."""
        return 0 < self.quantity_in_stock <= self.reorder_level

    @property
    def is_out_of_stock(self) -> bool:
        """Returns True if stock is zero or depleted."""
        return self.quantity_in_stock <= 0

    @classmethod
    def generate_unique_sku(cls, prefix="SKU-") -> str:
        """Generate a random unique SKU."""
        while True:
            candidate = f"{prefix}{uuid.uuid4().hex[:8].upper()}"
            if not cls.objects.filter(sku=candidate).exists():
                return candidate


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        STOCK_IN = 'stock_in', 'Stock In'
        SALE = 'sale', 'Sale'
        ADJUSTMENT = 'adjustment', 'Adjustment'

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity = models.IntegerField(help_text="Quantity delta: positive for incoming/stock_in, positive/negative for adjustments")
    reference = models.CharField(max_length=150, blank=True, help_text="e.g. Supplier invoice, Sale INV-0001, Correction")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_movement_type_display()} ({self.quantity}) - {self.product.name}"

    def save(self, *args, **kwargs):
        """
        Record the stock movement and update the Product's quantity_in_stock
        atomically to maintain complete audit trail consistency.
        """
        is_new = self.pk is None
        with transaction.atomic():
            super().save(*args, **kwargs)
            if is_new:
                # Lock row for update
                product = Product.objects.select_for_update().get(pk=self.product_id)
                if self.movement_type == self.MovementType.STOCK_IN:
                    product.quantity_in_stock += abs(self.quantity)
                elif self.movement_type == self.MovementType.SALE:
                    product.quantity_in_stock -= abs(self.quantity)
                elif self.movement_type == self.MovementType.ADJUSTMENT:
                    # Adjustment quantity can be positive or negative
                    product.quantity_in_stock += self.quantity

                product.save(update_fields=['quantity_in_stock', 'updated_at'])
                # Sync self.product instance
                self.product.quantity_in_stock = product.quantity_in_stock
