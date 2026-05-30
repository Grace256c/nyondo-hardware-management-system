from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import ProtectedError
from .models import Customer, Invoice, InvoiceItem, Receivable, CustomerPayment
from .forms import (
    CustomerForm, InvoiceForm, InvoiceItemForm,
    ReceivableEditForm, CustomerPaymentForm, TransportOverrideForm
)
from users.decorators import sales_required, manager_required, admin_required


# ── CUSTOMER VIEWS ────────────────────────────────────────────

@sales_required
def customer_list(request):
    customers = Customer.objects.filter(is_active=True).order_by('name')
    return render(request, 'sales/customer_list.html', {'customers': customers})


@sales_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer added successfully.')
            return redirect('sales:customer-list')
    else:
        form = CustomerForm()
    return render(request, 'sales/customer_form.html', {
        'form' : form,
        'title': 'Add Customer',
    })


@sales_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    invoices = Invoice.objects.filter(
        customer=customer, is_cancelled=False
    ).order_by('-sale_date')
    return render(request, 'sales/customer_detail.html', {
        'customer': customer,
        'invoices': invoices,
    })


@sales_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer updated successfully.')
            return redirect('sales:customer-list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'sales/customer_form.html', {
        'form' : form,
        'title': 'Edit Customer',
    })


@admin_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        try:
            customer.is_active = False
            customer.save()
            messages.success(request, 'Customer deactivated successfully.')
            return redirect('sales:customer-list')
        except ProtectedError:
            messages.error(request, 'Cannot deactivate this customer.')
    return render(request, 'sales/customer_confirm_delete.html', {
        'customer': customer,
    })


# ── INVOICE VIEWS ─────────────────────────────────────────────

@sales_required
def invoice_list(request):
    invoices = Invoice.objects.filter(
        is_cancelled=False
    ).order_by('-sale_date', '-created_at')
    return render(request, 'sales/invoice_list.html', {'invoices': invoices})


