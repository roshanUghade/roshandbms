# Top 30 DBMS Viva Questions & Answers
### Specially Prepared for the Product Management System DBMS Project

---

### Q1: What is a Database Management System (DBMS), and why use a Relational DBMS (RDBMS) for this project?
**Answer:**
A DBMS is system software for creating, managing, and querying databases. An RDBMS stores data in structured tables (relations) consisting of rows and columns, enforcing mathematical relational algebra principles. In this Product Management System, an RDBMS ensures **data integrity**, **elimination of data redundancy** via normalization, **ACID transaction guarantees**, and efficient retrieval via **indexes and joins**.

---

### Q2: What are the ACID properties, and how does your project demonstrate them?
**Answer:**
- **A – Atomicity:** All-or-nothing execution. In our `order_create` function, inserting into `orders`, inserting into `order_items`, and reducing product stock must all succeed together. If any item is out of stock, the entire transaction issues a `ROLLBACK`.
- **C – Consistency:** The database transitions only between valid states satisfying all constraints (e.g., `stock_quantity >= 0`, foreign keys).
- **I – Isolation:** Transactions execute concurrently without interfering with each other's intermediate uncommitted states.
- **D – Durability:** Once committed via `COMMIT`, changes are permanently written to persistent storage even in the event of a system crash.

---

### Q3: What is Normalization? Explain how your schema achieves 3NF and BCNF.
**Answer:**
Normalization is the systematic process of organizing database tables to eliminate data redundancy and prevent insert, update, and delete anomalies.
- **1NF (First Normal Form):** All column attributes contain atomic (indivisible) values, and each record is identified by a primary key. (e.g., no multi-valued comma-separated lists of products).
- **2NF (Second Normal Form):** Satisfies 1NF, and all non-key attributes are fully functionally dependent on the entire primary key (no partial dependency). (e.g., in `order_items`, attributes depend on `order_item_id`).
- **3NF (Third Normal Form):** Satisfies 2NF, and no non-key attribute is transitively dependent on the primary key ($X \to Y$ and $Y \to Z$). For example, supplier contact details are kept in `suppliers`, not duplicated inside `products`.
- **BCNF (Boyce-Codd Normal Form):** For every functional dependency $X \to Y$, $X$ must be a super key. In our `products` table, dependencies are determined solely by candidate keys `product_id` and `sku`.

---

### Q4: What is the difference between a Primary Key and a Unique Key?
**Answer:**
- A **Primary Key (PK)** uniquely identifies each row in a relation, cannot accept `NULL` values, and each table can have only one primary key. (e.g., `product_id`).
- A **Unique Key (UK)** also enforces uniqueness across column values, but can accept `NULL` values (depending on SQL dialect), and a table can have multiple unique keys. (e.g., `sku` in `products`, `email` in `suppliers`).

---

