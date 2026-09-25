from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Customer
from .forms import CustomerForm
from accounts.decorators import admin_required


@login_required
def customer_list(request):
    """Searchable customer directory, accessible to both Cashier and Admin."""
    query = request.GET.get('q', '').strip()
    customers = Customer.objects.all().order_by('name')

    if query:
        customers = customers.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )

    total_count = Customer.objects.count()
    paginator = Paginator(customers, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'customers/customer_list.html', {
        'customers': page_obj,
        'page_obj': page_obj,
        'query': query,
        'total_count': total_count,
    })


@login_required
def customer_detail(request, pk):
    """Customer profile and contact details."""
    customer = get_object_or_404(Customer, pk=pk)
    
    # We will safely fetch documents if the sales app models exist
    documents = []
    if hasattr(customer, 'documents'):
        documents = customer.documents.all().order_by('-issue_date')[:10]

    return render(request, 'customers/customer_detail.html', {
        'customer': customer,
        'documents': documents,
    })


@login_required
def customer_create(request):
    """Create a new customer (usable by Cashier and Admin)."""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Customer '{customer.name}' created successfully.")
            return redirect('customers:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm()

    return render(request, 'customers/customer_form.html', {
        'form': form,
        'title': 'Add New Customer',
        'is_edit': False,
    })


@login_required
def customer_edit(request, pk):
    """Edit existing customer details."""
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Customer '{customer.name}' updated successfully.")
            return redirect('customers:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)

    return render(request, 'customers/customer_form.html', {
        'form': form,
        'title': f'Edit Customer: {customer.name}',
        'is_edit': True,
        'customer': customer,
    })


@admin_required
@require_POST
def customer_delete(request, pk):
    """Admin-only deletion of a customer."""
    customer = get_object_or_404(Customer, pk=pk)
    name = customer.name
    customer.delete()
    messages.success(request, f"Customer '{name}' deleted.")
    return redirect('customers:customer_list')


@login_required
def customer_search_json(request):
    """
    Lightweight JSON endpoint for autocomplete search during quotation/invoice creation.
    Returns matching active customers.
    """
    term = request.GET.get('term', '').strip()
    customers = Customer.objects.all()
    if term:
        customers = customers.filter(
            Q(name__icontains=term) |
            Q(phone__icontains=term) |
            Q(email__icontains=term)
        )[:15]
    else:
        customers = customers[:15]

    data = [
        {
            'id': c.id,
            'name': c.name,
            'phone': c.phone,
            'email': c.email,
        }
        for c in customers
    ]
    return JsonResponse({'results': data})
