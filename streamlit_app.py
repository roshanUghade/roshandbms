"""
Product Management System - Streamlit DBMS Application
A complete interactive Streamlit dashboard for Database Management System (DBMS) demonstration:
Relational schema, 3NF normalization, ACID transactions, Triggers, Views, and SQL Console.
"""

import streamlit as st
import pandas as pd
import database
import json
import time
from datetime import datetime

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Product Management System | DBMS",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        padding: 1rem 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .stDataFrame {
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Ensure database is initialized
database.init_db()


# Helper function to run query and return pandas DataFrame
def get_df(query, params=()):
    conn = database.get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# -----------------------------------------------------------------------------
st.sidebar.markdown("## 📦 **ProductMS**")
st.sidebar.caption("DBMS Course Project • SQLite Engine")

# Fetch badge for low stock
try:
    low_stock_badge = database.query_db("SELECT COUNT(*) as c FROM v_low_stock_alerts", one=True)["c"]
except Exception:
    low_stock_badge = 0

menu_options = [
    "📊 Executive Dashboard",
    "📦 Products Catalog",
    "➕ Add New Product",
    "🛒 New Order (ACID Demo)",
    "🧾 Orders & Invoices",
    f"⚠️ Low Stock Alerts ({low_stock_badge})",
    "🔄 Inventory Ledger",
    "🏷️ Categories & Suppliers",
    "💻 Interactive SQL Console",
    "📐 ER Schema & Data Dictionary",
    "🛡️ Trigger Audit Trail"
]

choice = st.sidebar.radio("Navigation", menu_options)

st.sidebar.markdown("---")
st.sidebar.markdown("**DBMS Status**")
st.sidebar.success("SQLite 3.x • Foreign Keys: ON")

if st.sidebar.button("🔄 Reset Database (Fresh Data)", use_container_width=True):
    database.init_db(force_recreate=True)
    st.sidebar.success("Database reset with seed data!")
    st.rerun()

st.sidebar.caption("© 2026 Product Management System")


