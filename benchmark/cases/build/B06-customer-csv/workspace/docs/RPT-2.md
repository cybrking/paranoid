# RPT-2: Export customers to CSV

Account admins want to open their customer list in Excel. Add an "Export to CSV" button on the
Customers page.

Implement `customers_csv(store, user_id, account_id)` in `app/reports.py`. Columns:
`name,email,signup_source,total_spent`. Customers sign up through our public form, so
`name` and `signup_source` are whatever they typed.
