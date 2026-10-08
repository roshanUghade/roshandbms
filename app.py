"""
Product Management System - DBMS Application
A full-featured Flask Web Application demonstrating Relational DBMS concepts:
DDL/DML, Triggers, Views, Foreign Keys, Indexes, Normalization, ACID Transactions, and Analytics.
"""

from flask import (
    Flask, render_template, request, redirect, url_for, flash, jsonify, Response
)
import database
import io
import csv
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "dbms_product_management_secret_key_2026"


# ----------------------------------------------------------------------------
# CONTEXT PROCESSOR & FILTERS
# ----------------------------------------------------------------------------
@app.template_filter("currency")
def currency_filter(value):
    try:
        val = float(value)
        return f"₹{val:,.2f}"
    except (ValueError, TypeError):
        return "₹0.00"


@app.template_filter("datetime_format")
def datetime_format(value):
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", ""))
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return str(value)


@app.context_processor
def inject_globals():
    # Low stock notification badge count for sidebar
    try:
        low_stock_count = database.query_db(
            "SELECT COUNT(*) as count FROM v_low_stock_alerts", one=True
        )["count"]
    except Exception:
        low_stock_count = 0
    return {"nav_low_stock_count": low_stock_count}


# ----------------------------------------------------------------------------
# 1. DASHBOARD ROUTE
# ----------------------------------------------------------------------------
@app.route("/")
def index():
    # Fetch key business metrics
    total_products = database.query_db("SELECT COUNT(*) as c FROM products", one=True)["c"]
    total_categories = database.query_db("SELECT COUNT(*) as c FROM categories", one=True)["c"]
    total_suppliers = database.query_db("SELECT COUNT(*) as c FROM suppliers", one=True)["c"]
    
    inventory_val = database.query_db(
        "SELECT SUM(stock_quantity * unit_price) as retail_val, SUM(stock_quantity * cost_price) as cost_val FROM products",
        one=True
    )
    total_retail_val = inventory_val["retail_val"] or 0.0
    total_cost_val = inventory_val["cost_val"] or 0.0
    
    stock_counts = database.query_db("""
        SELECT 
            SUM(CASE WHEN stock_quantity = 0 THEN 1 ELSE 0 END) as out_of_stock,
            SUM(CASE WHEN stock_quantity > 0 AND stock_quantity <= reorder_level THEN 1 ELSE 0 END) as low_stock,
            SUM(CASE WHEN stock_quantity > reorder_level THEN 1 ELSE 0 END) as optimal_stock
        FROM products WHERE status = 'Active'
    """, one=True)

    sales_summary = database.query_db("""
        SELECT 
            COUNT(order_id) as total_orders,
            COALESCE(SUM(total_amount), 0.0) as total_revenue
        FROM orders WHERE status != 'Cancelled'
    """, one=True)

    # Categories breakdown for chart
    categories_chart = database.query_db("""
        SELECT c.name, COUNT(p.product_id) as product_count, COALESCE(SUM(p.stock_quantity), 0) as total_stock
        FROM categories c
        LEFT JOIN products p ON c.category_id = p.category_id
        GROUP BY c.category_id, c.name
    """)

    # Top 5 selling products from view
    top_products = database.query_db("SELECT * FROM v_top_selling_products LIMIT 5")

    # Recent orders from view
    recent_orders = database.query_db("SELECT * FROM v_sales_orders_summary LIMIT 5")

    # Recent inventory movements
    recent_transactions = database.query_db("""
        SELECT t.*, p.name as product_name, p.sku
        FROM inventory_transactions t
        INNER JOIN products p ON t.product_id = p.product_id
        ORDER BY t.transaction_id DESC
        LIMIT 6
    """)

    return render_template(
        "index.html",
        total_products=total_products,
        total_categories=total_categories,
        total_suppliers=total_suppliers,
        total_retail_val=total_retail_val,
        total_cost_val=total_cost_val,
        stock_counts=stock_counts,
        sales_summary=sales_summary,
        categories_chart=categories_chart,
        top_products=top_products,
        recent_orders=recent_orders,
        recent_transactions=recent_transactions
    )


