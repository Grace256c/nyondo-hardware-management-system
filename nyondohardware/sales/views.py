from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import ProtectedError
from .models import Customer, Invoice, InvoiceItem, Receivable, CustomerPayment
from .forms import CustomerForm, InvoiceForm, InvoiceItemForm, ReceivableEditForm, CustomerPaymentForm, TransportOverrideForm
from users.decorators import sales_required, manager_required, admin_required


# ─── CUSTOMER VIEWS ───────────────────────────────────────────

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
    return render(request, 'sales/customer_form.html', {'form': form, 'title': 'Add Customer'})


@sales_required
def customer_detail(request, pk):
    customer  = get_object_or_404(Customer, pk=pk)
    invoices  = Invoice.objects.filter(customer=customer).order_by('-sale_date')
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
    return render(request, 'sales/customer_form.html', {'form': form, 'title': 'Edit Customer'})


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
            messages.error(request, 'Cannot delete this customer.')
    return render(request, 'sales/customer_confirm_delete.html', {'customer': customer})


# ─── INVOICE VIEWS ────────────────────────────────────────────

@sales_required
def invoice_list(request):
    invoices = Invoice.objects.filter(
        is_cancelled=False).order_by('-sale_date', '-created_at')
    return render(request, 'sales/invoice_list.html', {'invoices': invoices})


@sales_required
def invoice_create(request):
    if request.method == 'POST':
        # Get form data
        customer_id    = request.POST.get('customer')
        customer_name  = request.POST.get('customer_name', '').strip()
        customer_type  = request.POST.get('customer_type', 'walk_in')
        payment_method = request.POST.get('payment_method')
        payment_status = request.POST.get('payment_status', 'paid')
        amount_paid    = request.POST.get('amount_paid', 0)
        notes          = request.POST.get('notes', '')
        products       = request.POST.getlist('product')
        quantities     = request.POST.getlist('quantity')
        prices         = request.POST.getlist('unit_price')

        # ── DJANGO VALIDATIONS ──────────────────────────────
        errors = []

        # Validate customer
        if not customer_id and not customer_name:
            errors.append('Please select a customer or enter a walk-in customer name.')

        # Validate payment method
        if not payment_method:
            errors.append('Please select a payment method.')

        # Validate products
        valid_items = []
        for i in range(len(products)):
            if products[i] and quantities[i] and prices[i]:
                try:
                    from stock.models import Product
                    product  = Product.objects.get(pk=products[i])
                    qty      = float(quantities[i])
                    price    = float(prices[i])

                    if qty <= 0:
                        errors.append(f'{product.name}: Quantity must be greater than 0.')
                    elif qty > float(product.quantity):
                        errors.append(
                            f'{product.name}: Not enough stock. '
                            f'Available: {product.quantity}'
                        )
                    elif price <= 0:
                        errors.append(f'{product.name}: Unit price must be greater than 0.')
                    else:
                        valid_items.append({
                            'product' : product,
                            'quantity': qty,
                            'price'   : price,
                        })
                except Exception as e:
                    errors.append(f'Invalid product selected.')

        if not valid_items:
            errors.append('Please add at least one product.')

        # Validate amount paid
        try:
            amount_paid = float(amount_paid)
            if amount_paid < 0:
                errors.append('Amount paid cannot be negative.')
        except ValueError:
            errors.append('Invalid amount paid.')
            amount_paid = 0

        # If errors show them
        if errors:
            from stock.models import Product as P
            for error in errors:
                messages.error(request, error)
            return render(request, 'sales/invoice_create.html', {
                'form'     : InvoiceForm(),
                'products' : P.objects.filter(is_active=True),
                'customers': Customer.objects.filter(is_active=True),
            })

        # ── SAVE INVOICE ────────────────────────────────────
        # Calculate subtotal
        subtotal = sum(item['quantity'] * item['price'] for item in valid_items)

        # Get customer
        customer = None
        if customer_id:
            try:
                customer = Customer.objects.get(pk=customer_id)
                customer_name = customer.name
                customer_type = customer.customer_type
            except Customer.DoesNotExist:
                pass

        # Create invoice
        invoice = Invoice.objects.create(
            customer       = customer,
            customer_name  = customer_name,
            customer_type  = customer_type,
            payment_method = payment_method,
            payment_status = payment_status,
            subtotal       = subtotal,
            amount_paid    = amount_paid,
            notes          = notes,
            served_by      = request.user,
        )

        # Save invoice items
        for item in valid_items:
            InvoiceItem.objects.create(
                invoice    = invoice,
                product    = item['product'],
                quantity   = item['quantity'],
                unit_price = item['price'],
            )

        messages.success(request, f'Invoice {invoice.invoice_number} created successfully.')
        return redirect('sales:invoice-detail', pk=invoice.pk)

    else:
        from stock.models import Product
        form      = InvoiceForm()
        products  = Product.objects.filter(is_active=True)
        customers = Customer.objects.filter(is_active=True)
        return render(request, 'sales/invoice_create.html', {
            'form'     : form,
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
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Invoice updated successfully.')
            return redirect('sales:invoice-detail', pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice)
    return render(request, 'sales/invoice_edit.html', {'form': form, 'invoice': invoice})


@manager_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        invoice.is_cancelled = True
        invoice.save()
        messages.success(request, 'Invoice cancelled successfully.')
        return redirect('sales:invoice-list')
    return render(request, 'sales/invoice_confirm_delete.html', {'invoice': invoice})


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


# ─── RECEIVABLE VIEWS ─────────────────────────────────────────

@manager_required
def receivable_list(request):
    receivables = Receivable.objects.exclude(status='paid').order_by('-created_at')
    return render(request, 'sales/receivable_list.html', {'receivables': receivables})


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
        receivable.status = 'written_off'
        receivable.save()
        messages.success(request, 'Receivable written off.')
        return redirect('sales:receivable-list')
    return render(request, 'sales/receivable_writeoff_form.html', {'receivable': receivable})


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
    return render(request, 'sales/receivable_confirm_delete.html', {'receivable': receivable})


# ─── AJAX VIEWS ───────────────────────────────────────────────

def ajax_product_price(request):
    from django.http import JsonResponse
    product_id    = request.GET.get('product_id')
    customer_type = request.GET.get('customer_type')

    try:
        from stock.models import Product
        product = Product.objects.get(pk=product_id)
        if customer_type == 'wholesale':
            price = product.wholesale_price
        else:
            price = product.retail_price
        return JsonResponse({
            'price'   : str(price),
            'quantity': str(product.quantity),
        })
    except Exception:
        return JsonResponse({'price': '0', 'quantity': '0'})


def ajax_transport(request):
    from django.http import JsonResponse
    from .utils import calculate_transport
    try:
        distance_km    = float(request.GET.get('distance_km', 0))
        invoice_total  = float(request.GET.get('invoice_total', 0))
        transport      = calculate_transport(distance_km, invoice_total)
        return JsonResponse({'transport': transport})
    except Exception:
        return JsonResponse({'transport': 0})