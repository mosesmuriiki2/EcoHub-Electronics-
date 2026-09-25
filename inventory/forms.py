from django import forms
from .models import Category, Product, StockMovement


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm',
                'placeholder': 'e.g. Cables & Adapters',
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm',
                'rows': 3,
                'placeholder': 'Optional category description...',
            }),
        }


class ProductForm(forms.ModelForm):
    initial_stock = forms.IntegerField(
        required=False,
        min_value=0,
        initial=0,
        help_text="Starting inventory count on creation (recorded as initial StockMovement).",
        widget=forms.NumberInput(attrs={
            'class': 'block w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm',
            'placeholder': '0',
        })
    )

    class Meta:
        model = Product
        fields = ['name', 'sku', 'category', 'cost_price', 'selling_price', 'reorder_level', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm',
                'placeholder': 'e.g. Samsung 25W Fast Charger Type-C',
            }),
            'sku': forms.TextInput(attrs={
                'class': 'block w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm font-mono',
                'placeholder': 'Leave blank to auto-generate',
            }),
            'category': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm bg-white',
            }),
            'cost_price': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm',
                'step': '0.01',
                'placeholder': '0.00',
            }),
            'selling_price': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm',
                'step': '0.01',
                'placeholder': '0.00',
            }),
            'reorder_level': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm',
                'min': '0',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-emerald-600 focus:ring-emerald-500 border-slate-300 rounded',
            }),
        }

    def __init__(self, *args, **kwargs):
        is_edit = kwargs.get('instance') is not None and kwargs.get('instance').pk is not None
        super().__init__(*args, **kwargs)
        if is_edit:
            # When editing an existing product, initial stock is not editable
            self.fields.pop('initial_stock', None)
        else:
            self.fields['sku'].required = False

    def clean_sku(self):
        sku = self.cleaned_data.get('sku', '').strip()
        if not sku:
            sku = Product.generate_unique_sku()
        return sku


class StockInForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True).order_by('name'),
        widget=forms.Select(attrs={
            'class': 'block w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm bg-white',
        })
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'block w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm',
            'placeholder': 'Quantity received (e.g. 10)',
        })
    )
    reference = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'block w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm',
            'placeholder': 'e.g. Supplier PO #8832, Restock batch',
        })
    )
class ProductExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        label='Excel file (.xlsx)',
        widget=forms.ClearableFileInput(attrs={'accept': '.xlsx,.xls'})
    )

    def clean_excel_file(self):
        f = self.cleaned_data['excel_file']
        if not f.name.lower().endswith(('.xlsx', '.xls')):
            raise forms.ValidationError('Please upload an .xlsx or .xls file.')
        return f