# ----------------------------------------------------------------------------
# 2. PRODUCT MANAGEMENT ROUTES
# ----------------------------------------------------------------------------
@app.route("/products")
def product_list():
    search = request.args.get("search", "").strip()
    category_id = request.args.get("category", "")
    supplier_id = request.args.get("supplier", "")
    stock_status = request.args.get("status", "")
    sort_by = request.args.get("sort", "name_asc")

    query = "SELECT * FROM v_product_catalog WHERE 1=1"
    params = []

    if search:
        query += " AND (product_name LIKE ? OR sku LIKE ? OR description LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    if category_id:
        query += " AND category_id = ?"
        params.append(category_id)

    if supplier_id:
        query += " AND supplier_id = ?"
        params.append(supplier_id)

    if stock_status:
        query += " AND stock_status = ?"
        params.append(stock_status)

    sort_mapping = {
        "name_asc": "product_name ASC",
        "name_desc": "product_name DESC",
        "price_asc": "unit_price ASC",
        "price_desc": "unit_price DESC",
        "stock_asc": "stock_quantity ASC",
        "stock_desc": "stock_quantity DESC",
        "sku_asc": "sku ASC",
    }
    order_clause = sort_mapping.get(sort_by, "product_name ASC")
    query += f" ORDER BY {order_clause}"

    products = database.query_db(query, params)
    categories = database.query_db("SELECT * FROM categories ORDER BY name")
    suppliers = database.query_db("SELECT * FROM suppliers ORDER BY name")

    return render_template(
        "products/list.html",
        products=products,
        categories=categories,
        suppliers=suppliers,
        search=search,
        selected_category=category_id,
        selected_supplier=supplier_id,
        selected_status=stock_status,
        selected_sort=sort_by
    )


