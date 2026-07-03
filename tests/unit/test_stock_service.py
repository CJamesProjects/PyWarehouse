"""
unit tests for stock service.

"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.utils.database import Base
from src.models.inventory import (
    Category, Product, Location, Warehouse, TrackingType, Stock
)
from src.services.stock_service import (
    receive_bulk, dispatch_bulk, InsufficientStockError, StockError
)



# db setup test, doesn't need docker up

@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def sample_data(db):
    """Create minimal data needed to test stock operations."""
    warehouse = Warehouse(code="WH-TEST", name="Test Warehouse")
    db.add(warehouse)
    db.flush()

    location = Location(
        warehouse_id=warehouse.id,
        aisle="A", bay="01", level="1", bin="L"
    )
    db.add(location)

    category = Category(name="Test Category")
    db.add(category)
    db.flush()

    product = Product(
        sku="TEST-001",
        name="Test Product",
        tracking_type=TrackingType.BULK,
        category_id=category.id,
        reorder_point=10,
    )
    db.add(product)
    db.flush()

    return {"product": product, "location": location, "warehouse": warehouse}


# TESTS


def test_receive_bulk_creates_stock(db, sample_data):
    """receiving stock should create a stock record at the location."""
    product  = sample_data["product"]
    location = sample_data["location"]

    result = receive_bulk(db, product.id, location.id, quantity=50)

    assert result.quantity == 50
    assert result.new_quantity_at_destination == 50

    stock = db.query(Stock).filter_by(
        product_id=product.id,
        location_id=location.id
    ).first()
    assert stock is not None
    assert stock.quantity == 50


def test_receive_bulk_adds_to_existing_stock(db, sample_data):
    """receiving stock twice should accumulate the quantity."""
    product  = sample_data["product"]
    location = sample_data["location"]

    receive_bulk(db, product.id, location.id, quantity=50)
    receive_bulk(db, product.id, location.id, quantity=30)

    stock = db.query(Stock).filter_by(
        product_id=product.id,
        location_id=location.id
    ).first()
    assert stock.quantity == 80


def test_dispatch_bulk_reduces_stock(db, sample_data):
    """dispatching stock should reduce the quantity."""
    product  = sample_data["product"]
    location = sample_data["location"]

    receive_bulk(db, product.id, location.id, quantity=50)
    result = dispatch_bulk(db, product.id, location.id, quantity=20)

    assert result.quantity == 20
    assert result.new_quantity_at_destination == 30


def test_dispatch_bulk_raises_when_insufficient(db, sample_data):
    """dispatching more than available should raise InsufficientStockError."""
    product  = sample_data["product"]
    location = sample_data["location"]

    receive_bulk(db, product.id, location.id, quantity=10)

    with pytest.raises(InsufficientStockError):
        dispatch_bulk(db, product.id, location.id, quantity=99)


def test_receive_bulk_rejects_zero_quantity(db, sample_data):
    """receiving zero or negative quantity should raise StockError."""
    product  = sample_data["product"]
    location = sample_data["location"]

    with pytest.raises(StockError):
        receive_bulk(db, product.id, location.id, quantity=0)