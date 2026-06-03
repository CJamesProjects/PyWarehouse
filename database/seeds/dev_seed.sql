-- seed data for development and testing purposes

-- Users
INSERT INTO users (username, email, password_hash, full_name) VALUES
    ('admin',     'admin@pywarehouse.com',   'changeme', 'Admin User'),
    ('jane.smith', 'jane@pywarehouse.com',   'changeme', 'Jane Smith'),
    ('tom.jones',  'tom@pywarehouse.com',    'changeme', 'Tom Jones');

-- Warehouses
INSERT INTO warehouses (code, name, address, city, country) VALUES
    ('WH-NORTH', 'North Distribution Centre', '10 Industrial Way', 'Manchester', 'UK'),
    ('WH-SOUTH', 'South Fulfilment Hub',       '5 Logistics Park',  'Bristol',    'UK');

-- User warehouse roles
INSERT INTO user_warehouse_roles (user_id, warehouse_id, role) VALUES
    (1, 1, 'admin'),
    (1, 2, 'admin'),
    (2, 1, 'operative'),
    (3, 2, 'read_only');

-- Locations (WH-NORTH)
INSERT INTO locations (warehouse_id, aisle, bay, level, bin, barcode) VALUES
    (1, 'A', '01', '1', 'L', 'LOC-A01-1L'),
    (1, 'A', '01', '1', 'R', 'LOC-A01-1R'),
    (1, 'A', '01', '2', 'L', 'LOC-A01-2L'),
    (1, 'A', '02', '1', 'L', 'LOC-A02-1L'),
    (1, 'B', '01', '1', 'L', 'LOC-B01-1L');

-- Locations (WH-SOUTH)
INSERT INTO locations (warehouse_id, aisle, bay, level, bin, barcode) VALUES
    (2, 'A', '01', '1', 'L', 'LOC-S-A01-1L'),
    (2, 'A', '01', '1', 'R', 'LOC-S-A01-1R');

-- Suppliers
INSERT INTO suppliers (code, name, contact_name, email) VALUES
    ('SUP-001', 'Acme Supplies Ltd',  'Jane Smith', 'jane@acme.example.com'),
    ('SUP-002', 'Global Parts Co',    'Tom Jones',  'tom@globalparts.example.com');

-- Categories
INSERT INTO categories (name, description) VALUES
    ('Electronics',      'Electronic components and devices'),
    ('Packaging',        'Boxes, tape, and packing materials'),
    ('Safety Equipment', 'PPE and safety items');

-- Products
INSERT INTO products (sku, name, category_id, tracking_type, unit_of_measure, reorder_point, reorder_qty) VALUES
    ('ELEC-001', 'USB-C Cable 1m',      1, 'BULK',       'EA',  50, 200),
    ('ELEC-002', 'Wireless Mouse',      1, 'SERIALISED',  'EA',   0,   0),
    ('PACK-001', 'Small Cardboard Box', 2, 'BULK',       'EA', 100, 500),
    ('SAFE-001', 'Hi-Vis Vest (M)',     3, 'BATCH',      'EA',  10,  50);

-- Bulk stock
INSERT INTO stock (product_id, location_id, quantity) VALUES
    (1, 1, 120),
    (1, 2,  80),
    (3, 4, 200);

-- Serialised items
INSERT INTO serialised_items (product_id, location_id, serial_number, barcode, status) VALUES
    (2, 3, 'SN-MOUSE-001', 'BC-MOUSE-001', 'IN_STOCK'),
    (2, 3, 'SN-MOUSE-002', 'BC-MOUSE-002', 'IN_STOCK'),
    (2, 3, 'SN-MOUSE-003', 'BC-MOUSE-003', 'DISPATCHED');

-- Batches
INSERT INTO batches (product_id, location_id, lot_number, supplier_id, manufacture_date, quantity, status) VALUES
    (4, 5, 'LOT-2026-001', 1, '2026-01-15', 30, 'AVAILABLE'),
    (4, 5, 'LOT-2026-002', 1, '2026-03-10', 20, 'AVAILABLE');