@app.route("/products/new", methods=["GET", "POST"])
def product_create():
    if request.method == "POST":
        sku = request.form.get("sku", "").strip()
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        category_id = request.form.get("category_id")
        supplier_id = request.form.get("supplier_id")
        unit_price = request.form.get("unit_price", 0.0)
        cost_price = request.form.get("cost_price", 0.0)
        stock_quantity = request.form.get("stock_quantity", 0)
        reorder_level = request.form.get("reorder_level", 10)
        unit_measure = request.form.get("unit_measure", "Piece")
        status = request.form.get("status", "Active")

        # Validation
        if not sku or not name or not category_id or not supplier_id:
            flash("SKU, Name, Category, and Supplier are required fields.", "danger")
            return redirect(url_for("product_create"))

        try:
            prod_id = database.execute_db("""
                INSERT INTO products (sku, name, description, category_id, supplier_id, unit_price, cost_price, stock_quantity, reorder_level, unit_measure, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sku, name, description, category_id, supplier_id, float(unit_price), float(cost_price), int(stock_quantity), int(reorder_level), unit_measure, status))

            # If initial stock was provided > 0, log an initial inventory purchase transaction
            if int(stock_quantity) > 0:
                database.execute_db("""
                    INSERT INTO inventory_transactions (product_id, transaction_type, quantity, unit_cost, reference_note)
                    VALUES (?, 'PURCHASE_IN', ?, ?, 'Initial Stock Balance on Creation')
                """, (prod_id, int(stock_quantity), float(cost_price)))

            flash(f"Product '{name}' (SKU: {sku}) created successfully! Audit trigger logged.", "success")
            return redirect(url_for("product_detail", product_id=prod_id))
        except Exception as e:
            flash(f"Error creating product: {e}", "danger")

    categories = database.query_db("SELECT * FROM categories ORDER BY name")
    suppliers = database.query_db("SELECT * FROM suppliers ORDER BY name")
    return render_template("products/form.html", categories=categories, suppliers=suppliers, product=None)


@app.route("/products/<int:product_id>")
def product_detail(product_id):
    product = database.query_db(
        "SELECT * FROM v_product_catalog WHERE product_id = ?",
        (product_id,),
        one=True
    )
    if not product:
        flash("Product not found.", "warning")
        return redirect(url_for("product_list"))

    # Audit history for this product (populated by DBMS triggers)
    audit_logs = database.query_db(
        "SELECT * FROM product_audit_log WHERE product_id = ? ORDER BY timestamp DESC",
        (product_id,)
    )

    # Inventory transactions for this product
    transactions = database.query_db(
        "SELECT * FROM inventory_transactions WHERE product_id = ? ORDER BY transaction_id DESC LIMIT 15",
        (product_id,)
    )

    # Sales order history containing this product
    orders_included = database.query_db("""
        SELECT o.order_id, o.order_number, o.order_date, o.status, c.name as customer_name, oi.quantity, oi.unit_price, oi.subtotal
        FROM order_items oi
        INNER JOIN orders o ON oi.order_id = o.order_id
        INNER JOIN customers c ON o.customer_id = c.customer_id
        WHERE oi.product_id = ?
        ORDER BY o.order_date DESC
    """, (product_id,))

    return render_template(
        "products/detail.html",
        product=product,
        audit_logs=audit_logs,
        transactions=transactions,
        orders_included=orders_included
    )


@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def product_edit(product_id):
    product = database.query_db(
        "SELECT * FROM products WHERE product_id = ?",
        (product_id,),
        one=True
    )
    if not product:
        flash("Product not found.", "warning")
        return redirect(url_for("product_list"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        category_id = request.form.get("category_id")
        supplier_id = request.form.get("supplier_id")
        unit_price = float(request.form.get("unit_price", 0.0))
        cost_price = float(request.form.get("cost_price", 0.0))
        stock_quantity = int(request.form.get("stock_quantity", 0))
        reorder_level = int(request.form.get("reorder_level", 10))
        unit_measure = request.form.get("unit_measure", "Piece")
        status = request.form.get("status", "Active")

        try:
            database.execute_db("""
                UPDATE products
                SET name = ?, description = ?, category_id = ?, supplier_id = ?,
                    unit_price = ?, cost_price = ?, stock_quantity = ?, reorder_level = ?,
                    unit_measure = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE product_id = ?
            """, (name, description, category_id, supplier_id, unit_price, cost_price, stock_quantity, reorder_level, unit_measure, status, product_id))

            flash(f"Product '{name}' updated successfully! DBMS trigger recorded changes to audit log.", "success")
            return redirect(url_for("product_detail", product_id=product_id))
        except Exception as e:
            flash(f"Update failed: {e}", "danger")

    categories = database.query_db("SELECT * FROM categories ORDER BY name")
    suppliers = database.query_db("SELECT * FROM suppliers ORDER BY name")
    return render_template("products/form.html", categories=categories, suppliers=suppliers, product=product)


@app.route("/products/<int:product_id>/delete", methods=["POST"])
def product_delete(product_id):
    try:
        database.execute_db("DELETE FROM products WHERE product_id = ?", (product_id,))
        flash("Product deleted successfully.", "success")
    except Exception as e:
        flash(f"Cannot delete product. Relational constraint violation: {e}", "danger")
    return redirect(url_for("product_list"))


@app.route("/products/export")
def product_export_csv():
    products = database.query_db("SELECT * FROM v_product_catalog ORDER BY sku")
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Product ID", "SKU", "Name", "Category", "Supplier",
        "Unit Price", "Cost Price", "Profit Margin %",
        "Stock Quantity", "Reorder Level", "Stock Status", "Inventory Value"
    ])
    for p in products:
        writer.writerow([
            p["product_id"], p["sku"], p["product_name"], p["category_name"], p["supplier_name"],
            p["unit_price"], p["cost_price"], p["profit_margin_pct"],
            p["stock_quantity"], p["reorder_level"], p["stock_status"], p["inventory_retail_value"]
        ])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=products_inventory_report.csv"}
    )


# ----------------------------------------------------------------------------
# 3. INVENTORY & STOCK MANAGEMENT
# ----------------------------------------------------------------------------
@app.route("/inventory/transactions")
def inventory_transactions():
    t_type = request.args.get("type", "")
    search = request.args.get("search", "")

    query = """
        SELECT t.*, p.name as product_name, p.sku
        FROM inventory_transactions t
        INNER JOIN products p ON t.product_id = p.product_id
        WHERE 1=1
    """
    params = []
    if t_type:
        query += " AND t.transaction_type = ?"
        params.append(t_type)
    if search:
        query += " AND (p.name LIKE ? OR p.sku LIKE ? OR t.reference_note LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    query += " ORDER BY t.transaction_id DESC"
    transactions = database.query_db(query, params)
    products = database.query_db("SELECT product_id, sku, name, stock_quantity FROM products ORDER BY name")

    return render_template(
        "inventory/transactions.html",
        transactions=transactions,
        products=products,
        selected_type=t_type,
        search=search
    )


@app.route("/inventory/stock-movement", methods=["POST"])
def stock_movement():
    product_id = request.form.get("product_id")
    action = request.form.get("action")  # 'IN', 'OUT', 'ADJUST_SET'
    quantity = int(request.form.get("quantity", 0))
    note = request.form.get("note", "").strip()

    if quantity <= 0:
        flash("Quantity must be a positive number.", "danger")
        return redirect(url_for("inventory_transactions"))

    conn = database.get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT stock_quantity, cost_price, name FROM products WHERE product_id = ?", (product_id,))
        prod = cur.fetchone()
        if not prod:
            flash("Product not found.", "danger")
            return redirect(url_for("inventory_transactions"))

        current_stock = prod["stock_quantity"]
        cost_price = prod["cost_price"]

        if action == "IN":
            new_stock = current_stock + quantity
            trx_type = "PURCHASE_IN"
        elif action == "OUT":
            if current_stock < quantity:
                flash(f"Cannot deduct {quantity} units. Available stock is only {current_stock}.", "danger")
                return redirect(url_for("inventory_transactions"))
            new_stock = current_stock - quantity
            trx_type = "ADJUSTMENT"
        else:
            flash("Invalid action type.", "danger")
            return redirect(url_for("inventory_transactions"))

        # Update stock
        cur.execute("UPDATE products SET stock_quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE product_id = ?", (new_stock, product_id))
        # Record transaction
        cur.execute("""
            INSERT INTO inventory_transactions (product_id, transaction_type, quantity, unit_cost, reference_note)
            VALUES (?, ?, ?, ?, ?)
        """, (product_id, trx_type, quantity, cost_price, note or f"Manual stock movement: {trx_type}"))

        conn.commit()
        flash(f"Stock for '{prod['name']}' updated from {current_stock} to {new_stock}.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Stock movement failed: {e}", "danger")
    finally:
        conn.close()

    return redirect(url_for("inventory_transactions"))


@app.route("/inventory/reorder")
def inventory_reorder():
    low_stock_products = database.query_db("SELECT * FROM v_low_stock_alerts")
    total_shortfall = sum(p["units_needed_for_reorder"] for p in low_stock_products)
    total_estimated_cost = sum(p["units_needed_for_reorder"] * p["cost_price"] for p in low_stock_products)

    return render_template(
        "inventory/reorder.html",
        products=low_stock_products,
        total_shortfall=total_shortfall,
        total_estimated_cost=total_estimated_cost
    )


# ----------------------------------------------------------------------------
# 4. CATEGORIES & SUPPLIERS MANAGEMENT
# ----------------------------------------------------------------------------
@app.route("/categories", methods=["GET", "POST"])
def categories_list():
    if request.method == "POST":
        category_code = request.form.get("category_code", "").strip().upper()
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not category_code or not name:
            flash("Category Code and Name are required.", "danger")
        else:
            try:
                database.execute_db(
                    "INSERT INTO categories (category_code, name, description) VALUES (?, ?, ?)",
                    (category_code, name, description)
                )
                flash(f"Category '{name}' created successfully.", "success")
            except Exception as e:
                flash(f"Error creating category: {e}", "danger")
        return redirect(url_for("categories_list"))

    categories = database.query_db("SELECT * FROM v_category_analytics ORDER BY category_name")
    return render_template("categories/list.html", categories=categories)


@app.route("/categories/<int:category_id>/delete", methods=["POST"])
def category_delete(category_id):
    try:
        database.execute_db("DELETE FROM categories WHERE category_id = ?", (category_id,))
        flash("Category deleted successfully.", "success")
    except Exception as e:
        flash(f"Cannot delete category. Products are linked to it (RESTRICT constraint): {e}", "danger")
    return redirect(url_for("categories_list"))


@app.route("/suppliers", methods=["GET", "POST"])
def suppliers_list():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        contact_name = request.form.get("contact_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()

        if not name:
            flash("Supplier Name is required.", "danger")
        else:
            try:
                database.execute_db("""
                    INSERT INTO suppliers (name, contact_name, email, phone, address, city)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, contact_name, email, phone, address, city))
                flash(f"Supplier '{name}' registered successfully.", "success")
            except Exception as e:
                flash(f"Error adding supplier: {e}", "danger")
        return redirect(url_for("suppliers_list"))

    suppliers = database.query_db("SELECT * FROM v_supplier_performance ORDER BY supplier_name")
    return render_template("suppliers/list.html", suppliers=suppliers)


