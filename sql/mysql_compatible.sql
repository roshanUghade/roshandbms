-- ============================================================================
-- DATABASE MANAGEMENT SYSTEM (DBMS) PROJECT: PRODUCT MANAGEMENT SYSTEM
-- SCRIPT: mysql_compatible.sql (MySQL / MariaDB / XAMPP / phpMyAdmin version)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS product_management_db;
USE product_management_db;

-- ----------------------------------------------------------------------------
-- 1. TABLE: categories
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    category_id     INT AUTO_INCREMENT PRIMARY KEY,
    category_code   VARCHAR(20) NOT NULL UNIQUE,
    name            VARCHAR(100) NOT NULL UNIQUE,
    description     TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 2. TABLE: suppliers
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id     INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(150) NOT NULL UNIQUE,
    contact_name    VARCHAR(100),
    email           VARCHAR(100) UNIQUE,
    phone           VARCHAR(25),
    address         TEXT,
    city            VARCHAR(60),
    country         VARCHAR(60) DEFAULT 'India',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 3. TABLE: products
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    product_id      INT AUTO_INCREMENT PRIMARY KEY,
    sku             VARCHAR(50) NOT NULL UNIQUE,
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    category_id     INT NOT NULL,
    supplier_id     INT NOT NULL,
    unit_price      DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0.0),
    cost_price      DECIMAL(10,2) NOT NULL CHECK (cost_price >= 0.0),
    stock_quantity  INT NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    reorder_level   INT NOT NULL DEFAULT 10 CHECK (reorder_level >= 0),
    unit_measure    VARCHAR(30) DEFAULT 'Piece',
    status          ENUM('Active', 'Discontinued', 'Draft') DEFAULT 'Active',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_prod_category FOREIGN KEY (category_id) REFERENCES categories (category_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_prod_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers (supplier_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 4. TABLE: customers
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    customer_id     INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    email           VARCHAR(120) NOT NULL UNIQUE,
    phone           VARCHAR(25),
    address         TEXT,
    city            VARCHAR(60),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 5. TABLE: orders
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    order_id        INT AUTO_INCREMENT PRIMARY KEY,
    order_number    VARCHAR(50) NOT NULL UNIQUE,
    customer_id     INT NOT NULL,
    order_date      DATETIME DEFAULT CURRENT_TIMESTAMP,
    status          ENUM('Pending', 'Completed', 'Cancelled') DEFAULT 'Completed',
    subtotal        DECIMAL(12,2) NOT NULL DEFAULT 0.0,
    tax_amount      DECIMAL(12,2) NOT NULL DEFAULT 0.0,
    total_amount    DECIMAL(12,2) NOT NULL DEFAULT 0.0,
    notes           TEXT,
    CONSTRAINT fk_order_customer FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 6. TABLE: order_items
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id   INT AUTO_INCREMENT PRIMARY KEY,
    order_id        INT NOT NULL,
    product_id      INT NOT NULL,
    quantity        INT NOT NULL CHECK (quantity > 0),
    unit_price      DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0.0),
    subtotal        DECIMAL(12,2) NOT NULL CHECK (subtotal >= 0.0),
    CONSTRAINT fk_item_order FOREIGN KEY (order_id) REFERENCES orders (order_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_item_product FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 7. TABLE: inventory_transactions
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory_transactions (
    transaction_id   INT AUTO_INCREMENT PRIMARY KEY,
    product_id       INT NOT NULL,
    transaction_type ENUM('PURCHASE_IN', 'SALE_OUT', 'ADJUSTMENT', 'RETURN_IN') NOT NULL,
    quantity         INT NOT NULL,
    unit_cost        DECIMAL(10,2) DEFAULT 0.0,
    reference_note   TEXT,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_trx_product FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 8. TABLE: product_audit_log
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product_audit_log (
    audit_id        INT AUTO_INCREMENT PRIMARY KEY,
    product_id      INT NOT NULL,
    action_type     ENUM('INSERT', 'UPDATE_PRICE', 'UPDATE_STOCK', 'UPDATE_DETAILS', 'DELETE') NOT NULL,
    old_values      TEXT,
    new_values      TEXT,
    changed_by      VARCHAR(60) NOT NULL DEFAULT 'system_admin',
    timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- TRIGGERS (MySQL DELIMITER syntax)
-- ----------------------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER trg_mysql_order_item_stock
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    UPDATE products 
    SET stock_quantity = stock_quantity - NEW.quantity
    WHERE product_id = NEW.product_id;

    INSERT INTO inventory_transactions (product_id, transaction_type, quantity, unit_cost, reference_note)
    VALUES (NEW.product_id, 'SALE_OUT', NEW.quantity, NEW.unit_price, CONCAT('Auto sale deduction for Order Item #', NEW.order_item_id));
END$$

CREATE TRIGGER trg_mysql_order_cancel
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
    IF OLD.status != 'Cancelled' AND NEW.status = 'Cancelled' THEN
        UPDATE products p
        JOIN order_items oi ON p.product_id = oi.product_id
        SET p.stock_quantity = p.stock_quantity + oi.quantity
        WHERE oi.order_id = NEW.order_id;
    END IF;
END$$

DELIMITER ;

-- ----------------------------------------------------------------------------
-- OPERATIONAL VIEWS
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_product_catalog AS
SELECT
    p.product_id,
    p.sku,
    p.name AS product_name,
    p.description,
    c.name AS category_name,
    s.name AS supplier_name,
    p.unit_price,
    p.cost_price,
    ROUND(p.unit_price - p.cost_price, 2) AS unit_profit,
    p.stock_quantity,
    p.reorder_level,
    p.unit_measure,
    ROUND(p.stock_quantity * p.unit_price, 2) AS inventory_value,
    p.status,
    CASE
        WHEN p.stock_quantity = 0 THEN 'OUT_OF_STOCK'
        WHEN p.stock_quantity <= p.reorder_level THEN 'LOW_STOCK'
        ELSE 'IN_STOCK'
    END AS stock_status
FROM products p
JOIN categories c ON p.category_id = c.category_id
JOIN suppliers s ON p.supplier_id = s.supplier_id;
