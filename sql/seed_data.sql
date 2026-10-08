-- ============================================================================
-- DATABASE MANAGEMENT SYSTEM (DBMS) PROJECT: PRODUCT MANAGEMENT SYSTEM
-- SCRIPT: seed_data.sql (Initial Sample Data Population)
-- ============================================================================

-- Disable foreign key checks temporarily during bulk seeding if needed, then re-enable
PRAGMA foreign_keys = OFF;

-- ----------------------------------------------------------------------------
-- 1. SEED CATEGORIES
-- ----------------------------------------------------------------------------
INSERT INTO categories (category_id, category_code, name, description) VALUES
(1, 'ELEC', 'Electronics & Gadgets', 'Smart gadgets, smart home devices, and power accessories'),
(2, 'COMP', 'Computers & Peripherals', 'Laptops, monitors, mechanical keyboards, and precision mice'),
(3, 'AUD',  'Audio & Acoustics', 'Noise cancelling headphones, studio monitors, and Bluetooth speakers'),
(4, 'WEAR', 'Wearable Tech', 'Smartwatches, fitness bands, and health tracking rings'),
(5, 'OFFC', 'Office & Ergonomics', 'Ergonomic chairs, standing desks, desk mats, and accessories'),
(6, 'STOR', 'Storage & Networking', 'NVMe SSDs, external hard drives, WiFi 6 routers, and NAS');

-- ----------------------------------------------------------------------------
-- 2. SEED SUPPLIERS
-- ----------------------------------------------------------------------------
INSERT INTO suppliers (supplier_id, name, contact_name, email, phone, address, city, country) VALUES
(1, 'Apex Tech Distribution Ltd.', 'Rajesh Sharma', 'sales@apextech.in', '+91-9820011223', 'Plot 42, Electronic City Phase 1', 'Bengaluru', 'India'),
(2, 'Silicon Valley Imports Co.', 'Priya Nair', 'orders@siliconimports.com', '+91-9876543210', 'B-108, Andheri MIDC Tech Park', 'Mumbai', 'India'),
(3, 'Zenith Hardware Solutions', 'Vikram Patel', 'vikram@zenithsolutions.in', '+91-9988776655', 'Sector 18, Udyog Vihar', 'Gurugram', 'India'),
(4, 'OmniSource Global Traders', 'Ananya Deshmukh', 'supply@omnisource.org', '+91-9123456780', 'Gera Commerce Zone, Kharadi', 'Pune', 'India'),
(5, 'Sonic Acoustics & Electro Pvt', 'Arjun Mehta', 'arjun@sonicacoustics.com', '+91-9765432109', 'Guindy Industrial Estate', 'Chennai', 'India');

