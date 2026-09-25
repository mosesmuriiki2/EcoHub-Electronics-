from django.contrib import admin
from .models import Document, DocumentItem, Payment, Receipt


class DocumentItemInline(admin.TabularInline):
    model = DocumentItem
    extra = 0


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('doc_number', 'doc_type', 'customer', 'status', 'issue_date', 'total', 'created_by')
    list_filter = ('doc_type', 'status', 'issue_date')
    search_fields = ('doc_number', 'customer__name', 'customer__phone')
    inlines = [DocumentItemInline, PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'method', 'reference', 'paid_at', 'received_by')
    list_filter = ('method', 'paid_at')
    search_fields = ('invoice__doc_number', 'reference')


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'invoice', 'issued_at', 'issued_by')
    search_fields = ('receipt_number', 'invoice__doc_number')
