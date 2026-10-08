-- ============================================================================
-- DATABASE MANAGEMENT SYSTEM (DBMS) PROJECT: PRODUCT MANAGEMENT SYSTEM
-- SCRIPT: complex_queries.sql (20 Essential DBMS Lab & Analytical Queries)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- QUERY 1: Multi-Table INNER JOIN (3 Tables)
-- Retrieve product details along with their category name and supplier contact info
-- ----------------------------------------------------------------------------
SELECT 
    p.product_id,
    p.sku,
    p.name AS product_name,
    c.name AS category_name,
    s.name AS supplier_name,
    s.contact_name,
    s.phone AS supplier_phone,
    p.unit_price,
    p.stock_quantity
FROM products p
INNER JOIN categories c ON p.category_id = c.category_id
INNER JOIN suppliers s ON p.supplier_id = s.supplier_id
WHERE p.status = 'Active'
ORDER BY c.name, p.unit_price DESC;

-- ----------------------------------------------------------------------------
-- QUERY 2: LEFT OUTER JOIN with NULL checking
-- Find suppliers who currently have zero active products in the system
-- ----------------------------------------------------------------------------
SELECT 
    s.supplier_id,
    s.name AS supplier_name,
    s.email,
    s.city
FROM suppliers s
LEFT JOIN products p ON s.supplier_id = p.supplier_id AND p.status = 'Active'
WHERE p.product_id IS NULL;

-- ----------------------------------------------------------------------------
-- QUERY 3: Aggregation with GROUP BY and HAVING
-- Identify categories having total retail stock inventory value exceeding ₹50,000
-- ----------------------------------------------------------------------------
SELECT 
    c.category_id,
    c.name AS category_name,
    COUNT(p.product_id) AS total_products,
    SUM(p.stock_quantity) AS total_units,
    ROUND(SUM(p.stock_quantity * p.unit_price), 2) AS total_retail_value
FROM categories c
INNER JOIN products p ON c.category_id = p.category_id
GROUP BY c.category_id, c.name
HAVING SUM(p.stock_quantity * p.unit_price) > 50000.00
ORDER BY total_retail_value DESC;

-- ----------------------------------------------------------------------------
-- QUERY 4: Correlated Subquery
-- Find all products whose unit price is higher than the average price in their category
-- ----------------------------------------------------------------------------
SELECT 
    p.product_id,
    p.sku,
    p.name AS product_name,
    p.category_id,
    p.unit_price,
    ROUND((
        SELECT AVG(p2.unit_price)
        FROM products p2
        WHERE p2.category_id = p.category_id
    ), 2) AS category_avg_price
FROM products p
WHERE p.unit_price > (
    SELECT AVG(p2.unit_price)
    FROM products p2
    WHERE p2.category_id = p.category_id
)
ORDER BY p.category_id, p.unit_price DESC;

-- ----------------------------------------------------------------------------
-- QUERY 5: Subquery with IN Operator
-- Find all customers who have placed at least one completed order
-- ----------------------------------------------------------------------------
SELECT 
    customer_id,
    name,
    email,
    city
FROM customers
WHERE customer_id IN (
    SELECT DISTINCT customer_id 
    FROM orders 
    WHERE status = 'Completed'
);

-- ----------------------------------------------------------------------------
-- QUERY 6: Subquery with NOT EXISTS Operator
-- Find customers who have registered but never placed any order
-- ----------------------------------------------------------------------------
SELECT 
    c.customer_id,
    c.name,
    c.email,
    c.city
FROM customers c
WHERE NOT EXISTS (
    SELECT 1 
    FROM orders o 
    WHERE o.customer_id = c.customer_id
);

-- ----------------------------------------------------------------------------
-- QUERY 7: Window Function: DENSE_RANK()
-- Rank products within each category by their unit price (highest to lowest)
-- ----------------------------------------------------------------------------
SELECT 
    c.name AS category_name,
    p.name AS product_name,
    p.unit_price,
    DENSE_RANK() OVER (
        PARTITION BY p.category_id 
        ORDER BY p.unit_price DESC
    ) AS price_rank_in_category