@sales_required
def invoice_create(request):
    from stock.models import Product
    products  = Product.objects.filter(is_active=True)
    customers = Customer.objects.filter(is_active=True)

    if request.method == 'POST':
        customer_id    = request.POST.get('customer', '').strip()
        customer_name  = request.POST.get('customer_name', '').strip()
        customer_type  = request.POST.get('customer_type', 'walk_in')
        payment_method = request.POST.get('payment_method', '').strip()
        payment_status = request.POST.get('payment_status', 'paid')
        notes          = request.POST.get('notes', '').strip()
        raw_paid       = request.POST.get('amount_paid', '0').strip()
        product_ids    = request.POST.getlist('product')
        quantities     = request.POST.getlist('quantity')
        prices         = request.POST.getlist('unit_price')

        # ── BACKEND VALIDATIONS ──────────────────────────────
        errors = []

        # Customer validation
        customer = None
        if customer_id:
            try:
                customer = Customer.objects.get(pk=customer_id, is_active=True)
                customer_name = customer.name
                customer_type = customer.customer_type
            except Customer.DoesNotExist:
                errors.append('Selected customer not found or is inactive.')
        elif not customer_name:
            errors.append('Please select an existing customer or enter a walk-in customer name.')
        elif len(customer_name) < 2:
            errors.append('Walk-in customer name must be at least 2 characters.')

        # Credit requires registered customer
        if payment_status == 'credit' and not customer:
            errors.append(
                'Credit sales require a registered customer. '
                'Please register the customer first.'
            )

        # Payment method
        valid_methods = ['cash', 'mobile_money', 'bank_transfer', 'cheque', 'scheme']
        if not payment_method:
            errors.append('Please select a payment method.')
        elif payment_method not in valid_methods:
            errors.append('Invalid payment method selected.')

        # Amount paid
        try:
            amount_paid = float(raw_paid) if raw_paid else 0
            if amount_paid < 0:
                errors.append('Amount paid cannot be negative.')
        except ValueError:
            errors.append('Invalid amount paid entered.')
            amount_paid = 0

        # Partial payment must have amount
        if payment_status == 'partial' and amount_paid <= 0:
            errors.append('Please enter the amount paid for a partial payment.')

        # Product rows validation
        valid_items = []
        for i in range(len(product_ids)):
            pid = product_ids[i].strip()
            qty = quantities[i].strip() if i < len(quantities) else ''
            prc = prices[i].strip() if i < len(prices) else ''

            if not pid:
                continue  # Skip empty rows

            try:
                product = Product.objects.get(pk=pid, is_active=True)
            except Product.DoesNotExist:
                errors.append(f'Product not found.')
                continue

            try:
                qty = float(qty)
            except (ValueError, TypeError):
                errors.append(f'{product.name}: Invalid quantity.')
                continue

            try:
                prc = float(prc)
            except (ValueError, TypeError):
                errors.append(f'{product.name}: Invalid unit price.')
                continue

            if qty <= 0:
                errors.append(f'{product.name}: Quantity must be greater than zero.')
                continue

            if prc <= 0:
                errors.append(f'{product.name}: Unit price must be greater than zero.')
                continue

            if qty > float(product.quantity):
                errors.append(
                    f'{product.name}: Not enough stock. '
                    f'Available: {product.quantity:,.0f} {product.get_unit_display()}.'
                )
                continue

            valid_items.append({
                'product' : product,
                'quantity': qty,
                'price'   : prc,
            })

        if not valid_items:
            errors.append('Please add at least one product to the invoice.')

        # Amount paid cannot exceed total
        if valid_items and not errors:
            subtotal = sum(item['quantity'] * item['price'] for item in valid_items)
            if amount_paid > subtotal + 30000:  # 30000 max transport
                errors.append(
                    f'Amount paid (UGX {amount_paid:,.0f}) '
                    f'cannot exceed the invoice total.'
                )

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'sales/invoice_create.html', {
                'products' : products,
                'customers': customers,
            })

        # ── SAVE INVOICE ─────────────────────────────────────
        from decimal import Decimal
        subtotal = Decimal(str(
            sum(item['quantity'] * item['price'] for item in valid_items)
        ))

        invoice = Invoice.objects.create(
            customer       = customer,
            customer_name  = customer_name,
            customer_type  = customer_type,
            payment_method = payment_method,
            payment_status = payment_status,
            subtotal       = subtotal,
            amount_paid    = Decimal(str(amount_paid)),
            notes          = notes,
            served_by      = request.user,
        )

        for item in valid_items:
            InvoiceItem.objects.create(
                invoice    = invoice,
                product    = item['product'],
                quantity   = Decimal(str(item['quantity'])),
                unit_price = Decimal(str(item['price'])),
            )

        messages.success(
            request,
            f'Invoice {invoice.invoice_number} created successfully.'
        )
        return redirect('sales:invoice-detail', pk=invoice.pk)

    return render(request, 'sales/invoice_create.html', {
        'products' : products,
        'customers': customers,
    })


@sales_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    items   = invoice.items.all()
    return render(request, 'sales/invoice_detail.html', {
        'invoice': invoice,
        'items'  : items,
    })