# -----------------------------------------------------------------------------
# 1. EXECUTIVE DASHBOARD
# -----------------------------------------------------------------------------
if choice == "📊 Executive Dashboard":
    st.markdown('<div class="main-header">📊 Executive DBMS Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Real-time analytical metrics, stock valuation, and relational queries</div>', unsafe_allow_html=True)

    # Top KPI metrics
    tot_products = database.query_db("SELECT COUNT(*) as c FROM products", one=True)["c"]
    val_data = database.query_db("SELECT SUM(stock_quantity * unit_price) as retail, SUM(stock_quantity * cost_price) as cost FROM products", one=True)
    retail_val = val_data["retail"] or 0.0
    cost_val = val_data["cost"] or 0.0
    
    order_data = database.query_db("SELECT COUNT(*) as orders, COALESCE(SUM(total_amount), 0.0) as rev FROM orders WHERE status != 'Cancelled'", one=True)
    total_rev = order_data["rev"]
    total_orders = order_data["orders"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Products", value=f"{tot_products:,}")
    with col2:
        st.metric(label="Total Inventory Value", value=f"₹{retail_val:,.2f}", delta=f"Cost: ₹{cost_val:,.2f}")
    with col3:
        st.metric(label="Low / Out of Stock", value=f"{low_stock_badge}", delta="-Replenish" if low_stock_badge > 0 else "Optimal", delta_color="inverse")
    with col4:
        st.metric(label="Sales Revenue", value=f"₹{total_rev:,.2f}", delta=f"{total_orders} Orders")

    st.markdown("---")

    # Visual Charts
    col_chart1, col_chart2 = st.columns([3, 2])
    with col_chart1:
        st.subheader("📈 Inventory Breakdown by Category")
        cat_df = get_df("""
            SELECT c.name as Category, COUNT(p.product_id) as Products, COALESCE(SUM(p.stock_quantity), 0) as Units
            FROM categories c
            LEFT JOIN products p ON c.category_id = p.category_id
            GROUP BY c.category_id, c.name
        """)
        st.bar_chart(cat_df.set_index("Category")[["Products", "Units"]])

    with col_chart2:
        st.subheader("🎯 Stock Health Distribution")
        stock_dist = database.query_db("""
            SELECT 
                SUM(CASE WHEN stock_quantity = 0 THEN 1 ELSE 0 END) as Out_of_Stock,
                SUM(CASE WHEN stock_quantity > 0 AND stock_quantity <= reorder_level THEN 1 ELSE 0 END) as Low_Stock,
                SUM(CASE WHEN stock_quantity > reorder_level THEN 1 ELSE 0 END) as Optimal_Stock
            FROM products WHERE status = 'Active'
        """, one=True)
        dist_df = pd.DataFrame({
            "Status": ["Optimal Stock", "Low Stock", "Out of Stock"],
            "Count": [stock_dist["Optimal_Stock"] or 0, stock_dist["Low_Stock"] or 0, stock_dist["Out_of_Stock"] or 0]
        })
        st.dataframe(dist_df, use_container_width=True, hide_index=True)

    # Tables: Top Selling Products & Recent Orders
    col_tbl1, col_tbl2 = st.columns([3, 2])
    with col_tbl1:
        st.subheader("🔥 Top Selling Products (SQL View: `v_top_selling_products`)")
        top_df = get_df("SELECT sku as SKU, product_name as Product, category_name as Category, total_units_sold as Units_Sold, total_revenue as Revenue, gross_profit as Profit FROM v_top_selling_products LIMIT 6")
        top_df["Revenue"] = top_df["Revenue"].apply(lambda x: f"₹{x:,.2f}")
        top_df["Profit"] = top_df["Profit"].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(top_df, use_container_width=True, hide_index=True)

    with col_tbl2:
        st.subheader("🕒 Recent Sales Orders")
        orders_df = get_df("SELECT order_number as Order_ID, customer_name as Customer, status as Status, total_amount as Total FROM v_sales_orders_summary LIMIT 6")
        orders_df["Total"] = orders_df["Total"].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(orders_df, use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# 2. PRODUCTS CATALOG
# -----------------------------------------------------------------------------
elif choice == "📦 Products Catalog":
    st.markdown('<div class="main-header">📦 Product Catalog & Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">View, search, filter, and export the product inventory</div>', unsafe_allow_html=True)

    # Filters row
    col_f1, col_f2, col_f3, col_f4 = st.columns([3, 2, 2, 2])
    with col_f1:
        search_kw = st.text_input("🔍 Search Product or SKU", "")
    with col_f2:
        cats = ["All Categories"] + [c["name"] for c in database.query_db("SELECT name FROM categories ORDER BY name")]
        selected_cat = st.selectbox("Category Filter", cats)
    with col_f3:
        sups = ["All Suppliers"] + [s["name"] for s in database.query_db("SELECT name FROM suppliers ORDER BY name")]
        selected_sup = st.selectbox("Supplier Filter", sups)
    with col_f4:
        status_filter = st.selectbox("Stock Status", ["All", "IN_STOCK", "LOW_STOCK", "OUT_OF_STOCK"])

    # Query builder
    query = "SELECT product_id, sku, product_name, category_name, supplier_name, unit_price, cost_price, profit_margin_pct, stock_quantity, reorder_level, stock_status FROM v_product_catalog WHERE 1=1"
    params = []

    if search_kw:
        query += " AND (product_name LIKE ? OR sku LIKE ?)"
        params.extend([f"%{search_kw}%", f"%{search_kw}%"])
    if selected_cat != "All Categories":
        query += " AND category_name = ?"
        params.append(selected_cat)
    if selected_sup != "All Suppliers":
        query += " AND supplier_name = ?"
        params.append(selected_sup)
    if status_filter != "All":
        query += " AND stock_status = ?"
        params.append(status_filter)

    query += " ORDER BY product_name ASC"
    products_df = get_df(query, params)

    st.write(f"Showing **{len(products_df)}** products:")
    
    # Format currency for display
    display_df = products_df.copy()
    display_df["unit_price"] = display_df["unit_price"].apply(lambda x: f"₹{x:,.2f}")
    display_df["cost_price"] = display_df["cost_price"].apply(lambda x: f"₹{x:,.2f}")
    display_df["profit_margin_pct"] = display_df["profit_margin_pct"].apply(lambda x: f"{x:.1f}%")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "product_id": "ID",
            "sku": "SKU",
            "product_name": "Product Name",
            "category_name": "Category",
            "supplier_name": "Supplier",
            "unit_price": "Price",
            "cost_price": "Cost",
            "profit_margin_pct": "Margin",
            "stock_quantity": "Stock",
            "reorder_level": "Min Level",
            "stock_status": "Status"
        }
    )

    # CSV Download Button
    csv_data = products_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Products to CSV",
        data=csv_data,
        file_name="products_catalog_export.csv",
        mime="text/csv"
    )

    st.markdown("---")
    # Quick Edit / Delete section
    st.subheader("⚙️ Manage Individual Product")
    if not products_df.empty:
        prod_options = {f"{row['product_name']} ({row['sku']})": row['product_id'] for _, row in products_df.iterrows()}
        selected_prod_name = st.selectbox("Select product to edit or delete:", list(prod_options.keys()))
        selected_prod_id = prod_options[selected_prod_name]

        curr_prod = database.query_db("SELECT * FROM products WHERE product_id = ?", (selected_prod_id,), one=True)
        if curr_prod:
            with st.expander(f"Edit {curr_prod['name']}"):
                with st.form("edit_product_form"):
                    e_name = st.text_input("Product Name", curr_prod["name"])
                    e_desc = st.text_area("Description", curr_prod["description"] or "")
                    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
                    with col_e1:
                        e_price = st.number_input("Selling Price (₹)", min_value=0.0, value=float(curr_prod["unit_price"]), step=10.0)
                    with col_e2:
                        e_cost = st.number_input("Cost Price (₹)", min_value=0.0, value=float(curr_prod["cost_price"]), step=10.0)
                    with col_e3:
                        e_stock = st.number_input("Stock Quantity", min_value=0, value=int(curr_prod["stock_quantity"]), step=1)
                    with col_e4:
                        e_reorder = st.number_input("Reorder Level", min_value=0, value=int(curr_prod["reorder_level"]), step=1)

                    if st.form_submit_button("💾 Save Changes (Triggers Audit Log)"):
                        database.execute_db("""
                            UPDATE products
                            SET name = ?, description = ?, unit_price = ?, cost_price = ?, stock_quantity = ?, reorder_level = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE product_id = ?
                        """, (e_name, e_desc, e_price, e_cost, e_stock, e_reorder, selected_prod_id))
                        st.success("Product updated successfully! Database trigger recorded the audit change.")
                        st.rerun()

            col_del1, col_del2 = st.columns([1, 4])
            with col_del1:
                if st.button("🗑️ Delete Product", type="secondary"):
                    try:
                        database.execute_db("DELETE FROM products WHERE product_id = ?", (selected_prod_id,))
                        st.success("Product deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Cannot delete product. Relational constraint violation: {e}")


