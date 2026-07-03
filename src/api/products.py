"""
API route for products endpoint for products.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.inventory import Product
from src.utils.database import get_db

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/")
def list_products(db: Session = Depends(get_db)):
    """Return all active products."""
    products = db.execute(
        select(Product).where(Product.is_active == True)  # noqa: E712
    ).scalars().all()

    return [
        {
            "id":              p.id,
            "sku":             p.sku,
            "name":            p.name,
            "tracking_type":   p.tracking_type,
            "unit_of_measure": p.unit_of_measure,
            "reorder_point":   p.reorder_point,
        }
        for p in products
    ]


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Return a single product by ID."""
    product = db.get(Product, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    return {
        "id":              product.id,
        "sku":             product.sku,
        "name":            product.name,
        "description":     product.description,
        "tracking_type":   product.tracking_type,
        "unit_of_measure": product.unit_of_measure,
        "reorder_point":   product.reorder_point,
        "reorder_qty":     product.reorder_qty,
        "is_active":       product.is_active,
    }