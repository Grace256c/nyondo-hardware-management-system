from django.shortcuts import render
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal
from stock.models import Product, SupplierCredit
from sales.models import Invoice, InvoiceItem, Receivable
from scheme.models import SchemeCustomer, Deposit, Pickup
from users.decorators import sales_required, admin_required


@sales_required
def home_view(request):
    today = timezone.now().date()

    today_invoices     = Invoice.objects.filter(sale_date=today, is_cancelled=False)
    today_revenue      = today_invoices.aggregate(total=Sum('total'))['total'] or 0
    today_invoice_count = today_invoices.count()

    low_stock_count    = Product.objects.filter(is_active=True, quantity__lte=0).count()
    pending_pickups    = Pickup.objects.filter(status='pending').count()
    overdue_credits    = SupplierCredit.objects.filter(status__in=['unpaid', 'partial']).count()
    outstanding_receivables = Receivable.objects.filter(status__in=['unpaid', 'partial']).count()
    recent_invoices    = Invoice.objects.filter(is_cancelled=False).order_by('-created_at')[:5]
    low_stock_products = Product.objects.filter(is_active=True, quantity__lte=0).order_by('quantity')[:5]

    return render(request, 'dashboard/home.html', {
        'today_revenue'          : today_revenue,
        'today_invoice_count'    : today_invoice_count,
        'low_stock_count'        : low_stock_count,
        'pending_pickups'        : pending_pickups,
        'overdue_credits'        : overdue_credits,
        'outstanding_receivables': outstanding_receivables,
        'recent_invoices'        : recent_invoices,
        'low_stock_products'     : low_stock_products,
        'today'                  : today,
    })


@admin_required
def sales_report_view(request):
    date_from = request.GET.get('date_from')
    date_to   = request.GET.get('date_to')

    invoices = Invoice.objects.filter(is_cancelled=False)
    if date_from:
        invoices = invoices.filter(sale_date__gte=date_from)
    if date_to:
        invoices = invoices.filter(sale_date__lte=date_to)

    total_revenue  = invoices.aggregate(Sum('total'))['total__sum'] or 0
    total_invoices = invoices.count()

    items = InvoiceItem.objects.filter(
        invoice__in=invoices
    ).values('product__name').annotate(
        total_qty     = Sum('quantity'),
        total_revenue = Sum('total_price')
    ).order_by('-total_revenue')

    return render(request, 'dashboard/sales_report.html', {
        'invoices'      : invoices.order_by('-sale_date')[:50],
        'total_revenue' : total_revenue,
        'total_invoices': total_invoices,
        'items'         : items,
        'date_from'     : date_from,
        'date_to'       : date_to,
    })


@admin_required
def stock_report_view(request):
    products           = Product.objects.filter(is_active=True).order_by('category__name', 'name')
    total_cost_value   = sum(p.quantity * p.cost_price for p in products)
    total_retail_value = sum(p.quantity * p.retail_price for p in products)

    return render(request, 'dashboard/stock_report.html', {
        'products'          : products,
        'total_cost_value'  : total_cost_value,
        'total_retail_value': total_retail_value,
    })


@admin_required
def profit_loss_view(request):
    date_from = request.GET.get('date_from')
    date_to   = request.GET.get('date_to')

    items = InvoiceItem.objects.filter(invoice__is_cancelled=False)
    if date_from:
        items = items.filter(invoice__sale_date__gte=date_from)
    if date_to:
        items = items.filter(invoice__sale_date__lte=date_to)

    product_stats = []
    for item in items.values('product__name', 'product__id').annotate(
        qty_sold      = Sum('quantity'),
        total_revenue = Sum('total_price')
    ):
        try:
            product      = Product.objects.get(pk=item['product__id'])
            total_cost   = Decimal(str(item['qty_sold'])) * product.cost_price
            gross_profit = item['total_revenue'] - total_cost
            margin       = (gross_profit / item['total_revenue'] * 100) if item['total_revenue'] else 0
        except Exception:
            total_cost   = Decimal('0')
            gross_profit = Decimal('0')
            margin       = 0

        product_stats.append({
            'product__name': item['product__name'],
            'qty_sold'     : item['qty_sold'],
            'total_revenue': item['total_revenue'],
            'total_cost'   : total_cost,
            'gross_profit' : gross_profit,
            'margin'       : margin,
        })

    total_revenue = sum(s['total_revenue'] for s in product_stats) or Decimal('0')
    total_cost    = sum(s['total_cost'] for s in product_stats) or Decimal('0')
    gross_profit  = total_revenue - total_cost

    return render(request, 'dashboard/profit_loss.html', {
        'product_stats': product_stats,
        'total_revenue': total_revenue,
        'total_cost'   : total_cost,
        'gross_profit' : gross_profit,
        'date_from'    : date_from,
        'date_to'      : date_to,
    })


@admin_required
def scheme_summary_view(request):
    from scheme.utils import get_customer_balance
    customers = SchemeCustomer.objects.all()
    for customer in customers:
        customer.balance = get_customer_balance(customer)

    total_deposits = Deposit.objects.filter(
        is_reversed=False
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    total_pickups = Pickup.objects.exclude(
        status='cancelled'
    ).aggregate(Sum('total_value'))['total_value__sum'] or 0

    return render(request, 'dashboard/scheme_summary.html', {
        'customers'     : customers,
        'total_deposits': total_deposits,
        'total_pickups' : total_pickups,
        'net_balance'   : Decimal(str(total_deposits)) - Decimal(str(total_pickups)),
    })