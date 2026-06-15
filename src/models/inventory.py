"""
ORM models for PyWarehouse.
These mirror the database schema, used by the API and services layer.
"""





import enum

from sqlalchemy import (
    Boolean, CheckConstraint, Column, Date, Enum,
    ForeignKey, Integer, Numeric, String, Text, TIMESTAMP, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.utils.database import Base


# ENUMS

class UserRole(str, enum.Enum):
    ADMIN      = "admin"
    MANAGER    = "manager"
    OPERATIVE  = "operative"
    READ_ONLY  = "read_only"
    NO_ACCESS  = "no_access"


class TrackingType(str, enum.Enum):
    BULK       = "BULK"
    SERIALISED = "SERIALISED"
    BATCH      = "BATCH"


class SerialisedStatus(str, enum.Enum):
    IN_STOCK   = "IN_STOCK"
    DISPATCHED = "DISPATCHED"
    RETURNED   = "RETURNED"
    WRITE_OFF  = "WRITE_OFF"


class BatchStatus(str, enum.Enum):
    AVAILABLE  = "AVAILABLE"
    DEPLETED   = "DEPLETED"
    ON_HOLD    = "ON_HOLD"
    QUARANTINE = "QUARANTINE"


class MovementType(str, enum.Enum):
    RECEIVE    = "RECEIVE"
    DISPATCH   = "DISPATCH"
    TRANSFER   = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"
    RETURN     = "RETURN"
    WRITE_OFF  = "WRITE_OFF"


class POStatus(str, enum.Enum):
    DRAFT     = "DRAFT"
    SENT      = "SENT"
    PARTIAL   = "PARTIAL"
    RECEIVED  = "RECEIVED"
    CANCELLED = "CANCELLED"


class OrderStatus(str, enum.Enum):
    PENDING    = "PENDING"
    PICKING    = "PICKING"
    PACKED     = "PACKED"
    DISPATCHED = "DISPATCHED"
    CANCELLED  = "CANCELLED"


class TransferStatus(str, enum.Enum):
    DRAFT      = "DRAFT"
    PENDING    = "PENDING"
    IN_TRANSIT = "IN_TRANSIT"
    COMPLETED  = "COMPLETED"
    CANCELLED  = "CANCELLED"


# USERS & PERMISSIONS

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True)
    username      = Column(String(50),  unique=True, nullable=False)
    email         = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name     = Column(String(100))
    is_active     = Column(Boolean, default=True)
    created_at    = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at    = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    warehouse_roles = relationship("UserWarehouseRole", back_populates="user")


class Warehouse(Base):
    __tablename__ = "warehouses"

    id         = Column(Integer, primary_key=True)
    code       = Column(String(20),  unique=True, nullable=False)
    name       = Column(String(100), nullable=False)
    address    = Column(Text)
    city       = Column(String(100))
    country    = Column(String(100))
    is_active  = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    locations      = relationship("Location",         back_populates="warehouse")
    user_roles     = relationship("UserWarehouseRole", back_populates="warehouse")