FROM products p
INNER JOIN categories c ON p.category_id = c.category_id
ORDER BY c.name, price_rank_in_category;

-- ----------------------------------------------------------------------------
-- QUERY 8: Window Function: Running Total with SUM() OVER()
-- Calculate cumulative sales revenue chronologically across orders
-- ----------------------------------------------------------------------------
SELECT 
    order_id,
    order_number,
    order_date,
    total_amount,
    ROUND(SUM(total_amount) OVER (
        ORDER BY order_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2) AS running_total_revenue
FROM orders
WHERE status != 'Cancelled'
ORDER BY order_date ASC;

-- ----------------------------------------------------------------------------
-- QUERY 9: Multi-Table 4-Way JOIN (Orders, Customers, Order Items, Products)
-- Complete itemized sales ledger with margin calculation
-- ----------------------------------------------------------------------------
SELECT 
    o.order_number,
    o.order_date,
    c.name AS customer_name,
    p.name AS product_name,
    oi.quantity,
    oi.unit_price AS selling_price,
    p.cost_price,
    ROUND((oi.unit_price - p.cost_price) * oi.quantity, 2) AS profit_made,
    oi.subtotal
FROM order_items oi
INNER JOIN orders o ON oi.order_id = o.order_id
INNER JOIN customers c ON o.customer_id = c.customer_id
INNER JOIN products p ON oi.product_id = p.product_id
ORDER BY o.order_date DESC, oi.order_item_id;

-- ----------------------------------------------------------------------------
-- QUERY 10: Set Operations: UNION & EXCEPT
-- Compare products that have been sold vs products in inventory
-- ----------------------------------------------------------------------------
-- Products that have NEVER been sold:
SELECT product_id, sku, name FROM products
EXCEPT
SELECT p.product_id, p.sku, p.name 
FROM products p 
INNER JOIN order_items oi ON p.product_id = oi.product_id;

-- ----------------------------------------------------------------------------
-- QUERY 11: Stock Health Classification using CASE Statement
-- Categorize products into business action urgency levels
-- ----------------------------------------------------------------------------
SELECT 
    product_id,
    sku,
    name,
    stock_quantity,
    reorder_level,
    CASE
        WHEN stock_quantity = 0 THEN 'CRITICAL: Out of Stock'
        WHEN stock_quantity < (reorder_level / 2) THEN 'HIGH ALERT: Severe Shortage'
        WHEN stock_quantity <= reorder_level THEN 'WARNING: Below Reorder Level'
        ELSE 'HEALTHY: Sufficient Stock'
    END AS stock_health_status
FROM products
ORDER BY stock_quantity ASC;

-- ----------------------------------------------------------------------------
-- QUERY 12: Aggregate with Filter (Percentage Contribution)
-- Find the percentage contribution of each supplier to total inventory value
-- ----------------------------------------------------------------------------
SELECT 
    s.name AS supplier_name,
    COUNT(p.product_id) AS product_count,
    ROUND(SUM(p.stock_quantity * p.cost_price), 2) AS supplier_inventory_cost,
    ROUND(
        (SUM(p.stock_quantity * p.cost_price) * 100.0) / 
        (SELECT SUM(stock_quantity * cost_price) FROM products), 
        2
    ) AS inventory_value_share_pct
FROM suppliers s
INNER JOIN products p ON s.supplier_id = p.supplier_id
GROUP BY s.supplier_id, s.name
ORDER BY supplier_inventory_cost DESC;

-- ----------------------------------------------------------------------------
-- QUERY 13: View Querying
-- Query the low stock alerts view with financial reorder cost estimation
-- ----------------------------------------------------------------------------
SELECT 
    sku,
    product_name,
    category_name,
    stock_quantity,
    reorder_level,
    units_needed_for_reorder,
    cost_price,
    ROUND(units_needed_for_reorder * cost_price, 2) AS estimated_procurement_cost
FROM v_low_stock_alerts;

-- ----------------------------------------------------------------------------
-- QUERY 14: Top 3 Revenue-Generating Products
-- Using LIMIT and Subquery logic
-- ----------------------------------------------------------------------------
SELECT 
    product_name,
    category_name,
    total_units_sold,
    total_revenue,
    gross_profit
FROM v_top_selling_products
ORDER BY total_revenue DESC
LIMIT 3;

-- ----------------------------------------------------------------------------
-- QUERY 15: Auditing Query (Data Provenance)
-- View historical price adjustments and stock modifications
-- ----------------------------------------------------------------------------
SELECT 
    pal.audit_id,
    p.sku,
    p.name AS product_name,
    pal.action_type,
    pal.old_values,
    pal.new_values,
    pal.changed_by,
    pal.timestamp
FROM product_audit_log pal
INNER JOIN products p ON pal.product_id = p.product_id
ORDER BY pal.timestamp DESC;

-- ----------------------------------------------------------------------------
-- QUERY 16: Inventory Turnover Analysis
-- Ratio of units sold compared to current stock available
-- ----------------------------------------------------------------------------
SELECT 
    p.sku,
    p.name,
    COALESCE(SUM(oi.quantity), 0) AS units_sold,
    p.stock_quantity AS current_stock,
    ROUND(
        CAST(COALESCE(SUM(oi.quantity), 0) AS REAL) / 
        NULLIF((p.stock_quantity + COALESCE(SUM(oi.quantity), 0)), 0),
        2
    ) AS sales_velocity_ratio
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.sku, p.name, p.stock_quantity
ORDER BY units_sold DESC;

-- ----------------------------------------------------------------------------
-- QUERY 17: Date-Truncated Sales Trend (Monthly Aggregation)
-- Group orders by Year-Month to assess revenue growth
-- ----------------------------------------------------------------------------
SELECT 
    strftime('%Y-%m', order_date) AS sales_month,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(total_amount) AS monthly_revenue,
    ROUND(AVG(total_amount), 2) AS average_order_value
FROM orders
WHERE status != 'Cancelled'
GROUP BY strftime('%Y-%m', order_date)
ORDER BY sales_month ASC;

-- ----------------------------------------------------------------------------
-- QUERY 18: Multiple Condition Search (Filter query)
-- Search products with price between 1000 and 10000 with high profit margin (>30%)
-- ----------------------------------------------------------------------------
SELECT 
    product_id,
    sku,
    product_name,
    category_name,
    unit_price,
    cost_price,
    profit_margin_pct
FROM v_product_catalog
WHERE unit_price BETWEEN 1000.00 AND 10000.00
  AND profit_margin_pct >= 30.00
ORDER BY profit_margin_pct DESC;

-- ----------------------------------------------------------------------------
-- QUERY 19: Customers with Highest Lifetime Value (LTV)
-- ----------------------------------------------------------------------------
SELECT 
    c.customer_id,
    c.name AS customer_name,
    c.email,
    c.city,
    COUNT(o.order_id) AS total_orders_placed,
    ROUND(SUM(o.total_amount), 2) AS total_lifetime_spend
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status != 'Cancelled'
GROUP BY c.customer_id, c.name, c.email, c.city
ORDER BY total_lifetime_spend DESC;

-- ----------------------------------------------------------------------------
-- QUERY 20: ACID Transaction Demonstration (Simulated Order Creation)
-- Demonstrates Atomicity, Consistency, Isolation, and Durability
-- ----------------------------------------------------------------------------
BEGIN TRANSACTION;

-- Step 1: Insert new order header
INSERT INTO orders (order_number, customer_id, status, subtotal, tax_amount, total_amount, notes)
VALUES ('ORD-TEST-999', 1, 'Completed', 1499.00, 269.82, 1768.82, 'ACID Transaction Test Order');

-- Step 2: Insert order item (Database trigger trg_order_item_deduct_stock will auto-deduct stock!)
INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
VALUES (last_insert_rowid(), 1, 1, 1499.00, 1499.00);

-- Step 3: Commit transaction to permanently save state
COMMIT;