# -----------------------------------------------------------------------------
# 3. ADD NEW PRODUCT
# -----------------------------------------------------------------------------
elif choice == "➕ Add New Product":
    st.markdown('<div class="main-header">➕ Add New Product</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Insert a new record adhering to DDL constraints and foreign keys</div>', unsafe_allow_html=True)

    categories = database.query_db("SELECT category_id, name FROM categories ORDER BY name")
    suppliers = database.query_db("SELECT supplier_id, name FROM suppliers ORDER BY name")

    with st.form("new_product_form"):
        col1, col2 = st.columns(2)
        with col1:
            p_sku = st.text_input("SKU (Unique Code) *", placeholder="e.g. PRD-ELEC-099")
            p_name = st.text_input("Product Name *", placeholder="e.g. Mechanical Gaming Keyboard")
            cat_dict = {c["name"]: c["category_id"] for c in categories}
            p_cat = st.selectbox("Category (Foreign Key) *", list(cat_dict.keys()))
        with col2:
            sup_dict = {s["name"]: s["supplier_id"] for s in suppliers}
            p_sup = st.selectbox("Supplier (Foreign Key) *", list(sup_dict.keys()))
            p_status = st.selectbox("Status", ["Active", "Discontinued", "Draft"])
            p_measure = st.selectbox("Unit of Measure", ["Piece", "Box", "Set", "Kg", "Liter"])

        p_desc = st.text_area("Product Description", placeholder="Specifications, warranty, details...")

        col3, col4, col5, col6 = st.columns(4)
        with col3:
            p_price = st.number_input("Selling Price (₹) *", min_value=0.0, value=999.0, step=10.0)
        with col4:
            p_cost = st.number_input("Cost Price (₹) *", min_value=0.0, value=500.0, step=10.0)
        with col5:
            p_stock = st.number_input("Initial Stock Quantity *", min_value=0, value=20, step=1)
        with col6:
            p_reorder = st.number_input("Reorder Alert Level *", min_value=0, value=10, step=1)

        submitted = st.form_submit_button("🚀 Insert Product into Database", use_container_width=True)
        if submitted:
            if not p_sku or not p_name:
                st.error("Please fill in both SKU and Product Name.")
            else:
                try:
                    new_id = database.execute_db("""
                        INSERT INTO products (sku, name, description, category_id, supplier_id, unit_price, cost_price, stock_quantity, reorder_level, unit_measure, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (p_sku, p_name, p_desc, cat_dict[p_cat], sup_dict[p_sup], p_price, p_cost, p_stock, p_reorder, p_measure, p_status))

                    if p_stock > 0:
                        database.execute_db("""
                            INSERT INTO inventory_transactions (product_id, transaction_type, quantity, unit_cost, reference_note)
                            VALUES (?, 'PURCHASE_IN', ?, ?, 'Initial Stock Balance')
                        """, (new_id, p_stock, p_cost))

                    st.success(f"Product '{p_name}' (ID: #{new_id}) successfully inserted! Trigger recorded audit log.")
                except Exception as e:
                    st.error(f"Error inserting product: {e}")


# -----------------------------------------------------------------------------
# 4. NEW ORDER (ACID DEMO)
# -----------------------------------------------------------------------------
elif choice == "🛒 New Order (ACID Demo)":
    st.markdown('<div class="main-header">🛒 Point of Sale & ACID Transactions</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Demonstration of Atomicity, Consistency, and Automated Trigger Stock Deductions</div>', unsafe_allow_html=True)

    st.info("💡 **ACID Guarantee:** Placing an order executes inside an atomic database transaction. If any requested item exceeds available stock, the entire transaction issues a **ROLLBACK**, preventing inconsistent inventory states.")

    customers = database.query_db("SELECT customer_id, name, city FROM customers ORDER BY name")
    available_products = database.query_db("SELECT product_id, sku, name, unit_price, stock_quantity FROM products WHERE status='Active' AND stock_quantity > 0 ORDER BY name")

    cust_dict = {f"{c['name']} ({c['city']})": c['customer_id'] for c in customers}
    sel_customer = st.selectbox("Select Customer:", list(cust_dict.keys()))

    st.markdown("#### Select Products to Purchase")
    selected_items = []
    
    prod_dict = {f"{p['name']} (SKU: {p['sku']}) - Stock: {p['stock_quantity']} - ₹{p['unit_price']:,.2f}": p for p in available_products}
    chosen_products = st.multiselect("Choose Products:", list(prod_dict.keys()))

    if chosen_products:
        quantities = {}
        for p_label in chosen_products:
            prod_info = prod_dict[p_label]
            col_p1, col_p2, col_p3 = st.columns([3, 1, 1])
            with col_p1:
                st.write(f"**{prod_info['name']}** (`{prod_info['sku']}`)")
            with col_p2:
                qty = st.number_input(f"Quantity (Max {prod_info['stock_quantity']})", min_value=1, max_value=prod_info['stock_quantity'], value=1, key=f"qty_{prod_info['product_id']}")
                quantities[prod_info['product_id']] = (prod_info, qty)
            with col_p3:
                line_subtotal = prod_info['unit_price'] * qty
                st.write(f"₹{line_subtotal:,.2f}")

        # Summary calculation
        subtotal = sum(p_info['unit_price'] * q for p_id, (p_info, q) in quantities.items())
        tax = round(subtotal * 0.18, 2)
        total = round(subtotal + tax, 2)

        st.markdown("---")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.metric("Subtotal", f"₹{subtotal:,.2f}")
        with col_s2:
            st.metric("GST Tax (18%)", f"₹{tax:,.2f}")
        with col_s3:
            st.metric("Grand Total", f"₹{total:,.2f}")

        order_notes = st.text_input("Order Notes / Instructions", "Standard Delivery")

        if st.button("🚀 Commit & Place Order (ACID)", type="primary", use_container_width=True):
            conn = database.get_connection()
            try:
                cur = conn.cursor()
                cur.execute("BEGIN TRANSACTION")

                order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{int(time.time()) % 10000:04d}"
                cust_id = cust_dict[sel_customer]

                cur.execute("""
                    INSERT INTO orders (order_number, customer_id, status, subtotal, tax_amount, total_amount, notes)
                    VALUES (?, ?, 'Completed', ?, ?, ?, ?)
                """, (order_number, cust_id, subtotal, tax, total, order_notes))
                new_order_id = cur.lastrowid

                # Insert line items (Trigger trg_order_item_deduct_stock deducts stock!)
                for p_id, (p_info, q) in quantities.items():
                    line_amt = round(p_info['unit_price'] * q, 2)
                    cur.execute("""
                        INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
                        VALUES (?, ?, ?, ?, ?)
                    """, (new_order_id, p_id, q, p_info['unit_price'], line_amt))

                conn.commit()
                st.success(f"Order #{order_number} successfully placed! Database triggers automatically deducted stock from products table.")
                st.balloons()
            except Exception as e:
                conn.rollback()
                st.error(f"Transaction Aborted & Rolled Back: {e}")
            finally:
                conn.close()


# -----------------------------------------------------------------------------
# 5. ORDERS & INVOICES
# -----------------------------------------------------------------------------
elif choice == "🧾 Orders & Invoices":
    st.markdown('<div class="main-header">🧾 Orders Ledger & Invoices</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">View customer invoices and test trigger-based order cancellation</div>', unsafe_allow_html=True)

    orders_df = get_df("SELECT * FROM v_sales_orders_summary")
    st.dataframe(
        orders_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "order_id": "ID",
            "order_number": "Order #",
            "order_date": "Date",
            "status": "Status",
            "customer_name": "Customer",
            "customer_city": "City",
            "total_line_items": "Items",
            "total_units_purchased": "Units",
            "total_amount": "Total (₹)"
        }
    )

    if not orders_df.empty:
        st.markdown("---")
        st.subheader("🔍 Inspect Order Invoice")
        ord_dict = {f"{row['order_number']} - {row['customer_name']} (₹{row['total_amount']:,.2f})": row['order_id'] for _, row in orders_df.iterrows()}
        selected_ord_label = st.selectbox("Choose Order to View:", list(ord_dict.keys()))
        selected_ord_id = ord_dict[selected_ord_label]

        items_df = get_df("""
            SELECT p.sku, p.name as product_name, oi.quantity, oi.unit_price, oi.subtotal
            FROM order_items oi
            INNER JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = ?
        """, (selected_ord_id,))

        st.dataframe(items_df, use_container_width=True, hide_index=True)

        # Cancel Order button to test cancellation trigger
        order_row = database.query_db("SELECT status FROM orders WHERE order_id = ?", (selected_ord_id,), one=True)
        if order_row and order_row["status"] != "Cancelled":
            st.warning("⚠️ **DBMS Trigger Demonstration:** Cancelling this order fires `trg_order_cancelled_restore_stock` which automatically adds product stock quantities back into the `products` table and writes `RETURN_IN` entries into `inventory_transactions`.")
            if st.button("❌ Cancel Order & Test Stock Restoration Trigger"):
                database.execute_db("UPDATE orders SET status = 'Cancelled' WHERE order_id = ?", (selected_ord_id,))
                st.success("Order status updated to 'Cancelled'. Stock restored via trigger!")
                st.rerun()


# -----------------------------------------------------------------------------
# 6. LOW STOCK ALERTS
# -----------------------------------------------------------------------------
elif choice.startswith("⚠️ Low Stock Alerts"):
    st.markdown('<div class="main-header">⚠️ Low Stock & Replenishment Center</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Decision support view: products below safety reorder threshold</div>', unsafe_allow_html=True)

    low_df = get_df("SELECT * FROM v_low_stock_alerts")
    
    if low_df.empty:
        st.success("🎉 All inventory products are currently above their reorder threshold!")
    else:
        tot_shortfall = low_df["units_needed_for_reorder"].sum()
        est_cost = (low_df["units_needed_for_reorder"] * low_df["cost_price"]).sum()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Products Needing Reorder", len(low_df))
        with col2:
            st.metric("Total Shortfall Units", f"{tot_shortfall} Units")
        with col3:
            st.metric("Est. Procurement Cost", f"₹{est_cost:,.2f}")

        st.dataframe(
            low_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "sku": "SKU",
                "product_name": "Product",
                "category_name": "Category",
                "supplier_name": "Supplier",
                "stock_quantity": "Current Stock",
                "reorder_level": "Min Level",
                "units_needed_for_reorder": "Shortfall",
                "cost_price": "Unit Cost (₹)"
            }
        )

        st.markdown("---")
        st.subheader("⚡ Quick Restock Action")
        low_dict = {f"{r['product_name']} (Shortfall: {r['units_needed_for_reorder']})": r for _, r in low_df.iterrows()}
        restock_choice = st.selectbox("Select product to restock:", list(low_dict.keys()))
        prod_data = low_dict[restock_choice]

        with st.form("quick_restock_form"):
            r_qty = st.number_input("Quantity to Add", min_value=1, value=int(prod_data["units_needed_for_reorder"]))
            r_note = st.text_input("PO Note", f"Restock batch for {prod_data['sku']}")
            if st.form_submit_button("✅ Confirm Restock"):
                new_qty = prod_data["stock_quantity"] + r_qty
                database.execute_db("UPDATE products SET stock_quantity = ? WHERE product_id = ?", (new_qty, int(prod_data["product_id"])))
                database.execute_db("""
                    INSERT INTO inventory_transactions (product_id, transaction_type, quantity, unit_cost, reference_note)
                    VALUES (?, 'PURCHASE_IN', ?, ?, ?)
                """, (int(prod_data["product_id"]), r_qty, prod_data["cost_price"], r_note))
                st.success(f"Restocked {r_qty} units! Stock updated to {new_qty}.")
                st.rerun()


# -----------------------------------------------------------------------------
# 7. INVENTORY LEDGER
# -----------------------------------------------------------------------------
elif choice == "🔄 Inventory Ledger":
    st.markdown('<div class="main-header">🔄 Immutable Stock Ledger</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Full audit log of incoming and outgoing inventory movements</div>', unsafe_allow_html=True)

    trx_type = st.selectbox("Filter Movement Type:", ["All Types", "PURCHASE_IN", "SALE_OUT", "RETURN_IN", "ADJUSTMENT"])
    
    query = """
        SELECT t.transaction_id, p.sku, p.name as product_name, t.transaction_type, t.quantity, t.unit_cost, t.reference_note, t.created_at
        FROM inventory_transactions t
        INNER JOIN products p ON t.product_id = p.product_id
        WHERE 1=1
    """
    params = []
    if trx_type != "All Types":
        query += " AND t.transaction_type = ?"
        params.append(trx_type)
    query += " ORDER BY t.transaction_id DESC"

    trx_df = get_df(query, params)
    st.dataframe(trx_df, use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# 8. CATEGORIES & SUPPLIERS
# -----------------------------------------------------------------------------
elif choice == "🏷️ Categories & Suppliers":
    st.markdown('<div class="main-header">🏷️ Categories & Suppliers</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Normalized entity management and vendor metrics</div>', unsafe_allow_html=True)

    tab_cat, tab_sup = st.tabs(["Categories Analytics", "Suppliers Directory"])
    
    with tab_cat:
        cat_df = get_df("SELECT * FROM v_category_analytics")
        st.dataframe(cat_df, use_container_width=True, hide_index=True)

    with tab_sup:
        sup_df = get_df("SELECT * FROM v_supplier_performance")
        st.dataframe(sup_df, use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# 9. INTERACTIVE SQL CONSOLE
# -----------------------------------------------------------------------------
elif choice == "💻 Interactive SQL Console":
    st.markdown('<div class="main-header">💻 Interactive SQL Console & Playground</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Execute real SQL queries directly against the database with execution latency timers</div>', unsafe_allow_html=True)

    sample_queries = {
        "3-Table Multi Join (Products, Categories, Suppliers)": """SELECT 
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
ORDER BY c.name, p.unit_price DESC;""",
        "Correlated Subquery (Price > Category Average)": """SELECT 
    p.product_id, 
    p.sku, 
    p.name, 
    p.unit_price,
    ROUND((SELECT AVG(p2.unit_price) FROM products p2 WHERE p2.category_id = p.category_id), 2) AS category_avg
FROM products p
WHERE p.unit_price > (
    SELECT AVG(p2.unit_price) FROM products p2 WHERE p2.category_id = p.category_id
)
ORDER BY p.unit_price DESC;""",
        "Window Function: DENSE_RANK() Price Hierarchy": """SELECT 
    c.name AS category,
    p.name AS product_name,
    p.unit_price,
    DENSE_RANK() OVER (
        PARTITION BY p.category_id 
        ORDER BY p.unit_price DESC
    ) AS rank_in_category
FROM products p
INNER JOIN categories c ON p.category_id = c.category_id
ORDER BY c.name, rank_in_category;""",
        "Window Function: Running Total Cumulative Sales": """SELECT 
    order_id,
    order_number,
    order_date,
    total_amount,
    ROUND(SUM(total_amount) OVER (
        ORDER BY order_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2) AS running_total_revenue
FROM orders
WHERE status != 'Cancelled'
ORDER BY order_date ASC;""",
        "GROUP BY with HAVING (Inventory > ₹50,000)": """SELECT 
    c.name AS category_name,
    COUNT(p.product_id) AS total_products,
    SUM(p.stock_quantity) AS total_units,
    ROUND(SUM(p.stock_quantity * p.unit_price), 2) AS total_retail_value
FROM categories c
INNER JOIN products p ON c.category_id = p.category_id
GROUP BY c.category_id, c.name
HAVING SUM(p.stock_quantity * p.unit_price) > 50000.00
ORDER BY total_retail_value DESC;"""
    }

    selected_sample = st.selectbox("📚 Select an Educational Pre-built SQL Query:", ["-- Custom Query --"] + list(sample_queries.keys()))
    default_text = sample_queries[selected_sample] if selected_sample != "-- Custom Query --" else "SELECT * FROM v_product_catalog LIMIT 10;"

    user_query = st.text_area("SQL Statement:", default_text, height=180)

    if st.button("▶️ Run SQL Query", type="primary"):
        res = database.execute_raw_sql(user_query)
        if res["success"]:
            st.success(f"Execution Succeeded! Latency: **{res['execution_time_ms']} ms** • Rows: **{res['row_count']}**")
            if res["columns"] and res["rows"]:
                df_res = pd.DataFrame(res["rows"], columns=res["columns"])
                st.dataframe(df_res, use_container_width=True)
            elif res["type"] == "DML":
                st.info(f"DML Statement executed. Affected rows: {res['row_count']}")
        else:
            st.error(f"SQL Error: {res['error_message']}")


# -----------------------------------------------------------------------------
# 10. ER SCHEMA & DATA DICTIONARY
# -----------------------------------------------------------------------------
elif choice == "📐 ER Schema & Data Dictionary":
    st.markdown('<div class="main-header">📐 ER Schema & Data Dictionary</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Relational metadata, foreign key constraints, triggers, and views</div>', unsafe_allow_html=True)

    meta = database.get_database_schema_metadata()
    st.markdown(f"**Database Catalog:** {len(meta['tables'])} Tables • {len(meta['triggers'])} Triggers • {len(meta['views'])} Views")

    for tbl_name, tbl_info in meta["tables"].items():
        with st.expander(f"📁 Table: `{tbl_name}` ({tbl_info['row_count']} records)"):
            cols_df = pd.DataFrame(tbl_info["columns"])[["name", "type", "pk", "notnull", "dflt_value"]]
            cols_df.columns = ["Column Name", "Data Type", "Primary Key", "NOT NULL", "Default"]
            st.dataframe(cols_df, use_container_width=True, hide_index=True)
            if tbl_info["foreign_keys"]:
                st.markdown("**Foreign Key Constraints:**")
                for fk in tbl_info["foreign_keys"]:
                    st.code(f"{fk['from_col']} -> {fk['to_table']}({fk['to_col']}) [ON DELETE {fk['on_delete']}]")

    st.markdown("---")
    st.subheader("⚡ Active Database Triggers")
    for trg in meta["triggers"]:
        with st.expander(f"Trigger: `{trg['name']}` on `{trg['table']}`"):
            st.code(trg["sql"], language="sql")

    st.subheader("👁️ Analytical Database Views")
    for v in meta["views"]:
        with st.expander(f"View: `{v['name']}`"):
            st.code(v["sql"], language="sql")


# -----------------------------------------------------------------------------
# 11. TRIGGER AUDIT TRAIL
# -----------------------------------------------------------------------------
elif choice == "🛡️ Trigger Audit Trail":
    st.markdown('<div class="main-header">🛡️ Trigger-Driven Audit Trail</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Automatic data provenance captured by database triggers</div>', unsafe_allow_html=True)

    st.info("💡 **DBMS Governance:** The table below is populated automatically by database triggers (`trg_product_audit_insert`, `trg_product_audit_update`). It logs previous states and updated states in JSON format.")

    audit_df = get_df("""
        SELECT pal.audit_id, p.sku, p.name as product_name, pal.action_type, pal.old_values, pal.new_values, pal.changed_by, pal.timestamp
        FROM product_audit_log pal
        LEFT JOIN products p ON pal.product_id = p.product_id
        ORDER BY pal.audit_id DESC
    """)
    st.dataframe(audit_df, use_container_width=True, hide_index=True)
