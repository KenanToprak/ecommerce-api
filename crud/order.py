from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from models.order import Order, OrderItem
from models.product import Product
from schemas.order import OrderCreate


def create_order(db: Session, order: OrderCreate, user_id: int):
    """Create an order atomically, validating stock and aggregating duplicate product IDs."""
    aggregated_quantities: dict[int, int] = {}
    for item in order.items:
        aggregated_quantities[item.product_id] = (
            aggregated_quantities.get(item.product_id, 0) + item.quantity
        )

    if not aggregated_quantities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must contain at least one item",
        )

    try:
        sorted_ids = sorted(aggregated_quantities.keys())
        query = db.query(Product).filter(Product.id.in_(sorted_ids)).order_by(Product.id)
        if db.bind is not None and db.bind.dialect.name != "sqlite":
            query = query.with_for_update()

        products_by_id = {product.id: product for product in query.all()}

        # Validate existence and sufficient stock for all items before mutating anything
        for product_id, quantity in aggregated_quantities.items():
            product = products_by_id.get(product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {product_id} not found",
                )
            if product.stock_quantity < quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Not enough stock for product {product.name}",
                )

        db_order = Order(user_id=user_id, total_price=Decimal("0.00"))
        db.add(db_order)
        db.flush()

        total_price = Decimal("0.00")
        for product_id, quantity in aggregated_quantities.items():
            product = products_by_id[product_id]
            product.stock_quantity -= quantity
            unit_price = Decimal(str(product.price))

            db_order_item = OrderItem(
                order_id=db_order.id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
            )
            db.add(db_order_item)
            total_price += unit_price * quantity

        db_order.total_price = total_price
        db.commit()
    except Exception:
        db.rollback()
        raise

    return (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.id == db_order.id)
        .first()
    )


def get_orders_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Retrieve paginated orders placed by a specific user with eager-loaded items."""
    return (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.user_id == user_id)
        .order_by(Order.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