### Q5: What is a Foreign Key, and what referential integrity actions did you configure?
**Answer:**
A Foreign Key is a field in one table that uniquely identifies a row in another table (referencing that table's primary key).
In this project:
- `ON DELETE RESTRICT`: Used on `categories(category_id)` and `suppliers(supplier_id)` referenced by `products`. Prevents deleting a category or supplier if products are still mapped to it.
- `ON DELETE CASCADE`: Used on `orders(order_id)` referenced by `order_items`. If an order is deleted, its child line items are automatically cleaned up.

---

### Q6: What is a Database Trigger? What triggers exist in this project?
**Answer:**
A trigger is a set of SQL statements automatically executed (fired) by the database engine in response to specific DML events (`INSERT`, `UPDATE`, `DELETE`) on a specified table.
Our project implements:
1. `trg_prevent_negative_stock`: `BEFORE UPDATE` trigger that raises an `ABORT` error if `stock_quantity < 0`.
2. `trg_order_item_deduct_stock`: `AFTER INSERT` trigger on `order_items` that automatically subtracts stock from `products` and creates a ledger entry in `inventory_transactions`.
3. `trg_order_cancelled_restore_stock`: `AFTER UPDATE` trigger on `orders` that restores product stock when status changes to 'Cancelled'.
4. `trg_product_audit_insert` & `trg_product_audit_update`: Captures old and new attribute values in JSON format into `product_audit_log`.

---

### Q7: What is a Database View, and why use them?
**Answer:**
A View is a virtual relation defined by a stored SQL `SELECT` query. It does not store physical data itself (unless materialized) but computes results dynamically upon being queried.
**Benefits:**
- Simplifies complex multi-table joins for application queries.
- Enhances data security by exposing only authorized subsets of columns.
- Provides abstraction and logical data independence.
**Views in our project:** `v_product_catalog`, `v_low_stock_alerts`, `v_top_selling_products`, `v_category_analytics`, `v_supplier_performance`, and `v_sales_orders_summary`.

---

### Q8: What is an Index, and which columns are indexed in your schema?
**Answer:**
An index is a database data structure (typically a B-Tree or B+ Tree) that accelerates data retrieval queries without having to perform full table scans (`O(N)` reduced to `O(log N)`).
Indexed columns in our project:
- `products(sku)` – For fast barcode/SKU searches.
- `products(category_id)` and `products(supplier_id)` – For high-performance foreign key joins.
- `products(stock_quantity, reorder_level)` – For instantaneous low-stock alert evaluation.
- `orders(customer_id, order_date)` – For customer history sorting and date range queries.

---

### Q9: What is the difference between `WHERE` and `HAVING` clauses?
**Answer:**
- `WHERE` filters individual rows **before** any aggregation (`GROUP BY`) is performed.
- `HAVING` filters aggregated groups **after** the `GROUP BY` clause executes, allowing filtering on aggregate functions like `SUM()`, `AVG()`, or `COUNT()`.
- *Example from our project:*
  `SELECT category_id, SUM(stock_quantity * unit_price) FROM products GROUP BY category_id HAVING SUM(stock_quantity * unit_price) > 50000;`

---

### Q10: What is a Correlated Subquery?
**Answer:**
A correlated subquery is an inner subquery that depends on values from the outer query for its evaluation, executing once for each candidate row processed by the outer query.
*Example from our project:* Finding products whose unit price exceeds their specific category average:
```sql
SELECT p.name, p.unit_price FROM products p
WHERE p.unit_price > (SELECT AVG(p2.unit_price) FROM products p2 WHERE p2.category_id = p.category_id);
```

---

### Q11: What are Window Functions, and how do they differ from Aggregate Functions?
**Answer:**
Standard aggregate functions collapse multiple rows into a single row summary. A Window Function performs a calculation across a set of table rows related to the current row, but **retains the individual identity of each row**.
In our project:
- `DENSE_RANK() OVER (PARTITION BY category_id ORDER BY unit_price DESC)` ranks products by price inside each category without skipping ranks.
- `SUM(total_amount) OVER (ORDER BY order_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` calculates running cumulative sales revenue.

---

### Q12: How is a Many-to-Many (M:N) relationship implemented in a relational database?
**Answer:**
An M:N relationship cannot be modeled directly with a single foreign key. It is decomposed into two 1:N relationships using an **associative / junction table**. In our project, the M:N relationship between `orders` and `products` is resolved via the `order_items` bridge table containing `order_id` (FK) and `product_id` (FK).

---

### Q13: What are the differences between DDL, DML, DCL, and TCL?
**Answer:**
- **DDL (Data Definition Language):** Defines structure (`CREATE`, `ALTER`, `DROP`, `TRUNCATE`).
- **DML (Data Manipulation Language):** Manipulates records (`SELECT`, `INSERT`, `UPDATE`, `DELETE`).
- **DCL (Data Control Language):** Manages user access and permissions (`GRANT`, `REVOKE`).
- **TCL (Transaction Control Language):** Controls transactional boundaries (`BEGIN`, `COMMIT`, `ROLLBACK`, `SAVEPOINT`).

---

### Q14: How does your database prevent stock from going below zero?
**Answer:**
We use a two-layer defense mechanism:
1. **CHECK Constraint:** `CHECK (stock_quantity >= 0)` defined at the table level in `schema.sql`.
2. **Database Trigger:** `trg_prevent_negative_stock` set to `BEFORE UPDATE`, which aborts the operation with an explicit custom error message if an incoming calculation would result in negative stock.

---

### Q15: What is Data Redundancy and what anomalies does it cause?
**Answer:**
Data redundancy is the unnecessary duplication of data. It causes:
1. **Insertion Anomaly:** Inability to record certain facts without adding unrelated data (e.g. inability to add a supplier without a product).
2. **Deletion Anomaly:** Unintended loss of valid data when deleting a record.
3. **Update Anomaly:** Inconsistent data if an update is applied to one copy of data but not others.
*Our schema prevents all three by normalizing into distinct 3NF relations.*

---

### Q16: What is SQLite and why is it suitable for this project?
**Answer:**
SQLite is a self-contained, serverless, zero-configuration, transactional SQL database engine. It stores the entire relational database in a single cross-platform disk file (`product_management.db`), fully supports standard SQL syntax, ACID transactions, foreign keys, triggers, views, and indexes, making it both lightweight and production-ready.

---

### Q17: What is the difference between `DELETE`, `TRUNCATE`, and `DROP`?
**Answer:**
- `DELETE`: DML command that removes specific rows based on a `WHERE` condition. Logs each row deletion and fires `BEFORE/AFTER DELETE` triggers.
- `TRUNCATE`: DDL command that rapidly removes all rows from a table by deallocating data pages. Cannot be rolled back in some DBMSs and does not fire per-row triggers.
- `DROP`: DDL command that completely deletes the table definition along with its schema, indexes, constraints, and data from the catalog.

---

### Q18: What is the difference between `INNER JOIN` and `LEFT OUTER JOIN`?
**Answer:**
- `INNER JOIN`: Returns only matching rows that satisfy the join condition in both tables. Non-matching rows are omitted.
- `LEFT OUTER JOIN`: Returns all rows from the left table, plus matched rows from the right table. If there is no match on the right, `NULL` values are returned for the right table columns.

---

### Q19: What is database Data Provenance or Auditing?
**Answer:**
Data Provenance refers to documenting the historical lineage and origin of data changes. In our project, table `product_audit_log` records what was changed, the previous state, the new state, the user responsible, and the timestamp whenever product records are altered.

---

### Q20: What is a Candidate Key?
**Answer:**
A Candidate Key is a minimal super key—an attribute or minimal set of attributes that uniquely identifies a tuple with no redundant attributes. A table may have multiple candidate keys. One is chosen as the **Primary Key**, while the others become **Alternative / Unique Keys** (e.g. `product_id` is PK; `sku` is UK).
