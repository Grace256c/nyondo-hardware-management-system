from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import ProtectedError, F
from .models import Category, Supplier, Product, StockReceipt, SupplierCredit, SupplierPayment
from .forms import CategoryForm, SupplierForm, ProductForm, StockReceiptForm, SupplierCreditEditForm, SupplierPaymentForm
from users.decorators import sales_required, manager_required, admin_required


# ─── CATEGORY VIEWS ───────────────────────────────────────────

@manager_required
def category_list(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'stock/category_list.html', {'categories': categories})


@manager_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully.')
            return redirect('stock:category-list')
    else:
        form = CategoryForm()
    return render(request, 'stock/category_form.html', {'form': form, 'title': 'Add Category'})


@manager_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('stock:category-list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'stock/category_form.html', {'form': form, 'title': 'Edit Category'})


@admin_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        try:
            category.delete()
            messages.success(request, 'Category deleted successfully.')
            return redirect('stock:category-list')
        except ProtectedError:
            messages.error(request, 'Cannot delete this category because it has products.')
    return render(request, 'stock/category_confirm_delete.html', {'category': category})


# ─── SUPPLIER VIEWS ───────────────────────────────────────────

@manager_required
def supplier_list(request):
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')
    return render(request, 'stock/supplier_list.html', {'suppliers': suppliers})


@manager_required
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier added successfully.')
            return redirect('stock:supplier-list')
    else:
        form = SupplierForm()
    return render(request, 'stock/supplier_form.html', {'form': form, 'title': 'Add Supplier'})


@manager_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    receipts = StockReceipt.objects.filter(supplier=supplier).order_by('-receipt_date')
    credits  = SupplierCredit.objects.filter(supplier=supplier)
    return render(request, 'stock/supplier_detail.html', {
        'supplier': supplier,
        'receipts': receipts,
        'credits' : credits,
    })


@manager_required
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier updated successfully.')
            return redirect('stock:supplier-list')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'stock/supplier_form.html', {'form': form, 'title': 'Edit Supplier'})


@admin_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        try:
            supplier.is_active = False
            supplier.save()
            messages.success(request, 'Supplier deactivated successfully.')
            return redirect('stock:supplier-list')
        except ProtectedError:
            messages.error(request, 'Cannot delete this supplier.')
    return render(request, 'stock/supplier_confirm_delete.html', {'supplier': supplier})


# ─── PRODUCT VIEWS ────────────────────────────────────────────

@sales_required
def product_list(request):
    products = Product.objects.filter(is_active=True).order_by('name')
    return render(request, 'stock/product_list.html', {'products': products})


@sales_required
def product_detail(request, pk):
    product  = get_object_or_404(Product, pk=pk)
    receipts = StockReceipt.objects.filter(product=product).order_by('-receipt_date')
    return render(request, 'stock/product_detail.html', {
        'product' : product,
        'receipts': receipts,
    })


@manager_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully.')
            return redirect('stock:product-list')
    else:
        form = ProductForm()
    return render(request, 'stock/product_form.html', {'form': form, 'title': 'Add Product'})


@manager_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('stock:product-list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'stock/product_form.html', {'form': form, 'title': 'Edit Product'})


@admin_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        try:
            product.is_active = False
            product.save()
            messages.success(request, 'Product deactivated successfully.')
            return redirect('stock:product-list')
        except ProtectedError:
            messages.error(request, 'Cannot delete this product.')
    return render(request, 'stock/product_confirm_delete.html', {'product': product})


# ─── STOCK RECEIPT VIEWS ──────────────────────────────────────

@manager_required
def receipt_list(request):
    receipts = StockReceipt.objects.all().order_by('-receipt_date')
    return render(request, 'stock/receipt_list.html', {'receipts': receipts})


@manager_required
def receipt_create(request):
    if request.method == 'POST':
        form = StockReceiptForm(request.POST)
        if form.is_valid():
            receipt             = form.save(commit=False)
            receipt.recorded_by = request.user
            receipt.save()
            messages.success(request, f'Stock receipt {receipt.grn_number} created successfully.')
            return redirect('stock:receipt-detail', pk=receipt.pk)
    else:
        form = StockReceiptForm()
    return render(request, 'stock/receipt_form.html', {'form': form, 'title': 'Receive Stock'})


@manager_required
def receipt_detail(request, pk):
    receipt = get_object_or_404(StockReceipt, pk=pk)
    return render(request, 'stock/receipt_detail.html', {'receipt': receipt})


@manager_required
def receipt_print(request, pk):
    receipt = get_object_or_404(StockReceipt, pk=pk)
    return render(request, 'stock/receipt_print.html', {'receipt': receipt})


@admin_required
def receipt_delete(request, pk):
    receipt = get_object_or_404(StockReceipt, pk=pk)
    if request.method == 'POST':
        try:
            receipt.delete()
            messages.success(request, 'Receipt deleted successfully.')
            return redirect('stock:receipt-list')
        except ProtectedError:
            messages.error(request, 'Cannot delete this receipt.')
    return render(request, 'stock/receipt_confirm_delete.html', {'receipt': receipt})


# ─── SUPPLIER CREDIT VIEWS ────────────────────────────────────

@manager_required
def credit_list(request):
    credits = SupplierCredit.objects.all().order_by('status', '-created_at')
    return render(request, 'stock/credit_list.html', {'credits': credits})


@manager_required
def credit_detail(request, pk):
    credit   = get_object_or_404(SupplierCredit, pk=pk)
    payments = credit.payments.all().order_by('-payment_date')
    return render(request, 'stock/credit_detail.html', {
        'credit'  : credit,
        'payments': payments,
    })


@manager_required
def credit_update(request, pk):
    credit = get_object_or_404(SupplierCredit, pk=pk)
    if request.method == 'POST':
        form = SupplierCreditEditForm(request.POST, instance=credit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Credit updated successfully.')
            return redirect('stock:credit-detail', pk=credit.pk)
    else:
        form = SupplierCreditEditForm(instance=credit)
    return render(request, 'stock/credit_form.html', {'form': form, 'credit': credit})


@manager_required
def credit_pay(request, pk):
    credit = get_object_or_404(SupplierCredit, pk=pk)
    if request.method == 'POST':
        form = SupplierPaymentForm(request.POST, credit=credit)
        if form.is_valid():
            payment             = form.save(commit=False)
            payment.credit      = credit
            payment.recorded_by = request.user
            payment.save()
            messages.success(request, 'Payment recorded successfully.')
            return redirect('stock:credit-detail', pk=credit.pk)
    else:
        form = SupplierPaymentForm(credit=credit)
    return render(request, 'stock/credit_pay_form.html', {'form': form, 'credit': credit})


@manager_required
def credit_payments(request, pk):
    credit   = get_object_or_404(SupplierCredit, pk=pk)
    payments = credit.payments.all().order_by('-payment_date')
    return render(request, 'stock/payment_list.html', {
        'credit'  : credit,
        'payments': payments,
    })


@admin_required
def payment_delete(request, pk):
    payment = get_object_or_404(SupplierPayment, pk=pk)
    credit  = payment.credit
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Payment reversed successfully.')
        return redirect('stock:credit-detail', pk=credit.pk)
    return render(request, 'stock/payment_confirm_delete.html', {'payment': payment})


# ─── LOW STOCK ALERT ──────────────────────────────────────────

@sales_required
def low_stock_alert(request):
    products = Product.objects.filter(
        is_active=True,
        quantity__lte=F('reorder_level')
    ).order_by('quantity')
    return render(request, 'stock/low_stock_alert.html', {'products': products})