# Academic DBMS Project Report: Product Management System

## 1. Project Abstract
The **Product Management System (PMS)** is a comprehensive, production-grade Database Management System (DBMS) designed to manage products, categories, suppliers, inventory stock movements, sales transactions, and audit provenance. Built adhering to strict relational algebra principles, the database schema is normalized up to **Boyce-Codd Normal Form (BCNF)** and enforces **Entity Integrity**, **Domain Constraints**, and **Referential Integrity** with foreign key cascading and restriction rules. The system integrates automated **Database Triggers**, **Analytical Views**, **B-Tree Indexes**, and **ACID Transactions** for atomic order processing. A modern Python/Flask web dashboard accompanies the relational database to provide an interactive graphical interface, a live SQL playground, and an ER schema visualizer.

---

## 2. Problem Statement & Objectives
In traditional enterprise and retail environments, unstructured or flat-file product management leads to severe anomalies:
- **Redundant Data Storage:** Duplicate vendor contact details and category specifications.
- **Inconsistent Inventory Counts:** Mismatches between orders placed and stock remaining.
- **Lack of Auditability:** Inability to identify who modified product pricing or when stock discrepancies arose.
- **Race Conditions:** Selling products that are already out of stock during concurrent checkouts.

### Objectives:
1. Design an Entity-Relationship (ER) model and normalize relations to eliminate insertion, update, and deletion anomalies.
2. Implement declarative constraints (`CHECK`, `UNIQUE`, `NOT NULL`, `FOREIGN KEY`).
3. Develop reactive database triggers to automate stock adjustments and log audit trails.
4. Construct analytical SQL views to supply real-time business intelligence metrics.
5. Provide ACID transaction handling for order processing with guaranteed rollbacks on failure.
6. Build an interactive web console for query execution, visual schema inspection, and catalog management.

---

## 3. Database Architecture & Schema Specification

### 3.1 Relational Schema Summary
- **`categories`** (`category_id` [PK], `category_code` [UK], `name` [UK], `description`, `created_at`)
- **`suppliers`** (`supplier_id` [PK], `name` [UK], `contact_name`, `email` [UK], `phone`, `address`, `city`, `country`, `created_at`)
- **`products`** (`product_id` [PK], `sku` [UK], `name`, `description`, `category_id` [FK], `supplier_id` [FK], `unit_price`, `cost_price`, `stock_quantity`, `reorder_level`, `unit_measure`, `status`, `created_at`, `updated_at`)
- **`customers`** (`customer_id` [PK], `name`, `email` [UK], `phone`, `address`, `city`, `created_at`)
- **`orders`** (`order_id` [PK], `order_number` [UK], `customer_id` [FK], `order_date`, `status`, `subtotal`, `tax_amount`, `total_amount`, `notes`)
- **`order_items`** (`order_item_id` [PK], `order_id` [FK], `product_id` [FK], `quantity`, `unit_price`, `subtotal`)
- **`inventory_transactions`** (`transaction_id` [PK], `product_id` [FK], `transaction_type`, `quantity`, `unit_cost`, `reference_note`, `created_at`)
- **`product_audit_log`** (`audit_id` [PK], `product_id`, `action_type`, `old_values`, `new_values`, `changed_by`, `timestamp`)

---

## 4. Normalization Analysis

### 4.1 First Normal Form (1NF)
- **Criterion:** All attribute values must be atomic; no repeating groups or comma-separated lists.
- **Application:** Instead of listing multiple products in an order row, the relationship is decomposed into individual rows in the `order_items` relation.

### 4.2 Second Normal Form (2NF)
- **Criterion:** Relation must be in 1NF, and all non-prime attributes must be fully functionally dependent on the primary key (no partial functional dependency).
- **Application:** In `order_items`, the composite attributes are identified by `order_item_id`. Unit price and quantity depend strictly on the line item, while customer attributes depend strictly on `customer_id` in `customers`.

### 4.3 Third Normal Form (3NF)
- **Criterion:** Relation must be in 2NF, and no non-prime attribute should be transitively dependent on the primary key ($X \to Y$ and $Y \to Z$ where $Z$ is non-prime).
- **Application:** In `products`, supplier contact information and location are not duplicated; only `supplier_id` is retained as a foreign key. The supplier's phone, email, and address reside in `suppliers`.

### 4.4 Boyce-Codd Normal Form (BCNF)
- **Criterion:** For every functional dependency $X \to Y$, $X$ must be a super key.
- **Application:** In `products`, functional dependencies are:
  - `product_id` $\to$ `{sku, name, category_id, supplier_id, unit_price, ...}`
  - `sku` $\to$ `{product_id, name, category_id, supplier_id, unit_price, ...}`
  Both `product_id` and `sku` are candidate keys; hence, every determinant is a super key.

---

## 5. DBMS Triggers Implementation

1. **`trg_prevent_negative_stock` (Integrity Guard):**
   Fires `BEFORE UPDATE` on `products`. If `NEW.stock_quantity < 0`, issues `SELECT RAISE(ABORT, 'DBMS Error: Stock quantity cannot be negative.')`.
2. **`trg_order_item_deduct_stock` (Stock Sync & Ledger):**
   Fires `AFTER INSERT` on `order_items`. Automatically updates `products.stock_quantity = stock_quantity - NEW.quantity` and records a corresponding row in `inventory_transactions`.
3. **`trg_order_cancelled_restore_stock` (Order Cancellation Reversal):**
   Fires `AFTER UPDATE OF status` on `orders` when transitioned to `'Cancelled'`. Re-adds item quantities back to `products` and records `'RETURN_IN'` transactions.
4. **`trg_product_audit_update` & `trg_product_audit_insert` (Data Provenance):**
   Captures modification deltas as structured JSON into `product_audit_log` detailing old vs new values.

---

## 6. Analytical SQL Views

- **`v_product_catalog`:** Joins `products`, `categories`, and `suppliers` to calculate gross profit margin percentage and stock status (`IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`).
- **`v_low_stock_alerts`:** Filters products where `stock_quantity <= reorder_level`, calculating exact units required for replenishment and cost estimation.
- **`v_category_analytics`:** Aggregates product counts, total physical units, and total inventory retail value grouped by category.
- **`v_supplier_performance`:** Aggregates active product portfolio and capital invested per supplier.
- **`v_top_selling_products`:** Computes total units sold, gross sales revenue, and net profit per product.
- **`v_sales_orders_summary`:** Itemized summary joining orders with customers and counting line items.

---

## 7. ACID Transaction Demonstration
Order processing is handled through explicit transactional control:
```sql
BEGIN TRANSACTION;
-- 1. Insert into orders header
-- 2. Insert into order_items (Triggers deduct stock)
-- If stock < requested_qty, trigger or application raises exception:
-- ROLLBACK TRANSACTION;
-- If all checks pass:
COMMIT;
```
This guarantees that inventory is never decremented without a recorded order, and no payment is accepted for unfulfillable items.

---

## 8. Conclusion
The Product Management System successfully fulfills all academic and practical requirements of an advanced DBMS project. By combining rigorous relational schema design, 3NF normalization, active database triggers, comprehensive analytical views, and an intuitive web interface, the project serves as a complete showcase of relational database capabilities.