@app.route("/suppliers/<int:supplier_id>/delete", methods=["POST"])
def supplier_delete(supplier_id):
    try:
        database.execute_db("DELETE FROM suppliers WHERE supplier_id = ?", (supplier_id,))
        flash("Supplier deleted successfully.", "success")
    except Exception as e:
        flash(f"Cannot delete supplier. Products are linked to it (RESTRICT constraint): {e}", "danger")
    return redirect(url_for("suppliers_list"))


# ----------------------------------------------------------------------------
# 5. ORDERS & POINT OF SALE (ACID TRANSACTIONS)
# ----------------------------------------------------------------------------
@app.route("/orders")
def order_list():
    orders = database.query_db("SELECT * FROM v_sales_orders_summary")
    return render_template("orders/list.html", orders=orders)


@app.route("/orders/new", methods=["GET", "POST"])
def order_create():
    if request.method == "POST":
        customer_id = request.form.get("customer_id")
        notes = request.form.get("notes", "").strip()
        
        # Product items list from form
        product_ids = request.form.getlist("product_id[]")
        quantities = request.form.getlist("quantity[]")

        if not customer_id or not product_ids:
            flash("Please select a customer and at least one product.", "danger")
            return redirect(url_for("order_create"))

        # Generate unique order number
        order_num = f"ORD-{datetime.now().strftime('%Y%m%d')}-{int(datetime.now().timestamp()) % 10000:04d}"

        # ---------------------------------------------------------------------
        # ACID TRANSACTION DEMO:
        # Atomic execution of: Order creation + Order Items insert + Trigger Stock Deduction
        # If any product has insufficient stock or trigger aborts, ROLLBACK completely!
        # ---------------------------------------------------------------------
        conn = database.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN TRANSACTION")

            subtotal = 0.0
            order_items_data = []

            for p_id, q_val in zip(product_ids, quantities):
                qty = int(q_val)
                if qty <= 0:
                    continue

                cur.execute("SELECT product_id, name, unit_price, stock_quantity FROM products WHERE product_id = ?", (p_id,))
                prod = cur.fetchone()
                if not prod:
                    raise ValueError(f"Product ID {p_id} not found.")

                if prod["stock_quantity"] < qty:
                    raise ValueError(
                        f"Insufficient stock for '{prod['name']}'. Requested: {qty}, Available: {prod['stock_quantity']}. Transaction rolled back."
                    )

                line_subtotal = round(prod["unit_price"] * qty, 2)
                subtotal += line_subtotal
                order_items_data.append((prod["product_id"], qty, prod["unit_price"], line_subtotal))

            if not order_items_data:
                raise ValueError("No valid product quantities provided.")

            tax_amount = round(subtotal * 0.18, 2)  # 18% GST/Tax demonstration
            total_amount = round(subtotal + tax_amount, 2)

            # Insert Order Header
            cur.execute("""
                INSERT INTO orders (order_number, customer_id, status, subtotal, tax_amount, total_amount, notes)
                VALUES (?, ?, 'Completed', ?, ?, ?, ?)
            """, (order_num, customer_id, subtotal, tax_amount, total_amount, notes))
            order_id = cur.lastrowid

            # Insert Order Items (Database trigger 'trg_order_item_deduct_stock' automatically fires here!)
            for prod_id, qty, unit_price, line_subtotal in order_items_data:
                cur.execute("""
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                """, (order_id, prod_id, qty, unit_price, line_subtotal))

            conn.commit()
            flash(f"Order #{order_num} successfully placed! Stock automatically deducted via DBMS Triggers.", "success")
            return redirect(url_for("order_detail", order_id=order_id))

        except Exception as e:
            conn.rollback()
            flash(f"ACID Transaction Aborted & Rolled Back: {e}", "danger")
            return redirect(url_for("order_create"))
        finally:
            conn.close()

    customers = database.query_db("SELECT * FROM customers ORDER BY name")
    products = database.query_db("SELECT product_id, sku, name, unit_price, stock_quantity FROM products WHERE status='Active' AND stock_quantity > 0 ORDER BY name")
    return render_template("orders/create.html", customers=customers, products=products)