class UserWarehouseRole(Base):
    __tablename__ = "user_warehouse_roles"
    __table_args__ = (UniqueConstraint("user_id", "warehouse_id"),)

    id           = Column(Integer, primary_key=True)
    user_id      = Column(Integer, ForeignKey("users.id",      ondelete="CASCADE"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    role         = Column(Enum(UserRole), nullable=False)
    created_at   = Column(TIMESTAMP(timezone=True), server_default=func.now())

    user      = relationship("User",      back_populates="warehouse_roles")
    warehouse = relationship("Warehouse", back_populates="user_roles")


# LOCATIONS

class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "aisle", "bay", "level", "bin"),
    )

    id           = Column(Integer, primary_key=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    aisle        = Column(String(10), nullable=False)
    bay          = Column(String(10), nullable=False)
    level        = Column(String(10), nullable=False)
    bin          = Column(String(10))
    barcode      = Column(String(50), unique=True)
    is_active    = Column(Boolean, default=True)
    created_at   = Column(TIMESTAMP(timezone=True), server_default=func.now())

    warehouse = relationship("Warehouse", back_populates="locations")
    stock     = relationship("Stock",     back_populates="location")


# SUPPLIERS & CATEGORIES

class Supplier(Base):
    __tablename__ = "suppliers"

    id           = Column(Integer, primary_key=True)
    code         = Column(String(20),  unique=True, nullable=False)
    name         = Column(String(200), nullable=False)
    contact_name = Column(String(100))
    email        = Column(String(150))
    phone        = Column(String(30))
    address      = Column(Text)
    is_active    = Column(Boolean, default=True)
    created_at   = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at   = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class Category(Base):
    __tablename__ = "categories"

    id          = Column(Integer, primary_key=True)
    name        = Column(String(100), nullable=False)
    parent_id   = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    description = Column(Text)
    created_at  = Column(TIMESTAMP(timezone=True), server_default=func.now())

    products = relationship("Product", back_populates="category")


# PRODUCTS

class Product(Base):
    __tablename__ = "products"

    id              = Column(Integer, primary_key=True)
    sku             = Column(String(50),  unique=True, nullable=False)
    name            = Column(String(200), nullable=False)
    description     = Column(Text)
    category_id     = Column(Integer, ForeignKey("categories.id"))
    tracking_type   = Column(Enum(TrackingType), nullable=False, default=TrackingType.BULK)
    unit_of_measure = Column(String(20), default="EA")
    weight_kg       = Column(Numeric(10, 3))
    barcode         = Column(String(100))
    reorder_point   = Column(Integer, default=0)
    reorder_qty     = Column(Integer, default=0)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at      = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    category         = relationship("Category",        back_populates="products")
    stock            = relationship("Stock",           back_populates="product")
    serialised_items = relationship("SerialisedItem",  back_populates="product")
    batches          = relationship("Batch",           back_populates="product")


# BULK STOCK

class Stock(Base):
    __tablename__ = "stock"
    __table_args__ = (UniqueConstraint("product_id", "location_id"),)

    id          = Column(Integer, primary_key=True)
    product_id  = Column(Integer, ForeignKey("products.id"),  nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    quantity    = Column(Integer, nullable=False, default=0)
    updated_at  = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    product  = relationship("Product",  back_populates="stock")
    location = relationship("Location", back_populates="stock")


# SERIALISED ITEMS

class SerialisedItem(Base):
    __tablename__ = "serialised_items"
    __table_args__ = (UniqueConstraint("product_id", "serial_number"),)

    id            = Column(Integer, primary_key=True)
    product_id    = Column(Integer, ForeignKey("products.id"),  nullable=False)
    location_id   = Column(Integer, ForeignKey("locations.id"))
    serial_number = Column(String(100), nullable=False)
    barcode       = Column(String(100))
    status        = Column(Enum(SerialisedStatus), nullable=False, default=SerialisedStatus.IN_STOCK)
    notes         = Column(Text)
    created_at    = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at    = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    product  = relationship("Product", back_populates="serialised_items")


# BATCHES

class Batch(Base):
    __tablename__ = "batches"
    __table_args__ = (UniqueConstraint("product_id", "lot_number"),)

    id               = Column(Integer, primary_key=True)
    product_id       = Column(Integer, ForeignKey("products.id"), nullable=False)
    location_id      = Column(Integer, ForeignKey("locations.id"))
    lot_number       = Column(String(100), nullable=False)
    supplier_id      = Column(Integer, ForeignKey("suppliers.id"))
    manufacture_date = Column(Date)
    expiry_date      = Column(Date)
    quantity         = Column(Integer, nullable=False, default=0)
    status           = Column(Enum(BatchStatus), nullable=False, default=BatchStatus.AVAILABLE)
    notes            = Column(Text)
    created_at       = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at       = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    product  = relationship("Product",  back_populates="batches")
    supplier = relationship("Supplier")


# STOCK MOVEMENTS

class StockMovement(Base):
    __tablename__ = "stock_movements"

    id                 = Column(Integer, primary_key=True)
    movement_type      = Column(Enum(MovementType), nullable=False)
    product_id         = Column(Integer, ForeignKey("products.id",          ondelete="RESTRICT"), nullable=False)
    from_location      = Column(Integer, ForeignKey("locations.id",         ondelete="RESTRICT"))
    to_location        = Column(Integer, ForeignKey("locations.id",         ondelete="RESTRICT"))
    quantity           = Column(Integer, nullable=False)
    reference_no       = Column(String(100))
    serialised_item_id = Column(Integer, ForeignKey("serialised_items.id",  ondelete="RESTRICT"))
    batch_id           = Column(Integer, ForeignKey("batches.id",           ondelete="RESTRICT"))
    created_by         = Column(Integer, ForeignKey("users.id",             ondelete="RESTRICT"))
    notes              = Column(Text)
    created_at         = Column(TIMESTAMP(timezone=True), server_default=func.now())

    product         = relationship("Product")
    serialised_item = relationship("SerialisedItem")
    batch           = relationship("Batch")
    user            = relationship("User")


# PURCHASE ORDERS

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id           = Column(Integer, primary_key=True)
    po_number    = Column(String(50), unique=True, nullable=False)
    supplier_id  = Column(Integer, ForeignKey("suppliers.id",  ondelete="RESTRICT"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False)
    status       = Column(Enum(POStatus), default=POStatus.DRAFT)
    expected_at  = Column(Date)
    received_at  = Column(TIMESTAMP(timezone=True))
    created_by   = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    notes        = Column(Text)
    created_at   = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at   = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    supplier  = relationship("Supplier")
    warehouse = relationship("Warehouse")
    user      = relationship("User")
    lines     = relationship("PurchaseOrderLine", back_populates="purchase_order")


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"

    id           = Column(Integer, primary_key=True)
    po_id        = Column(Integer, ForeignKey("purchase_orders.id", ondelete="RESTRICT"), nullable=False)
    product_id   = Column(Integer, ForeignKey("products.id",        ondelete="RESTRICT"), nullable=False)
    ordered_qty  = Column(Integer, nullable=False)
    received_qty = Column(Integer, default=0)
    unit_cost    = Column(Numeric(12, 4))
    created_at   = Column(TIMESTAMP(timezone=True), server_default=func.now())

    purchase_order = relationship("PurchaseOrder", back_populates="lines")
    product        = relationship("Product")


# OUTBOUND ORDERS

class Order(Base):
    __tablename__ = "orders"

    id            = Column(Integer, primary_key=True)
    order_number  = Column(String(50), unique=True, nullable=False)
    customer_ref  = Column(String(100))
    warehouse_id  = Column(Integer, ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False)
    status        = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    required_by   = Column(Date)
    dispatched_at = Column(TIMESTAMP(timezone=True))
    created_by    = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    notes         = Column(Text)
    created_at    = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at    = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    warehouse = relationship("Warehouse")
    user      = relationship("User")
    lines     = relationship("OrderLine", back_populates="order")


class OrderLine(Base):
    __tablename__ = "order_lines"

    id                 = Column(Integer, primary_key=True)
    order_id           = Column(Integer, ForeignKey("orders.id",           ondelete="RESTRICT"), nullable=False)
    product_id         = Column(Integer, ForeignKey("products.id",         ondelete="RESTRICT"), nullable=False)
    requested_qty      = Column(Integer, nullable=False)
    picked_qty         = Column(Integer, default=0)
    serialised_item_id = Column(Integer, ForeignKey("serialised_items.id", ondelete="RESTRICT"))
    batch_id           = Column(Integer, ForeignKey("batches.id",          ondelete="RESTRICT"))
    created_at         = Column(TIMESTAMP(timezone=True), server_default=func.now())

    order           = relationship("Order",          back_populates="lines")
    product         = relationship("Product")
    serialised_item = relationship("SerialisedItem")
    batch           = relationship("Batch")


# WAREHOUSE TRANSFERS

class Transfer(Base):
    __tablename__ = "transfers"
    __table_args__ = (
        CheckConstraint("from_warehouse_id != to_warehouse_id", name="ck_transfer_different_warehouses"),
    )

    id                = Column(Integer, primary_key=True)
    transfer_number   = Column(String(50), unique=True, nullable=False)
    from_warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False)
    to_warehouse_id   = Column(Integer, ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False)
    status            = Column(Enum(TransferStatus), default=TransferStatus.DRAFT)
    expected_at       = Column(Date)
    completed_at      = Column(TIMESTAMP(timezone=True))
    created_by        = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    notes             = Column(Text)
    created_at        = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at        = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    from_warehouse = relationship("Warehouse", foreign_keys=[from_warehouse_id])
    to_warehouse   = relationship("Warehouse", foreign_keys=[to_warehouse_id])
    user           = relationship("User")
    lines          = relationship("TransferLine", back_populates="transfer")


class TransferLine(Base):
    __tablename__ = "transfer_lines"

    id                 = Column(Integer, primary_key=True)
    transfer_id        = Column(Integer, ForeignKey("transfers.id",         ondelete="RESTRICT"), nullable=False)
    product_id         = Column(Integer, ForeignKey("products.id",          ondelete="RESTRICT"), nullable=False)
    requested_qty      = Column(Integer, nullable=False)
    transferred_qty    = Column(Integer, default=0)
    serialised_item_id = Column(Integer, ForeignKey("serialised_items.id",  ondelete="RESTRICT"))
    batch_id           = Column(Integer, ForeignKey("batches.id",           ondelete="RESTRICT"))
    created_at         = Column(TIMESTAMP(timezone=True), server_default=func.now())

    transfer        = relationship("Transfer",      back_populates="lines")
    product         = relationship("Product")
    serialised_item = relationship("SerialisedItem")
    batch           = relationship("Batch")
