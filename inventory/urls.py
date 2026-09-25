from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/toggle-active/', views.product_toggle_active, name='product_toggle_active'),
    path('stock-in/', views.stock_in, name='stock_in'),
    path('movements/', views.stock_movement_list, name='stock_movement_list'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('products/import/', views.product_bulk_upload, name='product_bulk_upload'),
]
