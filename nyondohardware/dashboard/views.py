from django.shortcuts import render
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.contrib.auth.models import User
from stock.models import Product, StockReceipt, SupplierCredit
from sales.models import Invoice, InvoiceItem, Receivable
from scheme.models import SchemeCustomer, Deposit, Pickup
from users.decorators import sales_required, manager_required, admin_required


@sales_required
def home_view(request):
    today = timezone.now().date()

    # Today's sales
    today_invoices = Invoice.objects.filter(
        sale_date=today,
        is_cancelled=False
    )
    today_revenue = today_invoices.aggregate(
        total=Sum('total'))['total'] or 0
    today_invoice_count = today_invoices.count()

    # Low stock
    low_stock_count = Product.objects.filter(
        is_active=True,
        quantity__lte=0
    ).count()

    # Pending scheme pickups
    pending_pickups = Pickup.objects.filter(status='pending').count()

    # Overdue supplier credits
    overdue_credits = SupplierCredit.objects.filter(
        status__in=['unpaid', 'partial']
    ).count()

    # Outstanding receivables
    outstanding_receivables = Receivable.objects.filter(
        status__in=['unpaid', 'partial']
    ).count()

    # Recent invoices
    recent_invoices = Invoice.objects.filter(
        is_cancelled=False
    ).order_by('-created_at')[:5]

    # Low stock products
    low_stock_products = Product.objects.filter(
        is_active=True,
        quantity__lte=0
    ).order_by('quantity')[:5]

    context = {
        'today_revenue'          : today_revenue,
        'today_invoice_count'    : today_invoice_count,
        'low_stock_count'        : low_stock_count,
        'pending_pickups'        : pending_pickups,
        'overdue_credits'        : overdue_credits,
        'outstanding_receivables': outstanding_receivables,
        'recent_invoices'        : recent_invoices,
        'low_stock_products'     : low_stock_products,
        'today'                  : today,
    }
    return render(request, 'dashboard/home.html', context)


@admin_required
def sales_report_view(request):
    date_from = request.GET.get('date_from')
    date_to   = request.GET.get('date_to')

    invoices = Invoice.objects.filter(is_cancelled=False)

    if date_from:
        invoices = invoices.filter(sale_date__gte=date_from)
    if date_to:
        invoices = invoices.filter(sale_date__lte=date_to)

    total_revenue = invoices.aggregate(Sum('total'))['total__sum'] or 0
    total_invoices = invoices.count()

    # Sales by product
    items = InvoiceItem.objects.filter(
        invoice__in=invoices
    ).values('product__name').annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_revenue')

    context = {
        'invoices'      : invoices.order_by('-sale_date')[:50],
        'total_revenue' : total_revenue,
        'total_invoices': total_invoices,
        'items'         : items,
        'date_from'     : date_from,
        'date_to'       : date_to,
    }
    return render(request, 'dashboard/sales_report.html', context)


@admin_required
def stock_report_view(request):
    products = Product.objects.filter(is_active=True).order_by('category__name', 'name')

    total_cost_value   = sum(p.quantity * p.cost_price for p in products)
    total_retail_value = sum(p.quantity * p.retail_price for p in products)

    context = {
        'products'          : products,
        'total_cost_value'  : total_cost_value,
        'total_retail_value': total_retail_value,
    }
    return render(request, 'dashboard/stock_report.html', context)


@admin_required
def profit_loss_view(request):
    date_from = request.GET.get('date_from')
    date_to   = request.GET.get('date_to')

    items = InvoiceItem.objects.filter(
        invoice__is_cancelled=False
    )

    if date_from:
        items = items.filter(invoice__sale_date__gte=date_from)
    if date_to:
        items = items.filter(invoice__sale_date__lte=date_to)

    product_stats = items.values('product__name').annotate(
        qty_sold     = Sum('quantity'),
        total_revenue= Sum('total_price'),
    )

    for stat in product_stats:
        from stock.models import Product as P
        try:
            product = P.objects.get(name=stat['product__name'])
            stat['total_cost']   = stat['qty_sold'] * product.cost_price
            stat['gross_profit'] = stat['total_revenue'] - stat['total_cost']
            stat['margin']       = (stat['gross_profit'] / stat['total_revenue'] * 100) if stat['total_revenue'] else 0
        except:
            stat['total_cost']   = 0
            stat['gross_profit'] = 0
            stat['margin']       = 0

    total_revenue = sum(s['total_revenue'] for s in product_stats)
    total_cost    = sum(s['total_cost'] for s in product_stats)
    gross_profit  = total_revenue - total_cost

    context = {
        'product_stats': product_stats,
        'total_revenue': total_revenue,
        'total_cost'   : total_cost,
        'gross_profit' : gross_profit,
        'date_from'    : date_from,
        'date_to'      : date_to,
    }
    return render(request, 'dashboard/profit_loss.html', context)


@admin_required
def scheme_summary_view(request):
    customers = SchemeCustomer.objects.all()
    from scheme.utils import get_customer_balance
    for customer in customers:
        customer.balance = get_customer_balance(customer)

    total_deposits = Deposit.objects.filter(
        is_reversed=False
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    total_pickups = Pickup.objects.exclude(
        status='cancelled'
    ).aggregate(Sum('total_value'))['total_value__sum'] or 0

    context = {
        'customers'     : customers,
        'total_deposits': total_deposits,
        'total_pickups' : total_pickups,
        'net_balance'   : total_deposits - total_pickups,
    }
    return render(request, 'dashboard/scheme_summary.html', context)