@app.route("/orders/<int:order_id>")
def order_detail(order_id):
    order = database.query_db("""
        SELECT o.*, c.name as customer_name, c.email as customer_email, c.phone as customer_phone, c.address as customer_address, c.city as customer_city
        FROM orders o
        INNER JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_id = ?
    """, (order_id,), one=True)

    if not order:
        flash("Order not found.", "warning")
        return redirect(url_for("order_list"))

    items = database.query_db("""
        SELECT oi.*, p.sku, p.name as product_name
        FROM order_items oi
        INNER JOIN products p ON oi.product_id = p.product_id
        WHERE oi.order_id = ?
    """, (order_id,))

    return render_template("orders/detail.html", order=order, items=items)


@app.route("/orders/<int:order_id>/cancel", methods=["POST"])
def order_cancel(order_id):
    try:
        # Updating order status to 'Cancelled' fires trigger 'trg_order_cancelled_restore_stock'
        database.execute_db("UPDATE orders SET status = 'Cancelled' WHERE order_id = ?", (order_id,))
        flash("Order marked as Cancelled. Trigger 'trg_order_cancelled_restore_stock' automatically restored product stock!", "success")
    except Exception as e:
        flash(f"Order cancellation failed: {e}", "danger")
    return redirect(url_for("order_detail", order_id=order_id))