-- ----------------------------------------------------------------------------
-- 3. SEED PRODUCTS
-- ----------------------------------------------------------------------------
INSERT INTO products (product_id, sku, name, description, category_id, supplier_id, unit_price, cost_price, stock_quantity, reorder_level, unit_measure, status) VALUES
(1,  'PRD-ELEC-001', 'Smart Wireless Charging Pad 15W', 'Fast charging Qi-certified wireless charging pad with LED indicator', 1, 1, 1499.00, 750.00,  45, 15, 'Piece', 'Active'),
(2,  'PRD-ELEC-002', 'USB-C GaN 65W Fast Charger', 'Ultra-compact Gallium Nitride 3-port wall charger for laptops and phones', 1, 1, 2299.00, 1100.00, 8,  12, 'Piece', 'Active'),
(3,  'PRD-COMP-001', 'RGB Mechanical Gaming Keyboard', 'Hot-swappable tactile brown switches with customizable per-key RGB backlighting', 2, 2, 4999.00, 2600.00, 25, 10, 'Piece', 'Active'),
(4,  'PRD-COMP-002', 'Ergonomic Vertical Wireless Mouse', '6-button wireless vertical mouse with adjustable DPI 800-2400', 2, 2, 1899.00, 950.00,  4,  10, 'Piece', 'Active'),
(5,  'PRD-COMP-003', '27-inch 4K UHD IPS Designer Monitor', 'Factory calibrated 99% sRGB color accurate display with USB-C 90W PD', 2, 3, 32999.00, 22500.00, 14, 5, 'Piece', 'Active'),
(6,  'PRD-AUD-001',  'ANC Wireless Over-Ear Headphones', 'Active Noise Cancelling Bluetooth 5.3 headphones with 40h battery life', 3, 5, 8999.00, 4800.00, 18, 8,  'Piece', 'Active'),
(7,  'PRD-AUD-002',  'True Wireless Earbuds with ENC', 'Quad-mic environmental noise cancellation earbuds with low-latency gaming mode', 3, 5, 2999.00, 1350.00, 0,  15, 'Piece', 'Active'),
(8,  'PRD-AUD-003',  'Portable Waterproof Bluetooth Speaker', '20W stereo output, IPX7 waterproof rating with deep bass radiator', 3, 5, 3499.00, 1700.00, 22, 10, 'Piece', 'Active'),
(9,  'PRD-WEAR-001', 'Smartwatch Pro AMOLED GPS', '1.43-inch AMOLED display, built-in GPS, SpO2 & Heart Rate 24/7 tracker', 4, 4, 6499.00, 3400.00, 12, 10, 'Piece', 'Active'),
(10, 'PRD-WEAR-002', 'Fitness Tracker Smart Band 8', 'Slim lightweight fitness band with 120 sports modes and 14-day battery', 4, 4, 2199.00, 1050.00, 30, 15, 'Piece', 'Active'),
(11, 'PRD-OFFC-001', 'Ergonomic High-Back Mesh Chair', 'Adjustable 3D armrests, lumbar support, and breathable Korean mesh', 5, 3, 14500.00, 8500.00, 6,  5,  'Piece', 'Active'),
(12, 'PRD-OFFC-002', 'Electric Dual-Motor Standing Desk', 'Height adjustable 72cm-120cm with memory presets and anti-collision sensor', 5, 3, 26999.00, 17000.00, 5, 3,  'Piece', 'Active'),
(13, 'PRD-OFFC-003', 'Extended Felt Desk Mat 90x40cm', 'Water-resistant natural wool felt desk pad with anti-slip rubber base', 5, 4, 899.00, 380.00, 50, 20, 'Piece', 'Active'),
(14, 'PRD-STOR-001', '1TB NVMe PCIe Gen4 M.2 SSD', 'Read speeds up to 7400 MB/s, ideal for high performance gaming and video editing', 6, 2, 7499.00, 4800.00, 15, 8, 'Piece', 'Active'),
(15, 'PRD-STOR-002', '2TB Rugged External Portable SSD', 'Drop-resistant, water-resistant IP55 portable solid state drive', 6, 2, 12999.00, 8500.00, 9, 6, 'Piece', 'Active'),
(16, 'PRD-STOR-003', 'WiFi 6 Dual-Band Gigabit Router', 'AX3000 speeds, 4 external antennas, OFDMA and MU-MIMO technology', 6, 1, 3999.00, 2200.00, 3, 8, 'Piece', 'Active'),
(17, 'PRD-ELEC-003', '10000mAh Magnetic Power Bank', 'MagSafe compatible wireless portable charger with 20W wired PD', 1, 1, 2499.00, 1250.00, 1, 10, 'Piece', 'Active'),
(18, 'PRD-COMP-004', '4K Ultra HD Streaming Webcam', 'Auto-focus HDR webcam with dual noise-reduction microphones and privacy shutter', 2, 2, 5499.00, 2900.00, 16, 5, 'Piece', 'Active');

-- ----------------------------------------------------------------------------
-- 4. SEED CUSTOMERS
-- ----------------------------------------------------------------------------
INSERT INTO customers (customer_id, name, email, phone, address, city) VALUES
(1, 'Aarav Kulkarni', 'aarav.k@example.com', '+91-9821123456', 'Flat 402, Green Glen Layout, Bellandur', 'Bengaluru'),
(2, 'Rohan Verma',    'rohan.verma@example.com', '+91-9871198765', 'A-24, Vasant Kunj Pocket B', 'New Delhi'),
(3, 'Sneha Iyer',      'sneha.iyer@example.com', '+91-9765544332', '304, Sea Breeze Apt, Bandra West', 'Mumbai'),
(4, 'Tanmay Joshi',   'tanmay.j@example.com', '+91-9988223344', 'Plot 12, Baner Pashan Link Road', 'Pune'),
(5, 'Meera Sen',       'meera.sen@example.com', '+91-9122334455', '88, Southern Avenue', 'Kolkata'),
(6, 'Aditya Rao',      'aditya.rao@example.com', '+91-9445566778', '14, Anna Nagar 2nd Avenue', 'Chennai');

-- ----------------------------------------------------------------------------
-- 5. SEED ORDERS
-- ----------------------------------------------------------------------------
INSERT INTO orders (order_id, order_number, customer_id, order_date, status, subtotal, tax_amount, total_amount, notes) VALUES
(1, 'ORD-2026-001', 1, '2026-09-15 11:30:00', 'Completed', 7298.00, 1313.64, 8611.64, 'Express shipping requested'),
(2, 'ORD-2026-002', 3, '2026-09-20 14:15:00', 'Completed', 37998.00, 6839.64, 44837.64, 'Deliver between 10am and 4pm'),
(3, 'ORD-2026-003', 2, '2026-09-28 16:45:00', 'Completed', 8999.00, 1619.82, 10618.82, 'Gift packaging included'),
(4, 'ORD-2026-004', 4, '2026-10-02 10:20:00', 'Completed', 26999.00, 4859.82, 31858.82, 'Corporate workstation setup'),
(5, 'ORD-2026-005', 5, '2026-10-05 18:00:00', 'Pending',   5498.00, 989.64, 6487.64, 'Pending customer payment verification');

