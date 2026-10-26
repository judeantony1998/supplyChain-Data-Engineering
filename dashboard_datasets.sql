-- ============================================================
-- Supply Chain Command Center: dashboard datasets
-- All queries read from the Gold layer.
-- ============================================================

-- Dataset 1: executive KPIs (one row)
SELECT
  total_purchase_orders,
  active_vendors,
  currencies_in_use,
  avg_lead_time_days,
  avg_vendor_score,
  high_risk_vendors,
  total_inventory_value_usd,
  critical_stock_items,
  reorder_needed_items,
  on_time_delivery_pct,
  deliveries_pending,
  open_quality_issues,
  open_critical_issues
FROM capstone_supply_chain.gold_consolidated.supply_chain_kpi_snapshot;

-- Dataset 2: spend by vendor and currency (never add currencies together)
SELECT
  vendor_name,
  currency,
  po_count,
  ROUND(total_spend, 0) AS total_spend
FROM capstone_supply_chain.gold.agg_vendor_spend_by_currency
ORDER BY total_spend DESC;

-- Dataset 3: purchase order status distribution
SELECT
  status,
  COUNT(*) AS num_orders
FROM capstone_supply_chain.gold.fact_purchase_orders
GROUP BY status
ORDER BY num_orders DESC;

-- Dataset 4: vendor scorecard
SELECT
  vendor_name,
  country,
  category,
  on_time_delivery_pct,
  quality_grade,
  defect_rate_ppm,
  audit_score,
  risk_rating,
  composite_score,
  total_pos_current,
  currencies_used
FROM capstone_supply_chain.gold.agg_vendor_scorecard
ORDER BY composite_score DESC;


--Dataset 5: inventory_by_warehouse (4 rows expected)
SELECT
  warehouse_code,
  SUM(num_parts) AS num_parts,
  SUM(total_units) AS total_units,
  ROUND(SUM(total_inventory_value), 0) AS inventory_value,
  SUM(critical_items) AS critical_items,
  SUM(reorder_items) AS reorder_items,
  SUM(healthy_items) AS healthy_items
FROM capstone_supply_chain.gold.agg_inventory_health
GROUP BY warehouse_code
ORDER BY inventory_value DESC

--Dataset 6: inventory_by_abc (3 rows expected: A, B, C)
SELECT
  abc_class,
  SUM(num_parts) AS num_parts,
  ROUND(SUM(total_inventory_value), 0) AS inventory_value
FROM capstone_supply_chain.gold.agg_inventory_health
GROUP BY abc_class
ORDER BY abc_class

--Dataset 7: parts_lowest_cover (10 rows expected)
SELECT
  part_number,
  part_name,
  warehouse_code,
  current_stock,
  reorder_point,
  safety_stock,
  days_of_supply,
  stock_status
FROM capstone_supply_chain.silver.inventory
ORDER BY days_of_supply ASC
LIMIT 10

--Dataset 8: deliveries (10 rows expected)
SELECT
  delivery_id,
  po_id,
  vendor_name,
  scheduled_date_clean AS scheduled_date,
  actual_date_clean AS actual_date,
  days_early_late,
  delivery_status,
  dock_clean AS dock,
  fulfillment_pct
FROM capstone_supply_chain.silver.deliveries
ORDER BY delivery_id

--Dataset 9: open_quality_issues (3 rows expected)
SELECT
  q.inspection_id,
  q.po_id,
  po.vendor_name,
  q.part_number,
  q.inspection_date,
  q.defect_type,
  q.severity_clean AS severity,
  q.defect_rate_pct,
  q.customer_impact,
  q.corrective_action,
  q.cost_mentioned_usd
FROM capstone_supply_chain.silver.quality_inspections q
LEFT JOIN capstone_supply_chain.silver.purchase_orders po ON q.po_id = po.po_id
WHERE q.is_open
ORDER BY q.severity_rank DESC, q.defect_rate_pct DESC


Dataset 10: defects_by_category (one row per part category)
SELECT
  p.category,
  SUM(q.defects_found) AS defects_found,
  SUM(q.sample_size) AS units_inspected,
  ROUND(100.0 * SUM(q.defects_found) / SUM(q.sample_size), 1) AS defect_rate_pct
FROM capstone_supply_chain.silver.quality_inspections q
JOIN capstone_supply_chain.gold.dim_parts p ON q.part_number = p.part_number
GROUP BY p.category
ORDER BY defects_found DESC