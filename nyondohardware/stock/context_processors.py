from django.db.models import F


def low_stock_count(request):
    if request.user.is_authenticated:
        try:
            from stock.models import Product
            count = Product.objects.filter(
                is_active=True,
                quantity__lte=F('reorder_level')
            ).count()
            return {'low_stock_count': count}
        except Exception:
            return {'low_stock_count': 0}
    return {'low_stock_count': 0}