# Nyondo Hardware Management System

A web-based management system for **NYONDO General Hardware LTD**, built with Django and SQLite. The system digitizes stock management, sales, supplier credit tracking, a salary-earner deposit scheme, and user/role management.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Apps](#apps)
  - [Users](#1-users-app)
  - [Stock](#2-stock-app-core)
  - [Sales](#3-sales-app)
  - [Scheme](#4-scheme-app)
  - [Dashboard](#5-dashboard-app)
- [Models Summary](#models-summary)
- [URL Structure](#url-structure)
- [Templates](#templates)
- [Validation Rules](#validation-rules)
- [User Roles & Permissions](#user-roles--permissions)
- [Build Order](#build-order)
- [Setup & Installation](#setup--installation)

---

## Project Overview

NYONDO General Hardware LTD is a wholesale and retail hardware store in Nansana dealing in cement, iron bars, nails, iron sheets, wheelbarrows, wire mesh, and barbed wire. This system replaces manual record-keeping with a centralized digital solution.

**Core features:**
- Stock registration and real-time inventory tracking
- Sales invoicing with automatic transport charge calculation
- Supplier credit recording and payment tracking
- Customer credit (receivables) management
- Salary-earner deposit scheme for deferred goods pickup
- Role-based access control for staff
- Sales, stock, and profit/loss reports with Excel export

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Django |
| Database | SQLite |
| Frontend | HTML, CSS
| Excel Export | openpyxl |
| Version Control | Git & GitHub |

---

## Project Structure

```
nyondo/
├── manage.py
├── nyondo/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── users/
│   ├── stock/
│   ├── sales/
│   ├── scheme/
│   └── dashboard/
├── templates/
│   ├── base.html
│   ├── partials/
│   │   ├── _navbar.html
│   │   ├── _sidebar.html
│   │   ├── _messages.html
│   │   ├── _pagination.html
│   │   └── _confirm_delete_modal.html
│   ├── users/
│   ├── stock/
│   ├── sales/
│   ├── scheme/
│   └── dashboard/
└── static/
    ├── css/
    └── js/
        └── invoice.js
```

`base.html` is the master layout extended by every template. It includes the navbar, role-aware sidebar, flash messages block, `{% block content %}` placeholder, and footer.

---

## Apps

---

### 1. Users App

Handles authentication, user creation, and role-based access control using Django's built-in `User` model extended with a `UserProfile`.

#### Models

**`UserProfile`**
| Field | Type | Notes |
|---|---|---|
| user | OneToOneField(User) | auto-created via post_save signal |
| role | CharField | choices: sales_attendant, store_manager, admin |
| phone | CharField | Ugandan phone format |
| is_active | BooleanField | default True |
| created_at | DateTimeField | auto_now_add |

#### URLs

| URL | View | Name |
|---|---|---|
| `users/login/` | Login | `users:login` |
| `users/logout/` | Logout | `users:logout` |
| `users/register/` | Create user (admin only) | `users:register` |
| `users/` | User list (admin only) | `users:user-list` |
| `users/<id>/` | User detail | `users:user-detail` |
| `users/<id>/edit/` | Edit role/phone/status | `users:user-update` |
| `users/<id>/deactivate/` | Deactivate user | `users:user-deactivate` |
| `users/<id>/delete/` | Hard delete (admin only) | `users:user-delete` |
| `users/profile/` | Own profile | `users:profile` |

#### Templates

| Template | Description |
|---|---|
| `users/login.html` | Centered login form with company logo |
| `users/register.html` | Admin-only: username, name, phone, role, password |
| `users/user_list.html` | Table of all users with role badge and status |
| `users/user_detail.html` | Profile card with activity summary |
| `users/user_edit_form.html` | Edit role, phone, active status |
| `users/user_confirm_deactivate.html` | Deactivation confirmation |
| `users/user_confirm_delete.html` | Delete confirmation with data warning |
| `users/profile.html` | Own profile with password change option |

#### Forms

- `UserRegistrationForm` — extends `UserCreationForm`, adds phone and role
- `UserEditForm` — role, phone, is_active only
- `CustomPasswordChangeForm` — wraps Django's built-in password change

#### Decorators (`users/decorators.py`)

- `@sales_required` — sales attendants, managers, admins
- `@manager_required` — managers and admins only
- `@admin_required` — admins only

---

### 2. Stock App (Core)

The foundation of the whole system. Every other app depends on stock data. Build and test this first.

Also contains **supplier credit** logic since credit is created at the point of stock receipt.

##### Models

**`Category`**
| Field | Type | Notes |
|---|---|---|
| name | CharField | unique |
| description | TextField | blank |

Seed data: Cement, Iron Bars, Nails, Iron Sheets, Wheelbarrows, Wire Mesh, Barbed Wire.

---

**`Supplier`**
| Field | Type | Notes |
|---|---|---|
| name | CharField | |
| phone | CharField | Ugandan phone validation |
| address | TextField | |
| tin | CharField | blank |
| is_active | BooleanField | default True |
| created_at | DateTimeField | auto_now_add |

---

**`Product`**
| Field | Type | Notes |
|---|---|---|
| name | CharField | |
| category | ForeignKey(Category) | on_delete=PROTECT |
| unit | CharField | choices: bag, kg, piece, roll, sheet, pack, length |
| cost_price | DecimalField | |
| retail_price | DecimalField | must be > cost_price |
| wholesale_price | DecimalField | must be > cost_price |
| quantity | DecimalField | updated by receipts and sales |
| reorder_level | DecimalField | default 10 |
| description | TextField | blank |
| is_active | BooleanField | default True |
| created_at | DateTimeField | auto_now_add |
| updated_at | DateTimeField | auto_now |

---

**`StockReceipt`**
| Field | Type | Notes |
|---|---|---|
| grn_number | CharField | unique, auto-generated: GRN-YYYYMMDD-XXXX |
| supplier | ForeignKey(Supplier) | on_delete=PROTECT |
| product | ForeignKey(Product) | on_delete=PROTECT |
| quantity | DecimalField | |
| unit_cost | DecimalField | |
| total_cost | DecimalField | computed: quantity × unit_cost |
| payment_status | CharField | choices: cash, credit |
| receipt_date | DateField | |
| notes | TextField | blank |
| recorded_by | ForeignKey(User) | on_delete=PROTECT |
| created_at | DateTimeField | auto_now_add |

On save: adds quantity to `product.quantity`. If `payment_status='credit'`, a post_save signal auto-creates a `SupplierCredit`.

---

**`SupplierCredit`**
| Field | Type | Notes |
|---|---|---|
| stock_receipt | OneToOneField(StockReceipt) | on_delete=PROTECT |
| supplier | ForeignKey(Supplier) | on_delete=PROTECT |
| total_amount | DecimalField | |
| amount_paid | DecimalField | default 0 |
| balance | DecimalField | auto = total_amount - amount_paid |
| due_date | DateField | null, blank |
| status | CharField | choices: unpaid, partial, paid |
| notes | TextField | blank |
| created_at | DateTimeField | auto_now_add |

---

**`SupplierPayment`**
| Field | Type | Notes |
|---|---|---|
| credit | ForeignKey(SupplierCredit) | related_name='payments' |
| amount | DecimalField | |
| payment_date | DateField | |
| payment_method | CharField | choices: cash, mobile_money, bank_transfer, cheque |
| reference | CharField | blank |
| recorded_by | ForeignKey(User) | on_delete=PROTECT |
| created_at | DateTimeField | auto_now_add |

On save: updates `credit.amount_paid`, recalculates `balance`, updates `status`.

#### URLs

| URL | Name |
|---|---|
| `stock/` | `stock:product-list` |
| `stock/products/add/` | `stock:product-create` |
| `stock/products/<id>/` | `stock:product-detail` |
| `stock/products/<id>/edit/` | `stock:product-update` |
| `stock/products/<id>/delete/` | `stock:product-delete` |
| `stock/categories/` | `stock:category-list` |
| `stock/categories/add/` | `stock:category-create` |
| `stock/categories/<id>/edit/` | `stock:category-update` |
| `stock/categories/<id>/delete/` | `stock:category-delete` |
| `stock/suppliers/` | `stock:supplier-list` |
| `stock/suppliers/add/` | `stock:supplier-create` |
| `stock/suppliers/<id>/` | `stock:supplier-detail` |
| `stock/suppliers/<id>/edit/` | `stock:supplier-update` |
| `stock/suppliers/<id>/delete/` | `stock:supplier-delete` |
| `stock/receipts/` | `stock:receipt-list` |
| `stock/receipts/add/` | `stock:receipt-create` |
| `stock/receipts/<id>/` | `stock:receipt-detail` |
| `stock/receipts/<id>/edit/` | `stock:receipt-update` |
| `stock/receipts/<id>/delete/` | `stock:receipt-delete` |
| `stock/receipts/<id>/print/` | `stock:receipt-print` |
| `stock/credits/` | `stock:credit-list` |
| `stock/credits/<id>/` | `stock:credit-detail` |
| `stock/credits/<id>/edit/` | `stock:credit-update` |
| `stock/credits/<id>/pay/` | `stock:credit-pay` |
| `stock/credits/<id>/payments/` | `stock:credit-payments` |
| `stock/payments/<id>/edit/` | `stock:payment-update` |
| `stock/payments/<id>/delete/` | `stock:payment-delete` |
| `stock/alerts/low-stock/` | `stock:low-stock` |

#### Templates

| Template | Description |
|---|---|
| `stock/product_list.html` | Product table with color-coded stock level badges |
| `stock/product_form.html` | Shared create/edit form |
| `stock/product_detail.html` | Product info + receipt history |
| `stock/product_confirm_delete.html` | Block if product has sales history |
| `stock/category_list.html` | Category table with product count |
| `stock/category_form.html` | Name and description |
| `stock/category_confirm_delete.html` | Shows product count before confirming |
| `stock/supplier_list.html` | Supplier table with outstanding credit total |
| `stock/supplier_form.html` | Name, phone, address, TIN |
| `stock/supplier_detail.html` | Supplier info + all GRNs + credit balance |
| `stock/supplier_confirm_delete.html` | Block if supplier has open credit |
| `stock/receipt_list.html` | GRN table with date, status, and filters |
| `stock/receipt_form.html` | Supplier, product, qty, unit cost, payment status |
| `stock/receipt_detail.html` | Full GRN details |
| `stock/receipt_print.html` | Print-only GRN layout with signature lines |
| `stock/receipt_confirm_delete.html` | Block if stock already used in sales |
| `stock/credit_list.html` | Supplier credits with aging column and status badges |
| `stock/credit_detail.html` | Credit summary + payment history |
| `stock/credit_form.html` | Edit due date and notes only |
| `stock/credit_pay_form.html` | Record payment with remaining balance shown |
| `stock/payment_list.html` | All payments against one credit |
| `stock/payment_edit_form.html` | Admin only |
| `stock/payment_confirm_delete.html` | Shows balance impact before reversing |
| `stock/low_stock_alert.html` | Products at or below reorder level |

#### Forms (`stock/forms.py`)

- `CategoryForm` — name and description, uniqueness validated
- `ProductForm` — all fields, `clean()` enforces retail and wholesale > cost price
- `SupplierForm` — includes phone `RegexValidator`
- `StockReceiptForm` — quantity and unit cost validated positive in `clean()`
- `SupplierCreditEditForm` — due date and notes only
- `SupplierPaymentForm` — `clean_amount()` checks amount does not exceed balance

---

### 3. Sales App

Handles customer management, invoicing, transport calculation, and customer credit (receivables).

#### Transport Rule (`sales/utils.py`)

```python
def calculate_transport(distance_km, invoice_total):
    if distance_km <= 10 and invoice_total >= 500000:
        return 0
    return 30000
```

Called automatically in `Invoice.save()` and via AJAX while the invoice form is being filled.

#### Models

**`Customer`**
| Field | Type | Notes |
|---|---|---|
| name | CharField | |
| phone | CharField | Ugandan phone validation |
| customer_type | CharField | choices: retail, wholesale, walk_in |
| address | TextField | blank |
| distance_km | DecimalField | default 0, used for transport rule |
| is_active | BooleanField | default True |
| created_at | DateTimeField | auto_now_add |

---

**`Invoice`**
| Field | Type | Notes |
|---|---|---|
| invoice_number | CharField | unique, auto-generated: INV-YYYYMMDD-XXXX |
| customer | ForeignKey(Customer) | null/blank for walk-in |
| customer_name | CharField | fallback for walk-in |
| customer_type | CharField | choices: retail, wholesale, walk_in |
| payment_method | CharField | choices: cash, mobile_money, bank_transfer, cheque, scheme |
| payment_status | CharField | choices: paid, credit, partial |
| transport_charge | DecimalField | auto-calculated |
| subtotal | DecimalField | |
| total | DecimalField | subtotal + transport_charge |
| amount_paid | DecimalField | default 0 |
| balance | DecimalField | total - amount_paid |
| sale_date | DateField | auto_now_add |
| notes | TextField | blank |
| served_by | ForeignKey(User) | on_delete=PROTECT |
| is_cancelled | BooleanField | default False |
| created_at | DateTimeField | auto_now_add |

On save: transport auto-calculated. If `payment_status` is credit or partial, a signal auto-creates a `Receivable`.

---

**`InvoiceItem`**
| Field | Type | Notes |
|---|---|---|
| invoice | ForeignKey(Invoice) | related_name='items', on_delete=CASCADE |
| product | ForeignKey(Product) | on_delete=PROTECT |
| quantity | DecimalField | validated against available stock |
| unit_price | DecimalField | auto-set from customer_type |
| total_price | DecimalField | quantity × unit_price |

On save: deducts quantity from `product.quantity`. Raises `ValidationError` if quantity exceeds available stock.

---

**`Receivable`**
| Field | Type | Notes |
|---|---|---|
| invoice | OneToOneField(Invoice) | on_delete=PROTECT |
| customer | ForeignKey(Customer) | on_delete=PROTECT |
| total_amount | DecimalField | |
| amount_paid | DecimalField | default 0 |
| balance | DecimalField | |
| due_date | DateField | null, blank |
| status | CharField | choices: unpaid, partial, paid, written_off |
| notes | TextField | blank |
| created_at | DateTimeField | auto_now_add |

---

**`CustomerPayment`**
| Field | Type | Notes |
|---|---|---|
| receivable | ForeignKey(Receivable) | related_name='payments' |
| amount | DecimalField | |
| payment_date | DateField | |
| payment_method | CharField | |
| reference | CharField | blank |
| recorded_by | ForeignKey(User) | on_delete=PROTECT |
| created_at | DateTimeField | auto_now_add |

On save: updates `receivable.amount_paid`, recalculates balance, updates status.

#### URLs

| URL | Name |
|---|---|
| `sales/customers/` | `sales:customer-list` |
| `sales/customers/add/` | `sales:customer-create` |
| `sales/customers/<id>/` | `sales:customer-detail` |
| `sales/customers/<id>/edit/` | `sales:customer-update` |
| `sales/customers/<id>/delete/` | `sales:customer-delete` |
| `sales/invoices/` | `sales:invoice-list` |
| `sales/invoices/create/` | `sales:invoice-create` |
| `sales/invoices/<id>/` | `sales:invoice-detail` |
| `sales/invoices/<id>/edit/` | `sales:invoice-update` |
| `sales/invoices/<id>/delete/` | `sales:invoice-delete` |
| `sales/invoices/<id>/print/` | `sales:invoice-print` |
| `sales/invoices/<id>/transport/` | `sales:transport-override` |
| `sales/invoices/export/` | `sales:invoice-export` |
| `sales/receivables/` | `sales:receivable-list` |
| `sales/receivables/<id>/` | `sales:receivable-detail` |
| `sales/receivables/<id>/pay/` | `sales:receivable-pay` |
| `sales/receivables/<id>/write-off/` | `sales:receivable-writeoff` |
| `sales/receivables/<id>/delete/` | `sales:receivable-delete` |
| `sales/receivables/<id>/payments/` | `sales:receivable-payments` |
| `sales/ajax/product-price/` | `sales:ajax-price` |
| `sales/ajax/transport/` | `sales:ajax-transport` |

#### Templates

| Template | Description |
|---|---|
| `sales/customer_list.html` | Searchable customer table with type badges |
| `sales/customer_form.html` | Name, phone, type, address, distance |
| `sales/customer_detail.html` | Profile + invoice history + outstanding balance |
| `sales/customer_confirm_delete.html` | Block if unpaid invoices exist |
| `sales/invoice_list.html` | Invoice table with filters by date, status, method |
| `sales/invoice_create.html` | Main sales form: dynamic product rows, live totals, transport preview, AJAX-driven |
| `sales/invoice_detail.html` | Invoice header, line items, totals, payment info |
| `sales/invoice_edit.html` | Restricted edit — unpaid and same-day only |
| `sales/invoice_print.html` | Print-only receipt, no navigation |
| `sales/invoice_confirm_delete.html` | Warns stock will be restocked on cancellation |
| `sales/receivable_list.html` | Customer credits with aging and status |
| `sales/receivable_detail.html` | Credit summary + payment history |
| `sales/receivable_pay_form.html` | Record payment with balance shown above |
| `sales/receivable_writeoff_form.html` | Mandatory reason, strong warning message |
| `sales/receivable_confirm_delete.html` | Admin only |
| `sales/payment_list.html` | Payments against one receivable with running balance |

#### Forms (`sales/forms.py`)

- `CustomerForm` — Ugandan phone regex validation
- `InvoiceForm` — customer, type, payment method, status, amount paid, notes
- `InvoiceItemFormSet` — `inlineformset_factory`, min one row, can_delete=True
- `TransportOverrideForm` — transport charge + mandatory reason
- `ReceivableEditForm` — due date and notes
- `CustomerPaymentForm` — `clean_amount()` checks amount does not exceed balance

#### JavaScript (`static/js/invoice.js`)

Powers the dynamic invoice creation form:
- On product selection: fires AJAX to `sales:ajax-price`, fills unit price, recalculates row total
- On quantity change: recalculates row total
- After any row change: recalculates subtotal, fires AJAX to `sales:ajax-transport`, updates transport charge and grand total
- Add row: clones last row, clears values, appends to table
- Remove row: deletes row, triggers recalculation
- Submit disabled until at least one valid product row exists

---

### 4. Scheme App

Manages the salary-earner deposit scheme. Customers register, make deposits over time, then pick up goods (cement, iron bars, or iron sheets only) up to the value of their balance.

#### Balance Utility (`scheme/utils.py`)

```python
def get_customer_balance(customer):
    total_deposits = customer.deposits.filter(
        is_reversed=False
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    total_pickups = customer.pickups.exclude(
        status='cancelled'
    ).aggregate(Sum('total_value'))['total_value__sum'] or 0

    return total_deposits - total_pickups
```

Never stored as a field — always computed fresh to stay accurate after reversals and cancellations.

#### Allowed Products Utility (`scheme/utils.py`)

```python
SCHEME_ALLOWED_CATEGORIES = ['Cement', 'Iron Bars', 'Iron Sheets']

def get_scheme_products():
    return Product.objects.filter(
        category__name__in=SCHEME_ALLOWED_CATEGORIES,
        is_active=True
    )
```

Used as the queryset on the product field in `PickupForm`.

#### Models

**`SchemeCustomer`**
| Field | Type | Notes |
|---|---|---|
| full_name | CharField | must match NIN, locked after registration |
| nin | CharField | unique, regex: `^[A-Z0-9]{14}$`, locked after registration |
| phone | CharField | Ugandan phone validation |
| employer | CharField | blank |
| employer_address | TextField | blank |
| registration_date | DateField | auto_now_add |
| status | CharField | choices: active, suspended |
| registered_by | ForeignKey(User) | on_delete=PROTECT |

---

**`Deposit`**
| Field | Type | Notes |
|---|---|---|
| customer | ForeignKey(SchemeCustomer) | related_name='deposits' |
| amount | DecimalField | |
| payment_date | DateField | |
| payment_method | CharField | choices: cash, mobile_money, bank_transfer |
| receipt_number | CharField | unique, auto-generated: RCPT-YYYYMMDD-XXXX |
| recorded_by | ForeignKey(User) | on_delete=PROTECT |
| created_at | DateTimeField | auto_now_add |
| is_reversed | BooleanField | default False |

---

**`Pickup`**
| Field | Type | Notes |
|---|---|---|
| customer | ForeignKey(SchemeCustomer) | related_name='pickups' |
| product | ForeignKey(Product) | limited to allowed categories |
| quantity | DecimalField | |
| unit_price | DecimalField | |
| total_value | DecimalField | quantity × unit_price |
| pickup_date | DateField | |
| status | CharField | choices: pending, dispatched, cancelled |
| processed_by | ForeignKey(User) | on_delete=PROTECT |
| created_at | DateTimeField | auto_now_add |

On dispatch: deducts stock, deducts from customer balance, auto-creates `SchemeInvoice`.

---

**`SchemeInvoice`**
| Field | Type | Notes |
|---|---|---|
| invoice_number | CharField | unique, auto-generated: SINV-YYYYMMDD-XXXX |
| pickup | OneToOneField(Pickup) | on_delete=PROTECT |
| customer | ForeignKey(SchemeCustomer) | on_delete=PROTECT |
| total_value | DecimalField | |
| issue_date | DateField | auto_now_add |
| printed | BooleanField | default False |

#### URLs

| URL | Name |
|---|---|
| `scheme/customers/` | `scheme:customer-list` |
| `scheme/customers/register/` | `scheme:customer-create` |
| `scheme/customers/<id>/` | `scheme:customer-detail` |
| `scheme/customers/<id>/edit/` | `scheme:customer-update` |
| `scheme/customers/<id>/suspend/` | `scheme:customer-suspend` |
| `scheme/customers/<id>/delete/` | `scheme:customer-delete` |
| `scheme/customers/<id>/deposit/` | `scheme:deposit-create` |
| `scheme/customers/<id>/deposits/` | `scheme:deposit-list` |
| `scheme/deposits/<id>/receipt/` | `scheme:deposit-receipt` |
| `scheme/deposits/<id>/edit/` | `scheme:deposit-update` |
| `scheme/deposits/<id>/reverse/` | `scheme:deposit-reverse` |
| `scheme/customers/<id>/pickup/` | `scheme:pickup-create` |
| `scheme/customers/<id>/pickups/` | `scheme:pickup-list` |
| `scheme/pickups/<id>/` | `scheme:pickup-detail` |
| `scheme/pickups/<id>/edit/` | `scheme:pickup-update` |
| `scheme/pickups/<id>/dispatch/` | `scheme:pickup-dispatch` |
| `scheme/pickups/<id>/cancel/` | `scheme:pickup-cancel` |
| `scheme/pickups/<id>/invoice/` | `scheme:pickup-invoice` |

#### Templates

| Template | Description |
|---|---|
| `scheme/customer_list.html` | Table with masked NIN, balance, status badge |
| `scheme/customer_register_form.html` | Full registration with NIN and phone validation hints |
| `scheme/customer_detail.html` | Balance card at top, deposit history, pickup history |
| `scheme/customer_edit_form.html` | Phone and employer only; name and NIN shown read-only |
| `scheme/customer_confirm_suspend.html` | Shows balance, requires reason |
| `scheme/customer_confirm_delete.html` | Admin only, shows transaction count |
| `scheme/deposit_list.html` | Deposits with running total column |
| `scheme/deposit_form.html` | Amount, date, method; current balance shown above |
| `scheme/deposit_receipt.html` | Print-only temporary receipt with "This is a temporary receipt" note |
| `scheme/deposit_edit_form.html` | Admin only, warns if editing after 24 hours |
| `scheme/deposit_confirm_reverse.html` | Warns if goods already picked against balance |
| `scheme/pickup_list.html` | Pickups with status badges and invoice links |
| `scheme/pickup_form.html` | Filtered product dropdown, live balance check, submit disabled if over balance |
| `scheme/pickup_detail.html` | Pickup info, dispatch and cancel buttons |
| `scheme/pickup_edit_form.html` | Manager only, pending status only |
| `scheme/pickup_confirm_cancel.html` | Shows value returned to balance and stock restocked |
| `scheme/pickup_invoice.html` | Print-only scheme invoice with signature lines |

#### Forms (`scheme/forms.py`)

- `SchemeCustomerRegistrationForm` — NIN `RegexValidator(r'^[A-Z0-9]{14}$')`, Ugandan phone, `clean_nin()` checks uniqueness
- `SchemeCustomerEditForm` — phone and employer only; NIN and name excluded
- `DepositForm` — amount, date, method; `clean_amount()` validates positive
- `DepositEditForm` — amount and date only, admin restricted in view
- `PickupForm` — product queryset from `get_scheme_products()`, `clean()` calls `get_customer_balance()` and raises `ValidationError` if total_value exceeds balance

---

### 5. Dashboard App

Read-only reporting views. No models. Aggregates data across all other apps.

#### Views (`dashboard/views.py`)

| View | What it computes |
|---|---|
| `home_view` | Today's revenue, invoices today, low-stock count, pending pickups, overdue supplier credits |
| `sales_report_view` | Revenue by product and customer type, filterable by date, customer, payment method |
| `stock_report_view` | Current inventory with cost value and retail value per product |
| `profit_loss_view` | Revenue minus COGS per product, gross profit and margin %, filterable by date range |
| `scheme_summary_view` | Total deposits, total pickups value, net outstanding balance, active member count |
| `sales_export_view` | Generates `.xlsx` sales report using openpyxl |
| `stock_export_view` | Generates `.xlsx` stock report using openpyxl |

#### URLs

| URL | Name |
|---|---|
| `/` | `dashboard:home` |
| `dashboard/reports/sales/` | `dashboard:sales-report` |
| `dashboard/reports/sales/export/` | `dashboard:sales-export` |
| `dashboard/reports/stock/` | `dashboard:stock-report` |
| `dashboard/reports/stock/export/` | `dashboard:stock-export` |
| `dashboard/reports/profit-loss/` | `dashboard:profit-loss` |
| `dashboard/reports/scheme/` | `dashboard:scheme-report` |

#### Templates

| Template | Description |
|---|---|
| `dashboard/home.html` | KPI cards, quick links by role, low-stock mini-table |
| `dashboard/sales_report.html` | Filter form, summary cards, breakdown table, invoice list, export button |
| `dashboard/stock_report.html` | Category filter, grand totals, product table with valuation, export button |
| `dashboard/profit_loss.html` | Date filter, summary cards, per-product margin table |
| `dashboard/scheme_summary.html` | Summary cards, customer balance table |

---

## Models Summary

| App | Models |
|---|---|
| Users | UserProfile |
| Stock | Category, Supplier, Product, StockReceipt, SupplierCredit, SupplierPayment |
| Sales | Customer, Invoice, InvoiceItem, Receivable, CustomerPayment |
| Scheme | SchemeCustomer, Deposit, Pickup, SchemeInvoice |
| Dashboard | None (reporting only) |

---

## URL Structure

```
/                           → dashboard home
users/                      → user management
stock/                      → stock, suppliers, GRNs, supplier credit
sales/                      → customers, invoices, receivables
scheme/                     → scheme customers, deposits, pickups
dashboard/reports/          → sales, stock, P&L, scheme reports
```

Project-level `nyondo/urls.py`:

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('apps.users.urls')),
    path('stock/', include('apps.stock.urls')),
    path('sales/', include('apps.sales.urls')),
    path('scheme/', include('apps.scheme.urls')),
    path('', include('apps.dashboard.urls')),
]
```

---

## Validation Rules

| Rule | Where enforced |
|---|---|
| Ugandan phone: `^(\+?256\|0)[7][0-9]{8}$` | Every form with a phone field |
| NIN: `^[A-Z0-9]{14}$` | `SchemeCustomerRegistrationForm` |
| Retail and wholesale price must exceed cost price | `ProductForm.clean()` and `Product.clean()` |
| Sale quantity cannot exceed available stock | `InvoiceItemFormSet.clean()` and `InvoiceItem.save()` |
| Scheme pickup value cannot exceed customer balance | `PickupForm.clean()` using `get_customer_balance()` |
| Scheme products restricted to cement, iron bars, iron sheets | Product queryset filtered in `PickupForm` |
| No hard delete on records with child records | All delete views catch `ProtectedError` and show a block message |
| Transport auto-calculated; manager override requires reason | `Invoice.save()` and `TransportOverrideForm` |
| NIN and full name locked after scheme registration | Edit form excludes fields; view never updates them |

---

## User Roles & Permissions

| Action | Sales Attendant | Store Manager | Admin |
|---|---|---|---|
| Record sales | ✓ | ✓ | ✓ |
| Issue receipts | ✓ | ✓ | ✓ |
| View stock levels | ✓ | ✓ | ✓ |
| Record scheme deposits and pickups | ✓ | ✓ | ✓ |
| Register stock receipts | | ✓ | ✓ |
| Add and edit products | | ✓ | ✓ |
| Set prices | | ✓ | ✓ |
| Override transport charges | | ✓ | ✓ |
| Edit and cancel invoices | | ✓ | ✓ |
| Register scheme customers | | ✓ | ✓ |
| Create and deactivate users | | | ✓ |
| Delete records | | | ✓ |
| View all reports | | | ✓ |
| Write off receivables | | | ✓ |
| Reverse deposits | | | ✓ |

---

## Build Order

Build strictly in this sequence to avoid missing foreign key dependencies:

1. **Users** — authentication and role decorators working before anything else is built
2. **Stock** — Category → Supplier → Product → StockReceipt → SupplierCredit → SupplierPayment. Test all CRUD and GRN auto-generation fully before moving on.
3. **Sales** — Customer → Invoice → InvoiceItem (with formset) → transport utility → AJAX endpoints → Receivable → CustomerPayment
4. **Scheme** — SchemeCustomer → Deposit → Pickup → SchemeInvoice. Test the balance utility thoroughly with edge cases (reversals, cancellations).
5. **Dashboard** — reports and exports last, once all data models are stable and seeded.

---

## Setup & Installation

```bash
# Clone the repository
git clone https://github.com/Grace256c/nyondo-hardware-management-system.git
cd nyondo-hardware

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Seed categories (optional seed script)
python manage.py loaddata categories.json

# Run the development server
python manage.py runserver
```

**Dependencies (`requirements.txt`):**
```
Django>=4.2
openpyxl>=3.1
```

---

## GitHub Repository

https://github.com/Grace256c/nyondo-hardware-management-system.git

*Built as a final project for the Computer Science Engineering program.*
*NYONDO General Hardware LTD — Nansana, Uganda.*