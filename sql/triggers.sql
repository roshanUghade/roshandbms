-- ============================================================================
-- DATABASE MANAGEMENT SYSTEM (DBMS) PROJECT: PRODUCT MANAGEMENT SYSTEM
-- SCRIPT: triggers.sql (Database Triggers for Business Logic & Integrity)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- TRIGGER 1: trg_prevent_negative_stock
-- Constraint Enforcement: Rejects any update attempting to make stock < 0
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_prevent_negative_stock;
CREATE TRIGGER trg_prevent_negative_stock
BEFORE UPDATE OF stock_quantity ON products
FOR EACH ROW
WHEN NEW.stock_quantity < 0
BEGIN
    SELECT RAISE(ABORT, 'DBMS Error: Stock quantity cannot be negative. Insufficient inventory.');
END;

-- ----------------------------------------------------------------------------
-- TRIGGER 2: trg_order_item_deduct_stock
-- Business Automation: Automatically decreases product stock upon sale
-- and writes an audit ledger entry in inventory_transactions
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_order_item_deduct_stock;
CREATE TRIGGER trg_order_item_deduct_stock
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    -- Deduct stock from the products table
    UPDATE products
    SET stock_quantity = stock_quantity - NEW.quantity,
        updated_at = CURRENT_TIMESTAMP
    WHERE product_id = NEW.product_id;

    -- Record transaction in the immutable ledger
    INSERT INTO inventory_transactions (
        product_id, transaction_type, quantity, unit_cost, reference_note
    ) VALUES (
        NEW.product_id,
        'SALE_OUT',
        NEW.quantity,
        NEW.unit_price,
        'Auto-deducted for Order Item ID #' || NEW.order_item_id || ' (Order #' || NEW.order_id || ')'
    );
END;

-- ----------------------------------------------------------------------------
-- TRIGGER 3: trg_order_cancelled_restore_stock
-- State Machine Automation: When an order is marked 'Cancelled',
-- automatically restore product stock and record return transactions
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_order_cancelled_restore_stock;
CREATE TRIGGER trg_order_cancelled_restore_stock
AFTER UPDATE OF status ON orders
FOR EACH ROW
WHEN OLD.status != 'Cancelled' AND NEW.status = 'Cancelled'
BEGIN
    -- Restore quantities for each ordered product
    UPDATE products
    SET stock_quantity = stock_quantity + (
        SELECT COALESCE(SUM(oi.quantity), 0)
        FROM order_items oi
        WHERE oi.order_id = NEW.order_id AND oi.product_id = products.product_id
    ),
    updated_at = CURRENT_TIMESTAMP
    WHERE product_id IN (
        SELECT oi.product_id FROM order_items oi WHERE oi.order_id = NEW.order_id
    );

    -- Log corresponding return inventory movements
    INSERT INTO inventory_transactions (
        product_id, transaction_type, quantity, unit_cost, reference_note
    )
    SELECT
        oi.product_id,
        'RETURN_IN',
        oi.quantity,
        oi.unit_price,
        'Auto-restored upon cancellation of Order ' || NEW.order_number
    FROM order_items oi
    WHERE oi.order_id = NEW.order_id;
END;

-- ----------------------------------------------------------------------------
-- TRIGGER 4: trg_product_audit_insert
-- Data Governance: Logs creation of every new product in the audit trail
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_product_audit_insert;
CREATE TRIGGER trg_product_audit_insert
AFTER INSERT ON products
FOR EACH ROW
BEGIN
    INSERT INTO product_audit_log (
        product_id, action_type, old_values, new_values, changed_by
    ) VALUES (
        NEW.product_id,
        'INSERT',
        NULL,
        json_object(
            'sku', NEW.sku,
            'name', NEW.name,
            'price', NEW.unit_price,
            'cost', NEW.cost_price,
            'stock', NEW.stock_quantity,
            'status', NEW.status
        ),
        'admin_user'
    );
END;

-- ----------------------------------------------------------------------------
-- TRIGGER 5: trg_product_audit_update
-- Data Governance: Detects and logs price changes, stock changes, or edits
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_product_audit_update;
CREATE TRIGGER trg_product_audit_update
AFTER UPDATE ON products
FOR EACH ROW
BEGIN
    INSERT INTO product_audit_log (
        product_id, action_type, old_values, new_values, changed_by
    ) VALUES (
        NEW.product_id,
        CASE
            WHEN OLD.unit_price != NEW.unit_price THEN 'UPDATE_PRICE'
            WHEN OLD.stock_quantity != NEW.stock_quantity THEN 'UPDATE_STOCK'
            ELSE 'UPDATE_DETAILS'
        END,
        json_object(
            'price', OLD.unit_price,
            'cost', OLD.cost_price,
            'stock', OLD.stock_quantity,
            'status', OLD.status
        ),
        json_object(
            'price', NEW.unit_price,
            'cost', NEW.cost_price,
            'stock', NEW.stock_quantity,
            'status', NEW.status
        ),
        'admin_user'
    );
END;

-- ----------------------------------------------------------------------------
-- TRIGGER 6: trg_product_audit_delete
-- Data Governance: Logs product deletion prior to removal
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_product_audit_delete;
CREATE TRIGGER trg_product_audit_delete
BEFORE DELETE ON products
FOR EACH ROW
BEGIN
    INSERT INTO product_audit_log (
        product_id, action_type, old_values, new_values, changed_by
    ) VALUES (
        OLD.product_id,
        'DELETE',
        json_object(
            'sku', OLD.sku,
            'name', OLD.name,
            'price', OLD.unit_price,
            'cost', OLD.cost_price,
            'stock', OLD.stock_quantity
        ),
        NULL,
        'admin_user'
    );
END;
