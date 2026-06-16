
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.inventory import (
    Batch, BatchStatus, MovementType, Product,
    SerialisedItem, SerialisedStatus, Stock, StockMovement,
)


class StockError(Exception):
    pass


class InsufficientStockError(StockError):
    pass


class InvalidTrackingTypeError(StockError):
    pass


@dataclass
class MovementResult:
    movement_id:                 int
    product_sku:                 str
    quantity:                    int
    new_quantity_at_destination: int | None = None


# BULK STOCK OPERATIONS

def receive_bulk(
    db: Session,
    product_id: int,
    location_id: int,
    quantity: int,
    reference_no: str | None = None,
    notes: str | None = None,
    created_by: int | None = None,
) -> MovementResult:
    """Receive bulk stock into a location."""
    if quantity <= 0:
        raise StockError("Quantity must be positive.")

    # upsert: add to existing stock row or create a new one
    stock = db.execute(
        select(Stock).where(
            Stock.product_id == product_id,
            Stock.location_id == location_id,
        )
    ).scalar_one_or_none()

    if stock:
        stock.quantity += quantity
    else:
        stock = Stock(product_id=product_id, location_id=location_id, quantity=quantity)
        db.add(stock)

    movement = StockMovement(
        movement_type=MovementType.RECEIVE,
        product_id=product_id,
        to_location=location_id,
        quantity=quantity,
        reference_no=reference_no,
        notes=notes,
        created_by=created_by,
    )
    db.add(movement)
    db.flush()

    return MovementResult(
        movement_id=movement.id,
        product_sku=stock.product.sku,
        quantity=quantity,
        new_quantity_at_destination=stock.quantity,
    )


def dispatch_bulk(
    db: Session,
    product_id: int,
    location_id: int,
    quantity: int,
    reference_no: str | None = None,
    notes: str | None = None,
    created_by: int | None = None,
) -> MovementResult:
    """Dispatch bulk stock from a location."""
    if quantity <= 0:
        raise StockError("Quantity must be positive.")

    stock = db.execute(
        select(Stock).where(
            Stock.product_id == product_id,
            Stock.location_id == location_id,
        )
    ).scalar_one_or_none()

    if not stock or stock.quantity < quantity:
        available = stock.quantity if stock else 0
        raise InsufficientStockError(
            f"Requested {quantity} but only {available} available at location {location_id}."
        )

    stock.quantity -= quantity

    movement = StockMovement(
        movement_type=MovementType.DISPATCH,
        product_id=product_id,
        from_location=location_id,
        quantity=quantity,
        reference_no=reference_no,
        notes=notes,
        created_by=created_by,
    )
    db.add(movement)
    db.flush()

    return MovementResult(
        movement_id=movement.id,
        product_sku=stock.product.sku,
        quantity=quantity,
        new_quantity_at_destination=stock.quantity,
    )


def transfer_bulk(
    db: Session,
    product_id: int,
    from_location_id: int,
    to_location_id: int,
    quantity: int,
    created_by: int | None = None,
) -> MovementResult:
    """Transfer bulk stock between two locations."""
    # dispatch from source (validates available qty)
    dispatch_bulk(db, product_id, from_location_id, quantity, created_by=created_by)

    # receive at destination
    return receive_bulk(
        db,
        product_id,
        to_location_id,
        quantity,
        notes=f"Transfer from location {from_location_id}",
        created_by=created_by,
    )


# SERIALISED ITEM OPERATIONS

def receive_serialised(
    db: Session,
    product_id: int,
    location_id: int,
    serial_number: str,
    barcode: str | None = None,
    reference_no: str | None = None,
    notes: str | None = None,
    created_by: int | None = None,
) -> MovementResult:
    """Receive a serialised item into a location."""
    # check serial number doesn't already exist for this product
    existing = db.execute(
        select(SerialisedItem).where(
            SerialisedItem.product_id == product_id,
            SerialisedItem.serial_number == serial_number,
        )
    ).scalar_one_or_none()

    if existing:
        raise StockError(f"Serial number {serial_number} already exists for this product.")

    item = SerialisedItem(
        product_id=product_id,
        location_id=location_id,
        serial_number=serial_number,
        barcode=barcode,
        status=SerialisedStatus.IN_STOCK,
        notes=notes,
    )
    db.add(item)

    movement = StockMovement(
        movement_type=MovementType.RECEIVE,
        product_id=product_id,
        to_location=location_id,
        quantity=1,
        serialised_item_id=item.id,
        reference_no=reference_no,
        notes=notes,
        created_by=created_by,
    )
    db.add(movement)
    db.flush()

    return MovementResult(
        movement_id=movement.id,
        product_sku=item.product.sku,
        quantity=1,
    )


