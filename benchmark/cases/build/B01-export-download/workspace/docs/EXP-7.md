# EXP-7: Download a finished customer export

Tenant admins can already request a CSV export of their customers from the Exports page
(`request_export`). A background job builds the file and marks the export `done`.

When it's done, the Exports page shows a Download button. Implement
`download_export(store, user_id, export_id)` so it returns the CSV bytes for that export.

Out of scope: the page itself and the background job.
