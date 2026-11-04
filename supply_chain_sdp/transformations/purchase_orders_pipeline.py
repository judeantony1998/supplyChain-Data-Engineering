import dlt
from pyspark.sql import functions as F

LANDING = "/Volumes/capstone_supply_chain/bronze/landing_csv/"


# BRONZE: a streaming table. Auto Loader remembers which files it has read,
# so each run only picks up NEW files.
@dlt.table(
    name="bronze_purchase_orders",
    comment="Raw purchase orders loaded incrementally from CSV files with Auto Loader",
)
def bronze_purchase_orders():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("pathGlobFilter", "purchase_orders*.csv")   # ignore delivery_schedule.csv
        .load(LANDING)
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source_file", F.col("_metadata.file_path"))
    )


# SILVER: cleaned, with data quality rules ("expectations")
@dlt.table(
    name="silver_purchase_orders",
    comment="Cleaned purchase orders. Rows that break a drop rule are removed and counted.",
)
@dlt.expect_or_drop("valid_po_id", "po_id IS NOT NULL")
@dlt.expect_or_drop("valid_unit_price", "unit_price > 0")
@dlt.expect_or_drop("valid_order_qty", "order_qty > 0")
@dlt.expect("valid_order_date", "order_date IS NOT NULL")      # only counts, keeps the row
def silver_purchase_orders():
    return (
        spark.read.table("bronze_purchase_orders")
        .select(
            F.col("PO_ID").alias("po_id"),
            F.col("Vendor_ID").alias("vendor_id"),
            F.col("Vendor_Name").alias("vendor_name"),
            F.col("Part_Number").alias("part_number"),
            F.expr("try_cast(Order_Qty AS INT)").alias("order_qty"),
            F.expr("try_cast(Unit_Price AS DOUBLE)").alias("unit_price"),
            F.col("Currency").alias("currency"),
            F.expr("try_cast(Order_Date AS DATE)").alias("order_date"),
            F.expr("try_cast(Expected_Delivery AS DATE)").alias("expected_delivery"),
            F.col("Plant_Code").alias("plant_code"),
            F.col("Status").alias("status"),
        )
        .withColumn("line_total", F.col("order_qty") * F.col("unit_price"))
        .withColumn("lead_time_days", F.datediff("expected_delivery", "order_date"))
        .dropDuplicates(["po_id"])
    )


# GOLD: spend per vendor and currency (currencies are never added together)
@dlt.table(
    name="gold_vendor_spend_by_currency",
    comment="Total purchase order spend per vendor and per currency.",
)
def gold_vendor_spend_by_currency():
    return (
        spark.read.table("silver_purchase_orders")
        .groupBy("vendor_id", "vendor_name", "currency")
        .agg(
            F.count("po_id").alias("po_count"),
            F.round(F.sum("line_total"), 2).alias("total_spend"),
        )
    )