def dispatch_serialised(
    db: Session,
    serialised_item_id: int,
    reference_no: str | None = None,
    notes: str | None = None,
    created_by: int | None = None,
) -> MovementResult:
    """Dispatch a specific serialised item."""
    item = db.get(SerialisedItem, serialised_item_id)

    if not item:
        raise StockError(f"Serialised item {serialised_item_id} not found.")

    if item.status != SerialisedStatus.IN_STOCK:
        raise StockError(f"Item {item.serial_number} is not available (status: {item.status}).")

    item.status = SerialisedStatus.DISPATCHED
    item.location_id = None  # no longer in a warehouse location

    movement = StockMovement(
        movement_type=MovementType.DISPATCH,
        product_id=item.product_id,
        from_location=item.location_id,
        quantity=1,
        serialised_item_id=item.id,
        reference_no=reference_no,
        notes=notes,
        created_by=created_by,
    )
    db.add(movement)
    db.flush()

    return MovementResult(
        movement_id=movement.id,
        product_sku=item.product.sku,
        quantity=1,
    )


# BATCH OPERATIONS

def receive_batch(
    db: Session,
    product_id: int,
    location_id: int,
    lot_number: str,
    quantity: int,
    supplier_id: int | None = None,
    manufacture_date=None,
    expiry_date=None,
    reference_no: str | None = None,
    notes: str | None = None,
    created_by: int | None = None,
) -> MovementResult:
    """Receive a batch of items into a location."""
    if quantity <= 0:
        raise StockError("Quantity must be positive.")

    batch = Batch(
        product_id=product_id,
        location_id=location_id,
        lot_number=lot_number,
        supplier_id=supplier_id,
        manufacture_date=manufacture_date,
        expiry_date=expiry_date,
        quantity=quantity,
        status=BatchStatus.AVAILABLE,
        notes=notes,
    )
    db.add(batch)

    movement = StockMovement(
        movement_type=MovementType.RECEIVE,
        product_id=product_id,
        to_location=location_id,
        quantity=quantity,
        batch_id=batch.id,
        reference_no=reference_no,
        notes=notes,
        created_by=created_by,
    )
    db.add(movement)
    db.flush()

    return MovementResult(
        movement_id=movement.id,
        product_sku=batch.product.sku,
        quantity=quantity,
        new_quantity_at_destination=batch.quantity,
    )


def dispatch_batch(
    db: Session,
    batch_id: int,
    quantity: int,
    reference_no: str | None = None,
    notes: str | None = None,
    created_by: int | None = None,
) -> MovementResult:
    """Dispatch a quantity from a specific batch."""
    if quantity <= 0:
        raise StockError("Quantity must be positive.")

    batch = db.get(Batch, batch_id)

    if not batch:
        raise StockError(f"Batch {batch_id} not found.")

    if batch.status != BatchStatus.AVAILABLE:
        raise StockError(f"Batch {batch.lot_number} is not available (status: {batch.status}).")

    if batch.quantity < quantity:
        raise InsufficientStockError(
            f"Requested {quantity} but only {batch.quantity} available in batch {batch.lot_number}."
        )

    batch.quantity -= quantity

    if batch.quantity == 0:
        batch.status = BatchStatus.DEPLETED

    movement = StockMovement(
        movement_type=MovementType.DISPATCH,
        product_id=batch.product_id,
        from_location=batch.location_id,
        quantity=quantity,
        batch_id=batch.id,
        reference_no=reference_no,
        notes=notes,
        created_by=created_by,
    )
    db.add(movement)
    db.flush()

    return MovementResult(
        movement_id=movement.id,
        product_sku=batch.product.sku,
        quantity=quantity,
        new_quantity_at_destination=batch.quantity,
    )


# STOCK QUERIES

def get_low_stock(db: Session, warehouse_id: int | None = None) -> list[dict]:
    """Return bulk products where total stock is at or below reorder point."""
    from src.models.inventory import Location, Warehouse

    query = (
        select(
            Product.sku,
            Product.name,
            Product.reorder_point,
            Product.reorder_qty,
            Stock.quantity,
            Warehouse.name.label("warehouse"),
        )
        .join(Stock,     Stock.product_id    == Product.id)
        .join(Location,  Location.id         == Stock.location_id)
        .join(Warehouse, Warehouse.id        == Location.warehouse_id)
        .where(Product.is_active == True)  # noqa: E712
        .where(Stock.quantity    <= Product.reorder_point)
    )

    if warehouse_id:
        query = query.where(Warehouse.id == warehouse_id)

    rows = db.execute(query).mappings().all()
    return [dict(row) for row in rows]