-- ============================================================================
-- DATABASE MANAGEMENT SYSTEM (DBMS) PROJECT: PRODUCT MANAGEMENT SYSTEM
-- SCRIPT: views.sql (Analytical & Operational Views)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- VIEW 1: v_product_catalog
-- Purpose: Denormalized operational view joining Product, Category, and Supplier
-- Includes computed fields: profit margin, total inventory value, stock status
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_product_catalog;
CREATE VIEW v_product_catalog AS
SELECT
    p.product_id,
    p.sku,
    p.name AS product_name,
    p.description,
    c.category_id,
    c.name AS category_name,
    s.supplier_id,
    s.name AS supplier_name,
    p.unit_price,
    p.cost_price,
    ROUND(p.unit_price - p.cost_price, 2) AS unit_profit,
    CASE 
        WHEN p.unit_price > 0 
        THEN ROUND(((p.unit_price - p.cost_price) / p.unit_price) * 100.0, 2)
        ELSE 0.0 
    END AS profit_margin_pct,
    p.stock_quantity,
    p.reorder_level,
    p.unit_measure,
    ROUND(p.stock_quantity * p.unit_price, 2) AS inventory_retail_value,
    ROUND(p.stock_quantity * p.cost_price, 2) AS inventory_cost_value,
    p.status,
    CASE
        WHEN p.stock_quantity = 0 THEN 'OUT_OF_STOCK'
        WHEN p.stock_quantity <= p.reorder_level THEN 'LOW_STOCK'
        ELSE 'IN_STOCK'
    END AS stock_status,
    p.created_at,
    p.updated_at
FROM products p
INNER JOIN categories c ON p.category_id = c.category_id
INNER JOIN suppliers s ON p.supplier_id = s.supplier_id;

-- ----------------------------------------------------------------------------
-- VIEW 2: v_low_stock_alerts
-- Purpose: Immediate decision-support view highlighting products needing replenishment
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_low_stock_alerts;
CREATE VIEW v_low_stock_alerts AS
SELECT
    product_id,
    sku,
    product_name,
    category_name,
    supplier_name,
    stock_quantity,
    reorder_level,
    (reorder_level - stock_quantity) AS units_needed_for_reorder,
    unit_price,
    cost_price,
    stock_status
FROM v_product_catalog
WHERE stock_quantity <= reorder_level AND status = 'Active'
ORDER BY stock_quantity ASC;

-- ----------------------------------------------------------------------------
-- VIEW 3: v_category_analytics
-- Purpose: Executive summary of inventory distribution across product categories
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_category_analytics;
CREATE VIEW v_category_analytics AS
SELECT
    c.category_id,
    c.category_code,
    c.name AS category_name,
    COUNT(p.product_id) AS total_products,
    COALESCE(SUM(p.stock_quantity), 0) AS total_units_in_stock,
    ROUND(COALESCE(SUM(p.stock_quantity * p.unit_price), 0.0), 2) AS total_retail_value,
    ROUND(COALESCE(SUM(p.stock_quantity * p.cost_price), 0.0), 2) AS total_cost_value,
    ROUND(COALESCE(AVG(p.unit_price), 0.0), 2) AS avg_product_price
FROM categories c
LEFT JOIN products p ON c.category_id = p.category_id
GROUP BY c.category_id, c.category_code, c.name;

-- ----------------------------------------------------------------------------
-- VIEW 4: v_supplier_performance
-- Purpose: Evaluates supplier dependency, active product portfolio, and capital tied
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_supplier_performance;
CREATE VIEW v_supplier_performance AS
SELECT
    s.supplier_id,
    s.name AS supplier_name,
    s.contact_name,
    s.phone,
    s.city,
    COUNT(p.product_id) AS active_products_supplied,
    COALESCE(SUM(p.stock_quantity), 0) AS total_units_available,
    ROUND(COALESCE(SUM(p.stock_quantity * p.cost_price), 0.0), 2) AS capital_invested
FROM suppliers s
LEFT JOIN products p ON s.supplier_id = p.supplier_id AND p.status = 'Active'
GROUP BY s.supplier_id, s.name, s.contact_name, s.phone, s.city;

-- ----------------------------------------------------------------------------
-- VIEW 5: v_top_selling_products
-- Purpose: Sales performance analysis calculating volume, revenue, and gross profit
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_top_selling_products;
CREATE VIEW v_top_selling_products AS
SELECT
    p.product_id,
    p.sku,
    p.name AS product_name,
    c.name AS category_name,
    COALESCE(SUM(oi.quantity), 0) AS total_units_sold,
    ROUND(COALESCE(SUM(oi.subtotal), 0.0), 2) AS total_revenue,
    ROUND(COALESCE(SUM(oi.quantity * (oi.unit_price - p.cost_price)), 0.0), 2) AS gross_profit
FROM products p
INNER JOIN categories c ON p.category_id = c.category_id
LEFT JOIN order_items oi ON p.product_id = oi.product_id
LEFT JOIN orders o ON oi.order_id = o.order_id AND o.status != 'Cancelled'
GROUP BY p.product_id, p.sku, p.name, c.name
ORDER BY total_revenue DESC;

-- ----------------------------------------------------------------------------
-- VIEW 6: v_sales_orders_summary
-- Purpose: Joins orders with customer info and counts aggregated order items
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_sales_orders_summary;
CREATE VIEW v_sales_orders_summary AS
SELECT
    o.order_id,
    o.order_number,
    o.order_date,
    o.status,
    c.customer_id,
    c.name AS customer_name,
    c.email AS customer_email,
    c.city AS customer_city,
    COUNT(oi.order_item_id) AS total_line_items,
    COALESCE(SUM(oi.quantity), 0) AS total_units_purchased,
    o.subtotal,
    o.tax_amount,
    o.total_amount
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_id, o.order_number, o.order_date, o.status, c.customer_id, c.name, c.email, c.city, o.subtotal, o.tax_amount, o.total_amount
ORDER BY o.order_date DESC;
