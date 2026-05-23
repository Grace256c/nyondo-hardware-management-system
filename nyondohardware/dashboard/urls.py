from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('',                        views.home_view,          name='home'),
    path('reports/sales/',          views.sales_report_view,  name='sales-report'),
    path('reports/stock/',          views.stock_report_view,  name='stock-report'),
    path('reports/profit-loss/',    views.profit_loss_view,   name='profit-loss'),
    path('reports/scheme/',         views.scheme_summary_view, name='scheme-report'),
]