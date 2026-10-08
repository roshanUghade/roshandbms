-- ============================================================================
-- DATABASE MANAGEMENT SYSTEM (DBMS) PROJECT: PRODUCT MANAGEMENT SYSTEM
-- SCRIPT: schema.sql (Data Definition Language - DDL)
-- Target DBMS: SQLite 3 / Relational DBMS Compatible
-- ============================================================================

-- Enable Foreign Key enforcement in SQLite
PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. TABLE: categories
-- Purpose: Stores product category hierarchy and classifications
-- Normalization: 3NF compliant
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    category_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    category_code   TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name            TEXT NOT NULL UNIQUE COLLATE NOCASE,
    description     TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. TABLE: suppliers
-- Purpose: Stores supplier information providing products to the inventory
-- Normalization: 3NF compliant
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE COLLATE NOCASE,
    contact_name    TEXT,
    email           TEXT UNIQUE COLLATE NOCASE,
    phone           TEXT,
    address         TEXT,
    city            TEXT,
    country         TEXT NOT NULL DEFAULT 'India',
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 3. TABLE: products
-- Purpose: Central entity of the system containing core product specifications,
--          pricing, stock counters, and foreign keys to category and supplier.
-- Constraints: Positive price & cost, non-negative stock, valid status.
-- Normalization: 3NF / BCNF compliant
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    product_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    sku             TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name            TEXT NOT NULL,
    description     TEXT,
    category_id     INTEGER NOT NULL,
    supplier_id     INTEGER NOT NULL,
    unit_price      REAL NOT NULL CHECK (unit_price >= 0.0),
    cost_price      REAL NOT NULL CHECK (cost_price >= 0.0),
    stock_quantity  INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    reorder_level   INTEGER NOT NULL DEFAULT 10 CHECK (reorder_level >= 0),
    unit_measure    TEXT NOT NULL DEFAULT 'Piece',
    status          TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Discontinued', 'Draft')),
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories (category_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers (supplier_id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ----------------------------------------------------------------------------
-- 4. TABLE: customers
-- Purpose: Stores customer profile details for order placements
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    customer_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE COLLATE NOCASE,
    phone           TEXT,
    address         TEXT,
    city            TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 5. TABLE: orders
-- Purpose: Header records for sales orders
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    order_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number    TEXT NOT NULL UNIQUE COLLATE NOCASE,
    customer_id     INTEGER NOT NULL,
    order_date      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status          TEXT NOT NULL DEFAULT 'Completed' CHECK (status IN ('Pending', 'Completed', 'Cancelled')),
    subtotal        REAL NOT NULL DEFAULT 0.0 CHECK (subtotal >= 0.0),
    tax_amount      REAL NOT NULL DEFAULT 0.0 CHECK (tax_amount >= 0.0),
    total_amount    REAL NOT NULL DEFAULT 0.0 CHECK (total_amount >= 0.0),
    notes           TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ----------------------------------------------------------------------------
-- 6. TABLE: order_items
-- Purpose: Bridge/associative entity for M:N relationship between orders and products
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NOT NULL,
    product_id      INTEGER NOT NULL,
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    unit_price      REAL NOT NULL CHECK (unit_price >= 0.0),
    subtotal        REAL NOT NULL CHECK (subtotal >= 0.0),
    FOREIGN KEY (order_id) REFERENCES orders (order_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ----------------------------------------------------------------------------
-- 7. TABLE: inventory_transactions
-- Purpose: Immutable ledger recording all incoming and outgoing inventory movements
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory_transactions (
    transaction_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id       INTEGER NOT NULL,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('PURCHASE_IN', 'SALE_OUT', 'ADJUSTMENT', 'RETURN_IN')),
    quantity         INTEGER NOT NULL,
    unit_cost        REAL DEFAULT 0.0,
    reference_note   TEXT,
    created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- ----------------------------------------------------------------------------
-- 8. TABLE: product_audit_log
-- Purpose: Auditing table tracking data modifications (Price shifts, Stock adjustments, Status changes)
-- Demonstrates DBMS Auditing, Data Provenance, and Security Logging
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product_audit_log (
    audit_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL,
    action_type     TEXT NOT NULL CHECK (action_type IN ('INSERT', 'UPDATE_PRICE', 'UPDATE_STOCK', 'UPDATE_DETAILS', 'DELETE')),
    old_values      TEXT,
    new_values      TEXT,
    changed_by      TEXT NOT NULL DEFAULT 'system_admin',
    timestamp       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR QUERY OPTIMIZATION
-- Speeds up search, foreign key joins, sorting, and analytical queries
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_products_sku ON products (sku);
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category_id);
CREATE INDEX IF NOT EXISTS idx_products_supplier ON products (supplier_id);
CREATE INDEX IF NOT EXISTS idx_products_status ON products (status);
CREATE INDEX IF NOT EXISTS idx_products_stock ON products (stock_quantity, reorder_level);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders (customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders (order_date);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items (order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items (product_id);

CREATE INDEX IF NOT EXISTS idx_transactions_product ON inventory_transactions (product_id);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON inventory_transactions (transaction_type);
CREATE INDEX IF NOT EXISTS idx_audit_product ON product_audit_log (product_id);
