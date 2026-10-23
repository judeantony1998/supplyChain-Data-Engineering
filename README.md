# SupplyChain-Data-Engineering
An End-to-End Supply Chain Data Engineering and AI Analytics Platform

## Progress

### Architecture
Medallion architecture on Databricks (Unity Catalog, Delta tables): raw files land in Volumes, then Bronze, Silver and Gold tables.

### Bronze layer (done)
- 11 raw Delta tables from CSV, TSV, Excel (3 sheets), nested JSON, invoice text files, image metadata and maintenance logs.
- Every table has audit columns (`_ingested_at`, `_source_file`, `_file_format`). Raw data is kept unchanged.
- Invoices are simulated PDF text files, and the image table is simulated metadata (no real image files).

### Silver layer (7 tables)
- Cleaned: purchase orders, vendors, inventory, deliveries, plants, quality inspections.
- Parsed with regex: invoice text turned into columns (invoice number, date, PO, vendor, total, currency, terms).
- Enforced types, snake_case names, deduplication and standardized values.
- Handled messy delivery data: mixed date formats, inconsistent dock names, blank values.
- Added business rules: stock status, defect rate, severity rank, open/closed and customer-impact flags.
- Checks: row counts, null checks, key uniqueness, and links to purchase orders.

### Gold layer (in progress)
- Dimensions: `dim_vendors`, `dim_parts`, `dim_plants` (keys unique, no orphan references).
- Fact: `fact_purchase_orders`, enriched with vendor and plant attributes.
- Aggregates: vendor scorecard (weighted composite score), inventory health, and vendor spend by currency.
- The data contains 5 currencies, so spend is kept per currency and never added across them. Totals are reconciled against Silver.

### Data quality findings
- Delivery DEL-003 was received with no receiver recorded.
- Ambiguous date format (`06/10/2026`) resolved as month-first, using the surrounding dates.
- Sample inventory has no low-stock parts, so stock-status rules were tested with synthetic rows.
- The vendor scorecard does not yet use inspection results (a vendor with an open critical issue still ranks high).

### Next
- KPI snapshot table, shipments (nested JSON) cleaning, dashboard, Genie, job scheduling, CI/CD.