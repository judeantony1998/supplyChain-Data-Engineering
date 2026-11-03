import os
import pandas as pd
import gradio as gr
from databricks import sql as dbsql
from databricks.sdk.core import Config

CATALOG = "capstone_supply_chain"
cfg = Config()  # reads the app's own credentials from environment variables


def run_query(query, params=None):
    """Run a SQL query on the warehouse and return a pandas DataFrame."""
    try:
        host = cfg.host.replace("https://", "").rstrip("/")
        with dbsql.connect(
            server_hostname=host,
            http_path=f"/sql/1.0/warehouses/{os.environ['DATABRICKS_WAREHOUSE_ID']}",
            credentials_provider=lambda: cfg.authenticate,
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                cols = [d[0] for d in cursor.description]
        return pd.DataFrame(rows, columns=cols)
    except Exception as e:
        # Show the problem in the app instead of crashing
        return pd.DataFrame({"error": [str(e)]})


def get_vendor_scorecard(risk):
    return run_query(f"""
        SELECT vendor_name, country, category, on_time_delivery_pct,
               quality_grade, defect_rate_ppm, risk_rating, composite_score
        FROM {CATALOG}.gold.agg_vendor_scorecard
        WHERE :risk = 'All' OR risk_rating = :risk
        ORDER BY composite_score DESC
    """, {"risk": risk})


def get_inventory_health():
    return run_query(f"""
        SELECT warehouse_code,
               SUM(num_parts) AS parts,
               SUM(total_units) AS units,
               ROUND(SUM(total_inventory_value), 0) AS inventory_value_usd,
               SUM(critical_items) AS critical_items,
               SUM(reorder_items) AS reorder_items,
               ROUND(100.0 * SUM(healthy_items) / SUM(num_parts), 1) AS healthy_pct
        FROM {CATALOG}.gold.agg_inventory_health
        GROUP BY warehouse_code
        ORDER BY warehouse_code
    """)


def get_po_by_status(status):
    return run_query(f"""
        SELECT po_id, vendor_name, part_description, order_qty,
               ROUND(line_total, 2) AS line_total, currency, status, plant_name
        FROM {CATALOG}.gold.fact_purchase_orders
        WHERE status = :status
        ORDER BY currency, line_total DESC
    """, {"status": status})


def get_spend_by_currency():
    return run_query(f"""
        SELECT currency,
               COUNT(DISTINCT vendor_id) AS vendors,
               SUM(po_count) AS purchase_orders,
               ROUND(SUM(total_spend), 0) AS total_spend
        FROM {CATALOG}.gold.agg_vendor_spend_by_currency
        GROUP BY currency
        ORDER BY currency
    """)


with gr.Blocks(title="Supply Chain Operations Portal", theme=gr.themes.Soft()) as app:
    gr.Markdown("# Supply Chain Operations Portal")
    gr.Markdown("Supply chain analytics on the Gold layer. Amounts in different currencies are never added together.")

    with gr.Tab("Vendor Scorecard"):
        risk_dd = gr.Dropdown(choices=["All", "Low", "Medium", "High"], value="All", label="Filter by risk rating")
        btn_vendor = gr.Button("Load vendor scorecard")
        vendor_table = gr.Dataframe()
        btn_vendor.click(fn=get_vendor_scorecard, inputs=risk_dd, outputs=vendor_table)

    with gr.Tab("Inventory Health"):
        btn_inv = gr.Button("Load inventory health by warehouse")
        inv_table = gr.Dataframe()
        btn_inv.click(fn=get_inventory_health, outputs=inv_table)

    with gr.Tab("Purchase Orders"):
        status_dd = gr.Dropdown(
            choices=["Delivered", "In Transit", "Pending Approval", "Confirmed", "In Production", "Quality Hold"],
            value="Quality Hold", label="Filter by status")
        btn_po = gr.Button("Search")
        po_table = gr.Dataframe()
        btn_po.click(fn=get_po_by_status, inputs=status_dd, outputs=po_table)

    with gr.Tab("Spend by Currency"):
        btn_spend = gr.Button("Load spend by currency")
        spend_table = gr.Dataframe()
        btn_spend.click(fn=get_spend_by_currency, outputs=spend_table)

if __name__ == "__main__":
    port = int(os.getenv("DATABRICKS_APP_PORT", "8000"))
    app.launch(server_name="0.0.0.0", server_port=port)