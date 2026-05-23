from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import SchemeCustomer, Deposit, Pickup, SchemeInvoice
from .forms import SchemeCustomerRegistrationForm, SchemeCustomerEditForm, DepositForm, PickupForm
from .utils import get_customer_balance
from users.decorators import sales_required, manager_required, admin_required


# ─── SCHEME CUSTOMER VIEWS ────────────────────────────────────

@sales_required
def customer_list(request):
    customers = SchemeCustomer.objects.all().order_by('full_name')
    for customer in customers:
        customer.balance = get_customer_balance(customer)
    return render(request, 'scheme/customer_list.html', {'customers': customers})


@manager_required
def customer_create(request):
    if request.method == 'POST':
        form = SchemeCustomerRegistrationForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.registered_by = request.user
            customer.save()
            messages.success(request, f'{customer.full_name} registered successfully.')
            return redirect('scheme:customer-detail', pk=customer.pk)
    else:
        form = SchemeCustomerRegistrationForm()
    return render(request, 'scheme/customer_register_form.html', {'form': form})


@sales_required
def customer_detail(request, pk):
    customer = get_object_or_404(SchemeCustomer, pk=pk)
    balance  = get_customer_balance(customer)
    deposits = customer.deposits.filter(is_reversed=False).order_by('-payment_date')
    pickups  = customer.pickups.exclude(status='cancelled').order_by('-pickup_date')
    return render(request, 'scheme/customer_detail.html', {
        'customer': customer,
        'balance' : balance,
        'deposits': deposits,
        'pickups' : pickups,
    })


@manager_required
def customer_update(request, pk):
    customer = get_object_or_404(SchemeCustomer, pk=pk)
    if request.method == 'POST':
        form = SchemeCustomerEditForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer updated successfully.')
            return redirect('scheme:customer-detail', pk=customer.pk)
    else:
        form = SchemeCustomerEditForm(instance=customer)
    return render(request, 'scheme/customer_edit_form.html', {
        'form'    : form,
        'customer': customer,
    })


@manager_required
def customer_suspend(request, pk):
    customer = get_object_or_404(SchemeCustomer, pk=pk)
    if request.method == 'POST':
        customer.status = 'suspended'
        customer.save()
        messages.success(request, f'{customer.full_name} suspended.')
        return redirect('scheme:customer-list')
    return render(request, 'scheme/customer_confirm_suspend.html', {'customer': customer})


@admin_required
def customer_delete(request, pk):
    customer = get_object_or_404(SchemeCustomer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted.')
        return redirect('scheme:customer-list')
    return render(request, 'scheme/customer_confirm_delete.html', {'customer': customer})


# ─── DEPOSIT VIEWS ────────────────────────────────────────────

@sales_required
def deposit_list(request, pk):
    customer = get_object_or_404(SchemeCustomer, pk=pk)
    deposits = customer.deposits.all().order_by('-payment_date')
    return render(request, 'scheme/deposit_list.html', {
        'customer': customer,
        'deposits': deposits,
    })


@sales_required
def deposit_create(request, pk):
    customer = get_object_or_404(SchemeCustomer, pk=pk)
    balance  = get_customer_balance(customer)
    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            deposit             = form.save(commit=False)
            deposit.customer    = customer
            deposit.recorded_by = request.user
            deposit.save()
            messages.success(request, f'Deposit of UGX {deposit.amount:,.0f} recorded.')
            return redirect('scheme:deposit-receipt', pk=deposit.pk)
    else:
        form = DepositForm()
    return render(request, 'scheme/deposit_form.html', {
        'form'    : form,
        'customer': customer,
        'balance' : balance,
    })


@sales_required
def deposit_receipt(request, pk):
    deposit = get_object_or_404(Deposit, pk=pk)
    balance = get_customer_balance(deposit.customer)
    return render(request, 'scheme/deposit_receipt.html', {
        'deposit': deposit,
        'balance': balance,
    })


@admin_required
def deposit_reverse(request, pk):
    deposit = get_object_or_404(Deposit, pk=pk)
    if request.method == 'POST':
        deposit.is_reversed = True
        deposit.save()
        messages.success(request, 'Deposit reversed.')
        return redirect('scheme:customer-detail', pk=deposit.customer.pk)
    return render(request, 'scheme/deposit_confirm_reverse.html', {'deposit': deposit})


# ─── PICKUP VIEWS ─────────────────────────────────────────────

@sales_required
def pickup_list(request, pk):
    customer = get_object_or_404(SchemeCustomer, pk=pk)
    pickups  = customer.pickups.all().order_by('-pickup_date')
    return render(request, 'scheme/pickup_list.html', {
        'customer': customer,
        'pickups' : pickups,
    })


@sales_required
def pickup_create(request, pk):
    customer = get_object_or_404(SchemeCustomer, pk=pk)
    balance  = get_customer_balance(customer)
    if request.method == 'POST':
        form = PickupForm(request.POST, customer=customer)
        if form.is_valid():
            pickup              = form.save(commit=False)
            pickup.customer     = customer
            pickup.processed_by = request.user
            pickup.save()
            messages.success(request, 'Pickup recorded successfully.')
            return redirect('scheme:pickup-detail', pk=pickup.pk)
    else:
        form = PickupForm(customer=customer)
    return render(request, 'scheme/pickup_form.html', {
        'form'    : form,
        'customer': customer,
        'balance' : balance,
    })


@sales_required
def pickup_detail(request, pk):
    pickup = get_object_or_404(Pickup, pk=pk)
    return render(request, 'scheme/pickup_detail.html', {'pickup': pickup})


@manager_required
def pickup_dispatch(request, pk):
    pickup = get_object_or_404(Pickup, pk=pk)
    if request.method == 'POST':
        pickup.status = 'dispatched'
        pickup.save()
        # Auto-create scheme invoice
        SchemeInvoice.objects.create(
            pickup      = pickup,
            customer    = pickup.customer,
            total_value = pickup.total_value,
        )
        # Deduct stock
        product = pickup.product
        product.quantity -= pickup.quantity
        product.save()
        messages.success(request, 'Pickup dispatched and invoice created.')
        return redirect('scheme:pickup-invoice', pk=pickup.pk)
    return render(request, 'scheme/pickup_confirm_dispatch.html', {'pickup': pickup})


@manager_required
def pickup_cancel(request, pk):
    pickup = get_object_or_404(Pickup, pk=pk)
    if request.method == 'POST':
        pickup.status = 'cancelled'
        pickup.save()
        messages.success(request, 'Pickup cancelled.')
        return redirect('scheme:customer-detail', pk=pickup.customer.pk)
    return render(request, 'scheme/pickup_confirm_cancel.html', {'pickup': pickup})


@sales_required
def pickup_invoice(request, pk):
    pickup  = get_object_or_404(Pickup, pk=pk)
    invoice = get_object_or_404(SchemeInvoice, pickup=pickup)
    return render(request, 'scheme/pickup_invoice.html', {
        'pickup' : pickup,
        'invoice': invoice,
    })