-- ----------------------------------------------------------------------------
-- 6. SEED ORDER ITEMS
-- ----------------------------------------------------------------------------
INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price, subtotal) VALUES
(1, 1, 1, 1, 1499.00, 1499.00),
(2, 1, 2, 1, 2299.00, 2299.00),
(3, 1, 8, 1, 3499.00, 3499.00),
(4, 2, 3, 1, 4999.00, 4999.00),
(5, 2, 5, 1, 32999.00, 32999.00),
(6, 3, 6, 1, 8999.00, 8999.00),
(7, 4, 12, 1, 26999.00, 26999.00),
(8, 5, 1, 2, 1499.00, 2998.00),
(9, 5, 17, 1, 2499.00, 2499.00);

-- ----------------------------------------------------------------------------
-- 7. SEED INVENTORY INITIAL TRANSACTIONS
-- ----------------------------------------------------------------------------
INSERT INTO inventory_transactions (product_id, transaction_type, quantity, unit_cost, reference_note, created_at) VALUES
(1,  'PURCHASE_IN', 50,  750.00,  'Initial Procurement Batch PO-001', '2026-09-01 09:00:00'),
(2,  'PURCHASE_IN', 15,  1100.00, 'Initial Procurement Batch PO-001', '2026-09-01 09:15:00'),
(3,  'PURCHASE_IN', 30,  2600.00, 'Initial Procurement Batch PO-002', '2026-09-02 10:00:00'),
(4,  'PURCHASE_IN', 10,  950.00,  'Initial Procurement Batch PO-002', '2026-09-02 10:30:00'),
(5,  'PURCHASE_IN', 15,  22500.00,'Initial Procurement Batch PO-003', '2026-09-03 11:00:00'),
(6,  'PURCHASE_IN', 20,  4800.00, 'Initial Procurement Batch PO-004', '2026-09-04 12:00:00'),
(7,  'PURCHASE_IN', 15,  1350.00, 'Initial Procurement Batch PO-004', '2026-09-04 12:30:00'),
(8,  'PURCHASE_IN', 25,  1700.00, 'Initial Procurement Batch PO-004', '2026-09-04 13:00:00'),
(9,  'PURCHASE_IN', 15,  3400.00, 'Initial Procurement Batch PO-005', '2026-09-05 14:00:00'),
(10, 'PURCHASE_IN', 35,  1050.00, 'Initial Procurement Batch PO-005', '2026-09-05 14:30:00'),
(11, 'PURCHASE_IN', 8,   8500.00, 'Initial Procurement Batch PO-003', '2026-09-06 15:00:00'),
(12, 'PURCHASE_IN', 6,   17000.00,'Initial Procurement Batch PO-003', '2026-09-06 15:30:00'),
(13, 'PURCHASE_IN', 60,  380.00,  'Initial Procurement Batch PO-005', '2026-09-07 16:00:00'),
(14, 'PURCHASE_IN', 20,  4800.00, 'Initial Procurement Batch PO-002', '2026-09-08 10:00:00'),
(15, 'PURCHASE_IN', 12,  8500.00, 'Initial Procurement Batch PO-002', '2026-09-08 11:00:00'),
(16, 'PURCHASE_IN', 5,   2200.00, 'Initial Procurement Batch PO-001', '2026-09-09 11:30:00'),
(17, 'PURCHASE_IN', 10,  1250.00, 'Initial Procurement Batch PO-001', '2026-09-10 12:00:00'),
(18, 'PURCHASE_IN', 18,  2900.00, 'Initial Procurement Batch PO-002', '2026-09-10 13:00:00'),
(7,  'SALE_OUT',    15,  2999.00, 'Flash Sale Clearance Batch #99',    '2026-09-25 18:00:00'),
(17, 'SALE_OUT',    10,  2499.00, 'Festival Promotional Sales Batch',  '2026-09-26 19:00:00');

-- ----------------------------------------------------------------------------
-- 8. SEED INITIAL AUDIT LOGS
-- ----------------------------------------------------------------------------
INSERT INTO product_audit_log (product_id, action_type, old_values, new_values, changed_by, timestamp) VALUES
(3, 'UPDATE_PRICE', '{"price": 4799.0}', '{"price": 4999.0}', 'inventory_manager', '2026-09-15 14:20:00'),
(2, 'UPDATE_STOCK', '{"stock": 15}', '{"stock": 8}', 'sales_system', '2026-09-16 11:00:00');

-- Re-enable foreign key checks
PRAGMA foreign_keys = ON;