# ----------------------------------------------------------------------------
# 6. INTERACTIVE SQL CONSOLE & DBMS PLAYGROUND
# ----------------------------------------------------------------------------
SAMPLE_QUERIES = [
    {
        "title": "3-Table INNER JOIN (Products, Categories, Suppliers)",
        "sql": """SELECT 
    p.sku, 
    p.name AS product_name, 
    c.name AS category, 
    s.name AS supplier, 
    p.unit_price, 
    p.stock_quantity 
FROM products p
INNER JOIN categories c ON p.category_id = c.category_id
INNER JOIN suppliers s ON p.supplier_id = s.supplier_id
WHERE p.status = 'Active'
ORDER BY c.name, p.unit_price DESC;"""
    },
    {
        "title": "Correlated Subquery: Products Priced Higher than Category Average",
        "sql": """SELECT 
    p.product_id, 
    p.sku, 
    p.name, 
    p.unit_price,
    ROUND((SELECT AVG(p2.unit_price) FROM products p2 WHERE p2.category_id = p.category_id), 2) AS category_avg
FROM products p
WHERE p.unit_price > (
    SELECT AVG(p2.unit_price) FROM products p2 WHERE p2.category_id = p.category_id
)
ORDER BY p.unit_price DESC;"""
    },
    {
        "title": "Aggregation with GROUP BY & HAVING (> ₹50,000 Inventory Value)",
        "sql": """SELECT 
    c.name AS category_name,
    COUNT(p.product_id) AS total_products,
    SUM(p.stock_quantity) AS total_units,
    ROUND(SUM(p.stock_quantity * p.unit_price), 2) AS total_retail_value
FROM categories c
INNER JOIN products p ON c.category_id = p.category_id
GROUP BY c.category_id, c.name
HAVING SUM(p.stock_quantity * p.unit_price) > 50000.00
ORDER BY total_retail_value DESC;"""
    },
    {
        "title": "Window Function: DENSE_RANK() Price Ranking by Category",
        "sql": """SELECT 
    c.name AS category,
    p.name AS product_name,
    p.unit_price,
    DENSE_RANK() OVER (
        PARTITION BY p.category_id 
        ORDER BY p.unit_price DESC
    ) AS rank_in_category
FROM products p
INNER JOIN categories c ON p.category_id = c.category_id
ORDER BY c.name, rank_in_category;"""
    },
    {
        "title": "Window Function: Running Total Cumulative Sales Revenue",
        "sql": """SELECT 
    order_id,
    order_number,
    order_date,
    total_amount,
    ROUND(SUM(total_amount) OVER (
        ORDER BY order_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2) AS running_total_revenue
FROM orders
WHERE status != 'Cancelled'
ORDER BY order_date ASC;"""
    },
    {
        "title": "View Inspection: Low Stock Alerts with Reorder Cost",
        "sql": """SELECT 
    sku,
    product_name,
    stock_quantity,
    reorder_level,
    units_needed_for_reorder,
    cost_price,
    ROUND(units_needed_for_reorder * cost_price, 2) AS estimated_procurement_cost
FROM v_low_stock_alerts;"""
    },
    {
        "title": "Trigger Audit Trail: Recent Automated Changes Logged",
        "sql": """SELECT 
    pal.audit_id,
    p.sku,
    p.name,
    pal.action_type,
    pal.old_values,
    pal.new_values,
    pal.changed_by,
    pal.timestamp
FROM product_audit_log pal
INNER JOIN products p ON pal.product_id = p.product_id
ORDER BY pal.timestamp DESC
LIMIT 10;"""
    },
    {
        "title": "Customer Lifetime Value (LTV) Summary",
        "sql": """SELECT 
    c.name AS customer_name,
    c.email,
    c.city,
    COUNT(o.order_id) AS total_orders,
    ROUND(SUM(o.total_amount), 2) AS lifetime_spent
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status != 'Cancelled'
GROUP BY c.customer_id, c.name, c.email, c.city
ORDER BY lifetime_spent DESC;"""
    }
]


