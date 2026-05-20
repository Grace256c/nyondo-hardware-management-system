from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # Customers
    path('customers/',                    views.customer_list,       name='customer-list'),
    path('customers/add/',                views.customer_create,     name='customer-create'),
    path('customers/<int:pk>/',           views.customer_detail,     name='customer-detail'),
    path('customers/<int:pk>/edit/',      views.customer_update,     name='customer-update'),
    path('customers/<int:pk>/delete/',    views.customer_delete,     name='customer-delete'),

    # Invoices
    path('invoices/',                     views.invoice_list,        name='invoice-list'),
    path('invoices/create/',              views.invoice_create,      name='invoice-create'),
    path('invoices/<int:pk>/',            views.invoice_detail,      name='invoice-detail'),
    path('invoices/<int:pk>/edit/',       views.invoice_update,      name='invoice-update'),
    path('invoices/<int:pk>/delete/',     views.invoice_delete,      name='invoice-delete'),
    path('invoices/<int:pk>/print/',      views.invoice_print,       name='invoice-print'),
    path('invoices/<int:pk>/transport/',  views.transport_override,  name='transport-override'),

    # Receivables
    path('receivables/',                  views.receivable_list,     name='receivable-list'),
    path('receivables/<int:pk>/',         views.receivable_detail,   name='receivable-detail'),
    path('receivables/<int:pk>/pay/',     views.receivable_pay,      name='receivable-pay'),
    path('receivables/<int:pk>/write-off/', views.receivable_writeoff, name='receivable-writeoff'),
    path('receivables/<int:pk>/delete/', views.receivable_delete,   name='receivable-delete'),

    # AJAX
    path('ajax/product-price/',           views.ajax_product_price,  name='ajax-price'),
    path('ajax/transport/',               views.ajax_transport,      name='ajax-transport'),
]