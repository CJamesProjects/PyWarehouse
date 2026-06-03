-- USERS & PERMISSIONS

CREATE TYPE user_role AS ENUM ('admin', 'manager', 'operative', 'read_only');

CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(50)  UNIQUE NOT NULL,
    email         VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(100),
    is_active     BOOLEAN      DEFAULT TRUE,
    created_at    TIMESTAMPTZ  DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  DEFAULT NOW()
);

CREATE TABLE warehouses (
    id         SERIAL PRIMARY KEY,
    code       VARCHAR(20)  UNIQUE NOT NULL,
    name       VARCHAR(100) NOT NULL,
    address    TEXT,
    city       VARCHAR(100),
    country    VARCHAR(100),
    is_active  BOOLEAN      DEFAULT TRUE,
    created_at TIMESTAMPTZ  DEFAULT NOW(),
    updated_at TIMESTAMPTZ  DEFAULT NOW()
);

-- Which users can access which warehouses, and what role they have there
CREATE TABLE user_warehouse_roles (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    warehouse_id INTEGER     NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    role         user_role   NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, warehouse_id)
);


-- LOCATIONS

CREATE TABLE locations (
    id           SERIAL PRIMARY KEY,
    warehouse_id INTEGER     NOT NULL REFERENCES warehouses(id),
    aisle        VARCHAR(10) NOT NULL,
    bay          VARCHAR(10) NOT NULL,
    level        VARCHAR(10) NOT NULL,
    bin          VARCHAR(10),
    barcode      VARCHAR(50) UNIQUE,
    is_active    BOOLEAN     DEFAULT TRUE,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (warehouse_id, aisle, bay, level, bin)
);

-- SUPPLIERS & CATEGORIES

CREATE TABLE suppliers (
    id           SERIAL PRIMARY KEY,
    code         VARCHAR(20)  UNIQUE NOT NULL,
    name         VARCHAR(200) NOT NULL,
    contact_name VARCHAR(100),
    email        VARCHAR(150),
    phone        VARCHAR(30),
    address      TEXT,
    is_active    BOOLEAN      DEFAULT TRUE,
    created_at   TIMESTAMPTZ  DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  DEFAULT NOW()
);

CREATE TABLE categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    parent_id   INTEGER      REFERENCES categories(id),
    description TEXT,
    created_at  TIMESTAMPTZ  DEFAULT NOW()
);

-- PRODUCTS          #splits into bulk, serial and batch products

CREATE TYPE tracking_type AS ENUM ('BULK', 'SERIALISED', 'BATCH');

CREATE TABLE products (
    id              SERIAL PRIMARY KEY,
    sku             VARCHAR(50)   UNIQUE NOT NULL,
    name            VARCHAR(200)  NOT NULL,
    description     TEXT,
    category_id     INTEGER       REFERENCES categories(id),
    tracking_type   tracking_type NOT NULL DEFAULT 'BULK',
    unit_of_measure VARCHAR(20)   DEFAULT 'EA',
    weight_kg       NUMERIC(10,3),
    barcode         VARCHAR(100),
    reorder_point   INTEGER       DEFAULT 0,
    reorder_qty     INTEGER       DEFAULT 0,
    is_active       BOOLEAN       DEFAULT TRUE,
    created_at      TIMESTAMPTZ   DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   DEFAULT NOW()
);

-- BULK STOCK
-- BULK items only          #parts

CREATE TABLE stock (
    id          SERIAL PRIMARY KEY,
    product_id  INTEGER     NOT NULL REFERENCES products(id),
    location_id INTEGER     NOT NULL REFERENCES locations(id),
    quantity    INTEGER     NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (product_id, location_id)
);

-- SERIALISED ITEMS
-- SERIALISED items only      #assets

CREATE TYPE serialised_status AS ENUM (
    'IN_STOCK', 'DISPATCHED', 'RETURNED', 'WRITE_OFF'
);

