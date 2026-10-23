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