@manager_required
def invoice_update(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if invoice.is_cancelled:
        messages.error(request, 'Cannot edit a cancelled invoice.')
        return redirect('sales:invoice-detail', pk=invoice.pk)

    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Invoice updated successfully.')
            return redirect('sales:invoice-detail', pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice)
    return render(request, 'sales/invoice_edit.html', {
        'form'   : form,
        'invoice': invoice,
    })


@manager_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        invoice.is_cancelled = True
        invoice.save()
        messages.success(request, 'Invoice cancelled successfully.')
        return redirect('sales:invoice-list')
    return render(request, 'sales/invoice_confirm_delete.html', {
        'invoice': invoice,
    })


@sales_required
def invoice_print(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    items   = invoice.items.all()
    return render(request, 'sales/invoice_print.html', {
        'invoice': invoice,
        'items'  : items,
    })


@manager_required
def transport_override(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        form = TransportOverrideForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transport charge updated.')
            return redirect('sales:invoice-detail', pk=invoice.pk)
    else:
        form = TransportOverrideForm(instance=invoice)
    return render(request, 'sales/invoice_transport.html', {
        'form'   : form,
        'invoice': invoice,
    })


# ── RECEIVABLE VIEWS ──────────────────────────────────────────

@manager_required
def receivable_list(request):
    receivables = Receivable.objects.exclude(
        status='paid'
    ).order_by('-created_at')
    return render(request, 'sales/receivable_list.html', {
        'receivables': receivables,
    })


@manager_required
def receivable_detail(request, pk):
    receivable = get_object_or_404(Receivable, pk=pk)
    payments   = receivable.payments.all().order_by('-payment_date')
    return render(request, 'sales/receivable_detail.html', {
        'receivable': receivable,
        'payments'  : payments,
    })


@manager_required
def receivable_pay(request, pk):
    receivable = get_object_or_404(Receivable, pk=pk)
    if receivable.status == 'paid':
        messages.error(request, 'This receivable is already fully paid.')
        return redirect('sales:receivable-detail', pk=receivable.pk)

    if request.method == 'POST':
        form = CustomerPaymentForm(request.POST, receivable=receivable)
        if form.is_valid():
            payment             = form.save(commit=False)
            payment.receivable  = receivable
            payment.recorded_by = request.user
            payment.save()
            messages.success(request, 'Payment recorded successfully.')
            return redirect('sales:receivable-detail', pk=receivable.pk)
    else:
        form = CustomerPaymentForm(receivable=receivable)
    return render(request, 'sales/receivable_pay_form.html', {
        'form'      : form,
        'receivable': receivable,
    })


@admin_required
def receivable_writeoff(request, pk):
    receivable = get_object_or_404(Receivable, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if not reason or len(reason) < 10:
            messages.error(
                request,
                'Please provide a detailed reason for the write-off (at least 10 characters).'
            )
            return render(request, 'sales/receivable_writeoff_form.html', {
                'receivable': receivable,
            })
        receivable.status = 'written_off'
        receivable.notes  = f'Written off: {reason}'
        receivable.save()
        messages.success(request, 'Receivable written off successfully.')
        return redirect('sales:receivable-list')
    return render(request, 'sales/receivable_writeoff_form.html', {
        'receivable': receivable,
    })


@admin_required
def receivable_delete(request, pk):
    receivable = get_object_or_404(Receivable, pk=pk)
    if request.method == 'POST':
        try:
            receivable.delete()
            messages.success(request, 'Receivable deleted.')
            return redirect('sales:receivable-list')
        except ProtectedError:
            messages.error(request, 'Cannot delete this receivable.')
    return render(request, 'sales/receivable_confirm_delete.html', {
        'receivable': receivable,
    })


# ── AJAX VIEWS ────────────────────────────────────────────────

def ajax_product_price(request):
    from django.http import JsonResponse
    from stock.models import Product
    product_id    = request.GET.get('product_id')
    customer_type = request.GET.get('customer_type', 'retail')

    try:
        product = Product.objects.get(pk=product_id, is_active=True)
        price   = (
            product.wholesale_price
            if customer_type == 'wholesale'
            else product.retail_price
        )
        return JsonResponse({
            'price'   : str(price),
            'quantity': str(product.quantity),
            'unit'    : product.get_unit_display(),
        })
    except Product.DoesNotExist:
        return JsonResponse({'price': '0', 'quantity': '0', 'unit': ''})
    except Exception:
        return JsonResponse({'price': '0', 'quantity': '0', 'unit': ''})


def ajax_transport(request):
    from django.http import JsonResponse
    from .utils import calculate_transport
    try:
        distance_km   = float(request.GET.get('distance_km', 0))
        invoice_total = float(request.GET.get('invoice_total', 0))
        transport     = calculate_transport(distance_km, invoice_total)
        return JsonResponse({'transport': transport})
    except Exception:
        return JsonResponse({'transport': 0})