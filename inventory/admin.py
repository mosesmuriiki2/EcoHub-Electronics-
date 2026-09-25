from django.contrib import admin
from .models import Category, Product, StockMovement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'selling_price', 'cost_price', 'quantity_in_stock', 'reorder_level', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'sku')
    readonly_fields = ('quantity_in_stock',)  # Stock is only modified via StockMovement


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'movement_type', 'quantity', 'reference', 'created_by', 'created_at')
    list_filter = ('movement_type', 'created_at')
    search_fields = ('product__name', 'product__sku', 'reference')
    readonly_fields = ('product', 'movement_type', 'quantity', 'reference', 'created_by', 'created_at')
