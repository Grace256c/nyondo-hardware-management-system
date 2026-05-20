from django.urls import path
from . import views

app_name = 'scheme'

urlpatterns = [
    # Scheme Customers
    path('customers/',                          views.customer_list,      name='customer-list'),
    path('customers/register/',                 views.customer_create,    name='customer-create'),
    path('customers/<int:pk>/',                 views.customer_detail,    name='customer-detail'),
    path('customers/<int:pk>/edit/',            views.customer_update,    name='customer-update'),
    path('customers/<int:pk>/suspend/',         views.customer_suspend,   name='customer-suspend'),
    path('customers/<int:pk>/delete/',          views.customer_delete,    name='customer-delete'),

    # Deposits
    path('customers/<int:pk>/deposit/',         views.deposit_create,     name='deposit-create'),
    path('customers/<int:pk>/deposits/',        views.deposit_list,       name='deposit-list'),
    path('deposits/<int:pk>/receipt/',          views.deposit_receipt,    name='deposit-receipt'),
    path('deposits/<int:pk>/reverse/',          views.deposit_reverse,    name='deposit-reverse'),

    # Pickups
    path('customers/<int:pk>/pickup/',          views.pickup_create,      name='pickup-create'),
    path('customers/<int:pk>/pickups/',         views.pickup_list,        name='pickup-list'),
    path('pickups/<int:pk>/',                   views.pickup_detail,      name='pickup-detail'),
    path('pickups/<int:pk>/dispatch/',          views.pickup_dispatch,    name='pickup-dispatch'),
    path('pickups/<int:pk>/cancel/',            views.pickup_cancel,      name='pickup-cancel'),
    path('pickups/<int:pk>/invoice/',           views.pickup_invoice,     name='pickup-invoice'),
]