@app.route("/sql-console", methods=["GET", "POST"])
def sql_console():
    query_text = request.form.get("sql_query", "").strip() if request.method == "POST" else ""
    result = None

    if query_text:
        result = database.execute_raw_sql(query_text)

    return render_template(
        "sql_playground.html",
        sql_query=query_text,
        result=result,
        sample_queries=SAMPLE_QUERIES
    )


# ----------------------------------------------------------------------------
# 7. ER DIAGRAM & SCHEMA VISUALIZER
# ----------------------------------------------------------------------------
@app.route("/er-diagram")
def er_diagram():
    schema_meta = database.get_database_schema_metadata()
    return render_template("er_diagram.html", schema=schema_meta)


# ----------------------------------------------------------------------------
# 8. AUDIT LOGS
# ----------------------------------------------------------------------------
@app.route("/audit-logs")
def audit_logs():
    logs = database.query_db("""
        SELECT pal.*, p.name as product_name, p.sku
        FROM product_audit_log pal
        LEFT JOIN products p ON pal.product_id = p.product_id
        ORDER BY pal.audit_id DESC
    """)
    return render_template("audit_logs.html", logs=logs)


# ----------------------------------------------------------------------------
# 9. DATABASE MAINTENANCE / RESET
# ----------------------------------------------------------------------------
@app.route("/database/reset", methods=["POST"])
def db_reset():
    try:
        database.init_db(force_recreate=True)
        flash("Database successfully reset and re-seeded with fresh demonstration data!", "success")
    except Exception as e:
        flash(f"Database reset failed: {e}", "danger")
    return redirect(url_for("index"))


# ----------------------------------------------------------------------------
# APP STARTUP
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    database.init_db()
    print("\n" + "=" * 60)
    print(" Product Management System - DBMS Web Application")
    print(" Running on http://127.0.0.1:5000")
    print("=" * 60 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=True)
