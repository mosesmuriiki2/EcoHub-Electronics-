from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q, F
from django.core.paginator import Paginator
from .models import Product, Category, StockMovement
from .forms import ProductForm, CategoryForm, StockInForm, ProductExcelUploadForm
from accounts.decorators import admin_required
import openpyxl
from django.db import transaction
from .utils import generate_sku

@login_required
def product_list(request):
    """
    List products with stock levels, low-stock alerts, search and filtering.
    Accessible to both Admins and Cashiers.
    """
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    stock_status = request.GET.get('stock_status', '').strip()

    products = Product.objects.select_related('category').all().order_by('name')

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    if stock_status == 'low':
        products = products.filter(quantity_in_stock__lte=F('reorder_level'), quantity_in_stock__gt=0)
    elif stock_status == 'out':
        products = products.filter(quantity_in_stock__lte=0)
    elif stock_status == 'adequate':
        products = products.filter(quantity_in_stock__gt=F('reorder_level'))

    # Counts
    total_products = Product.objects.count()
    low_stock_count = Product.objects.filter(quantity_in_stock__lte=F('reorder_level'), quantity_in_stock__gt=0).count()
    out_of_stock_count = Product.objects.filter(quantity_in_stock__lte=0).count()

    paginator = Paginator(products, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'category_id': category_id,
        'stock_status': stock_status,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
    }
    return render(request, 'inventory/product_list.html', context)


@login_required
def product_detail(request, pk):
    """View details of a single product and its movement history."""
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk)
    movements = product.stock_movements.select_related('created_by')[:20]

    return render(request, 'inventory/product_detail.html', {
        'product': product,
        'movements': movements,
    })


@admin_required
def product_create(request):
    """Admin-only: Create a new product with optional starting stock."""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            initial_stock = form.cleaned_data.get('initial_stock', 0)
            product = form.save(commit=False)
            product.quantity_in_stock = 0  # Will be adjusted via StockMovement
            product.save()

            if initial_stock > 0:
                StockMovement.objects.create(
                    product=product,
                    movement_type=StockMovement.MovementType.STOCK_IN,
                    quantity=initial_stock,
                    reference='Initial Stock on Creation',
                    created_by=request.user
                )

            messages.success(request, f"Product '{product.name}' was created successfully.")
            return redirect('inventory:product_detail', pk=product.pk)
    else:
        form = ProductForm()

    return render(request, 'inventory/product_form.html', {
        'form': form,
        'title': 'Add New Product',
        'is_edit': False,
    })


@admin_required
def product_edit(request, pk):
    """Admin-only: Edit product metadata (cost, price, name, category, reorder level)."""
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product '{product.name}' was updated successfully.")
            return redirect('inventory:product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)

    return render(request, 'inventory/product_form.html', {
        'form': form,
        'title': f'Edit Product: {product.name}',
        'is_edit': True,
        'product': product,
    })


@admin_required
@require_POST
def product_toggle_active(request, pk):
    """Admin-only: Toggle active status for catalog availability."""
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save(update_fields=['is_active'])

    status_str = "activated" if product.is_active else "deactivated"
    messages.success(request, f"Product '{product.name}' was {status_str}.")
    return redirect('inventory:product_detail', pk=product.pk)


@admin_required
def stock_in(request):
    """Admin-only: Fast stock-in receipt form for inventory restocks."""
    initial_product_id = request.GET.get('product')
    initial_data = {}
    if initial_product_id:
        initial_data['product'] = initial_product_id

    if request.method == 'POST':
        form = StockInForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            quantity = form.cleaned_data['quantity']
            reference = form.cleaned_data['reference'] or 'Stock In / Restock'

            StockMovement.objects.create(
                product=product,
                movement_type=StockMovement.MovementType.STOCK_IN,
                quantity=quantity,
                reference=reference,
                created_by=request.user
            )

            messages.success(request, f"Successfully added {quantity} units to '{product.name}'. New stock: {product.quantity_in_stock}.")
            return redirect('inventory:product_detail', pk=product.pk)
    else:
        form = StockInForm(initial=initial_data)

    return render(request, 'inventory/stock_in.html', {
        'form': form,
        'title': 'Record Stock-In / Restock',
    })


@login_required
def stock_movement_list(request):
    """Audit trail log of all inventory movements."""
    movements = StockMovement.objects.select_related('product', 'created_by').all().order_by('-created_at')

    movement_type = request.GET.get('type', '').strip()
    if movement_type in [t[0] for t in StockMovement.MovementType.choices]:
        movements = movements.filter(movement_type=movement_type)

    paginator = Paginator(movements, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/stock_movement_list.html', {
        'movements': page_obj,
        'page_obj': page_obj,
        'movement_type': movement_type,
        'type_choices': StockMovement.MovementType.choices,
    })


