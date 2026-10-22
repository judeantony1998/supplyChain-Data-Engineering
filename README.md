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
