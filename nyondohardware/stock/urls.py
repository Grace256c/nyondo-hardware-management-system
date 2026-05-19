from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    # Categories
    path('categories/',                views.category_list,    name='category-list'),
    path('categories/add/',            views.category_create,  name='category-create'),
    path('categories/<int:pk>/edit/',  views.category_update,  name='category-update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category-delete'),

    # Suppliers
    path('suppliers/',                 views.supplier_list,    name='supplier-list'),
    path('suppliers/add/',             views.supplier_create,  name='supplier-create'),
    path('suppliers/<int:pk>/',        views.supplier_detail,  name='supplier-detail'),
    path('suppliers/<int:pk>/edit/',   views.supplier_update,  name='supplier-update'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete,  name='supplier-delete'),

    # Products
    path('',                           views.product_list,     name='product-list'),
    path('products/add/',              views.product_create,   name='product-create'),
    path('products/<int:pk>/',         views.product_detail,   name='product-detail'),
    path('products/<int:pk>/edit/',    views.product_update,   name='product-update'),
    path('products/<int:pk>/delete/',  views.product_delete,   name='product-delete'),

    # Stock Receipts
    path('receipts/',                  views.receipt_list,     name='receipt-list'),
    path('receipts/add/',              views.receipt_create,   name='receipt-create'),
    path('receipts/<int:pk>/',         views.receipt_detail,   name='receipt-detail'),
    path('receipts/<int:pk>/print/',   views.receipt_print,    name='receipt-print'),
    path('receipts/<int:pk>/delete/',  views.receipt_delete,   name='receipt-delete'),

    # Supplier Credits
    path('credits/',                   views.credit_list,      name='credit-list'),
    path('credits/<int:pk>/',          views.credit_detail,    name='credit-detail'),
    path('credits/<int:pk>/edit/',     views.credit_update,    name='credit-update'),
    path('credits/<int:pk>/pay/',      views.credit_pay,       name='credit-pay'),
    path('credits/<int:pk>/payments/', views.credit_payments,  name='credit-payments'),

    # Supplier Payments
    path('payments/<int:pk>/delete/',  views.payment_delete,   name='payment-delete'),

    # Low Stock Alert
    path('alerts/low-stock/',          views.low_stock_alert,  name='low-stock'),
]