@admin_required
def category_list(request):
    """Admin-only: Manage product categories."""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"Category '{cat.name}' created.")
            return redirect('inventory:category_list')
    else:
        form = CategoryForm()

    categories = Category.objects.all().order_by('name')
    return render(request, 'inventory/category_list.html', {
        'categories': categories,
        'form': form,
    })


@admin_required
@require_POST
def category_delete(request, pk):
    """Admin-only: Delete a category."""
    category = get_object_or_404(Category, pk=pk)
    cat_name = category.name
    category.delete()
    messages.success(request, f"Category '{cat_name}' deleted.")
    return redirect('inventory:category_list')




@admin_required
def product_bulk_upload(request):
    summary = None

    if request.method == 'POST':
        form = ProductExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            wb = openpyxl.load_workbook(form.cleaned_data['excel_file'], data_only=True)
            ws = wb.active

            categories_created = 0
            products_created = 0
            products_updated = 0
            current_category = None
            sku_counters = {}  # prefix -> last used number, cached for this import run

            def next_sku(category):
                if category and category.name:
                    letters = ''.join(ch for ch in category.name if ch.isalnum())
                    prefix = (letters[:3] or 'GEN').upper()
                else:
                    prefix = 'GEN'

                if prefix not in sku_counters:
                    existing = Product.objects.filter(
                        sku__startswith=f'{prefix}-'
                    ).values_list('sku', flat=True)
                    max_num = 0
                    for sku in existing:
                        suffix = sku[len(prefix) + 1:]
                        if suffix.isdigit():
                            max_num = max(max_num, int(suffix))
                    sku_counters[prefix] = max_num

                sku_counters[prefix] += 1
                candidate = f'{prefix}-{sku_counters[prefix]:04d}'
                while Product.objects.filter(sku=candidate).exists():
                    sku_counters[prefix] += 1
                    candidate = f'{prefix}-{sku_counters[prefix]:04d}'
                return candidate

            with transaction.atomic():
                for row in ws.iter_rows(values_only=True):
                    name, cost_price, stock, selling_price = (list(row) + [None, None, None, None])[:4]

                    if name is None or str(name).strip() == '':
                        continue

                    name = str(name).strip()

                    if name.isupper():
                        current_category, created = Category.objects.get_or_create(name=name.title())
                        if created:
                            categories_created += 1
                        continue

                    def as_number(value):
                        return value if isinstance(value, (int, float)) else None

                    cost_price = as_number(cost_price)
                    selling_price = as_number(selling_price)
                    stock_qty = as_number(stock) or 0

                    existing_product = Product.objects.filter(name__iexact=name).first()

                    if existing_product:
                        changed = False
                        if current_category and existing_product.category_id != current_category.id:
                            existing_product.category = current_category
                            changed = True
                        if cost_price is not None and existing_product.cost_price != cost_price:
                            existing_product.cost_price = cost_price
                            changed = True
                        if selling_price is not None and existing_product.selling_price != selling_price:
                            existing_product.selling_price = selling_price
                            changed = True
                        if changed:
                            existing_product.save()
                            products_updated += 1
                    else:
                        product = Product.objects.create(
                            name=name,
                            sku=next_sku(current_category),
                            category=current_category,
                            cost_price=cost_price,
                            selling_price=selling_price,
                            quantity_in_stock=0,
                            is_active=True,
                        )
                        products_created += 1

                        if stock_qty > 0:
                            StockMovement.objects.create(
                                product=product,
                                movement_type=StockMovement.MovementType.STOCK_IN,
                                quantity=stock_qty,
                                reference='Bulk Excel Import',
                                created_by=request.user,
                            )

            summary = {
                'categories_created': categories_created,
                'products_created': products_created,
                'products_updated': products_updated,
            }
            messages.success(
                request,
                f"Import complete: {products_created} products created, "
                f"{products_updated} updated, {categories_created} new categories."
            )
            form = ProductExcelUploadForm()
    else:
        form = ProductExcelUploadForm()

    return render(request, 'inventory/product_bulk_upload.html', {
        'form': form,
        'summary': summary,
    })