CREATE TABLE serialised_items (
    id            SERIAL PRIMARY KEY,
    product_id    INTEGER           NOT NULL REFERENCES products(id),
    location_id   INTEGER           REFERENCES locations(id),
    serial_number VARCHAR(100)      NOT NULL,
    barcode       VARCHAR(100),
    status        serialised_status NOT NULL DEFAULT 'IN_STOCK',
    notes         TEXT,
    created_at    TIMESTAMPTZ       DEFAULT NOW(),
    updated_at    TIMESTAMPTZ       DEFAULT NOW(),
    UNIQUE (product_id, serial_number)
);

-- BATCH / LOT ITEMS
-- identical items sharing manufacture date and lot number           #batches

CREATE TYPE batch_status AS ENUM (
    'AVAILABLE', 'DEPLETED', 'ON_HOLD', 'QUARANTINE'
);

CREATE TABLE batches (
    id               SERIAL PRIMARY KEY,
    product_id       INTEGER      NOT NULL REFERENCES products(id),
    location_id      INTEGER      REFERENCES locations(id),
    lot_number       VARCHAR(100) NOT NULL,
    supplier_id      INTEGER      REFERENCES suppliers(id),
    manufacture_date DATE,
    expiry_date      DATE,        DEFAULT NULL,
    quantity         INTEGER      NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    status           batch_status NOT NULL DEFAULT 'AVAILABLE',
    notes            TEXT,
    created_at       TIMESTAMPTZ  DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (product_id, lot_number)
);



-- OUTBOUND ORDERS

CREATE TYPE order_status AS ENUM ('PENDING', 'PICKING', 'PACKED', 'DISPATCHED', 'CANCELLED');

CREATE TABLE orders (
    id            SERIAL PRIMARY KEY,
    order_number  VARCHAR(50)  UNIQUE NOT NULL,
    customer_ref  VARCHAR(100),
    warehouse_id  INTEGER      NOT NULL REFERENCES warehouses(id) ON DELETE RESTRICT,
    status        order_status DEFAULT 'PENDING',
    required_by   DATE,
    dispatched_at TIMESTAMPTZ,
    created_by    INTEGER      REFERENCES users(id) ON DELETE RESTRICT,
    notes         TEXT,
    created_at    TIMESTAMPTZ  DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  DEFAULT NOW()
);

CREATE TABLE order_lines (
    id                 SERIAL PRIMARY KEY,
    order_id           INTEGER     NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    product_id         INTEGER     NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    requested_qty      INTEGER     NOT NULL CHECK (requested_qty > 0),
    picked_qty         INTEGER     DEFAULT 0 CHECK (picked_qty >= 0),
    serialised_item_id INTEGER     REFERENCES serialised_items(id) ON DELETE RESTRICT,
    batch_id           INTEGER     REFERENCES batches(id) ON DELETE RESTRICT,
    created_at         TIMESTAMPTZ DEFAULT NOW()
);

-- PURCHASE ORDERS

CREATE TYPE po_status AS ENUM ('DRAFT', 'SENT', 'PARTIAL', 'RECEIVED', 'CANCELLED');

CREATE TABLE purchase_orders (
    id           SERIAL PRIMARY KEY,
    po_number    VARCHAR(50) UNIQUE NOT NULL,
    supplier_id  INTEGER     NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
    warehouse_id INTEGER     NOT NULL REFERENCES warehouses(id) ON DELETE RESTRICT,
    status       po_status   DEFAULT 'DRAFT',
    expected_at  DATE,
    received_at  TIMESTAMPTZ,
    created_by   INTEGER     REFERENCES users(id) ON DELETE RESTRICT,
    notes        TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE purchase_order_lines (
    id           SERIAL PRIMARY KEY,
    po_id        INTEGER     NOT NULL REFERENCES purchase_orders(id) ON DELETE RESTRICT,
    product_id   INTEGER     NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    ordered_qty  INTEGER     NOT NULL CHECK (ordered_qty > 0),
    received_qty INTEGER     DEFAULT 0 CHECK (received_qty >= 0),
    unit_cost    NUMERIC(12,4),
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- To do
-- - reorder points varying across warehouses?
-- - add an ON DELETE - possibly just restrict or soft delete
-- - add indexes for faster querying
-- - add triggers, cant pick more than available stock, cant put serialised item into bulk stock
-- - add views?