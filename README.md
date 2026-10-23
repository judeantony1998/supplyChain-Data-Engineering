# SupplyChain-Data-Engineering
An End-to-End Supply Chain Data Engineering and AI Analytics Platform

## Progress

### Bronze layer (done)
- 11 raw Delta tables loaded from CSV, TSV, Excel (3 sheets), nested JSON, invoice text files, image metadata and maintenance logs.
- Every table has audit columns: `_ingested_at`, `_source_file` and `_file_format`.
- Raw data is stored unchanged; cleaning happens in the Silver layer.
- Note: invoices are simulated PDF text files, and image data is simulated metadata (no real image files).

### Next
- Silver layer: clean dates, remove duplicates, standardize values.
### After cleaning silver table 
The sample inventory has no parts below reorder level, so the stock-status rules were verified with synthetic test rows.

### Silver layer (in progress)
- 5 cleaned tables: purchase orders, vendors, inventory, deliveries, parsed invoices.
- Enforced types, snake_case names, deduplication, and standardized statuses and dock names.
- Handled mixed date formats and blank values in the delivery data.
- Parsed invoice text with regex, then validated results against purchase orders (invoice totals match PO line totals plus freight and packaging).
- Stock-status rules tested with synthetic rows, since the sample data had no low-stock parts.