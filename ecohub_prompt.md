You are helping me build "Ecohub" — a simple, modern inventory and sales management
system for a small electronics shop. Build it with Django and MySQL.

## What the system does
- Manages products and stock levels
- Creates quotations and invoices for customers
- Generates printable invoices, quotations and receipts (PDF)
- Supports normal catalog sales AND ad-hoc sales: a cashier can sell an item that
  is NOT in the product catalog by typing a description, quantity and price on the
  spot. That sale still gets recorded, appears on the receipt, and counts in reports
  — it just isn't linked to a Product and doesn't touch stock.
- Has a dashboard and reports (sales trends, top products, low stock, outstanding
  invoices, ad-hoc sales).
- Has multiple user roles: Admin (full access, manages products/users/reports) and
  Cashier/Sales staff (can create quotations, sales/invoices, receipts, and view
  stock, but not manage users or see full financial reports).

## Data model to implement
- Product: name, sku, category, cost_price, selling_price, quantity_in_stock,
  reorder_level, is_active
- StockMovement: product (FK), type (stock_in / sale / adjustment), quantity,
  reference, created_by, created_at — every stock change must go through this,
  never edit quantity_in_stock directly
- Customer: name, phone, email, address (all optional except name; walk-in sales
  allowed with no customer)
- Document: doc_type (quotation/invoice), doc_number (auto e.g. QT-0001/INV-0001),
  customer (FK, nullable), status, issue_date, due_date, subtotal, discount, tax,
  total, converted_from (self-FK for quotation→invoice), created_by
- DocumentItem: document (FK), product (FK, NULLABLE — null means ad-hoc item),
  description, quantity, unit_price, line_total
- Payment: invoice (FK), amount, method, paid_at, received_by
- Receipt: invoice (FK, one-to-one), receipt_number, issued_at, issued_by
- User: Django auth user extended with a role field (Admin / Cashier)

## Suggested app layout
ecohub/
├── config/          settings, urls
├── inventory/       Product, StockMovement, categories
├── customers/       Customer
├── sales/           Document, DocumentItem, Payment, Receipt
├── reports/         report views, exports
├── accounts/        custom User, roles, permissions
├── templates/       base + print templates (invoice.html, quotation.html, receipt.html)
└── static/

## Dashboard requirements (admin)
Build a clean, modern admin dashboard (use Tailwind CSS for styling) with:
- Summary cards: today's sales total, today's transaction count, low-stock count,
  outstanding invoices total
- A 7/30-day sales trend chart (Chart.js)
- Recent sales table (last 10, with a link to each document)
- Quick links to: new sale, new quotation, add product, stock-in
- Role-aware: Admin sees full financial figures; Cashier's dashboard/home shows
  only their own recent sales and a simplified quick-actions view, no revenue totals

## PDF generation
Use WeasyPrint to render invoice/quotation/receipt as PDF from an HTML template,
sharing one base layout with shop name/logo and differing footer text per document
type. Add "Print" and "Download PDF" buttons on each document's detail page.

## Build order — please work through these phases one at a time, and check in with
me before moving to the next phase:

1. Project scaffold: Django project + apps above, MySQL connection via .env,
   custom User model with role field, base template with Tailwind.
2. Auth: login/logout, role-based access control (Admin vs Cashier), a simple
   Admin-only user management screen (create/deactivate staff accounts).
3. Inventory: Product CRUD, categories, stock-in form, StockMovement audit trail,
   low-stock indicator.
4. Customers: simple CRUD, searchable list.
5. Sales/Documents: build the quotation/invoice creation flow — line item entry
   supporting BOTH catalog product search-and-add AND a "custom item" add (ad-hoc,
   no product link), running totals, discount/tax, save as draft.
6. Quotation → Invoice conversion, invoice payment recording (partial/full),
   auto-generated Receipt once fully paid.
7. PDF templates and print/download for invoice, quotation, receipt.
8. Dashboard (as specified above) and Reports module (sales summary, top products,
   ad-hoc sales report, stock valuation, outstanding invoices — with CSV export).
9. Polish: search/filtering, pagination, form validation, empty states, seed data
   script for demo purposes.

For each phase: propose the models/migrations or views first, wait for my go-ahead
if something is ambiguous, then implement. Keep the code simple and readable —
this is a small single-shop system, not a multi-tenant platform, so avoid
over-engineering it.

Let's start with Phase 1.
