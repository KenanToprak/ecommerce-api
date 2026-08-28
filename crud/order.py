from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.order import Order, OrderItem
from models.product import Product
from schemas.order import OrderCreate

def create_order(db: Session, order: OrderCreate, user_id: int):
    """Create an order with multiple items and calculate total price."""
    db_order = Order(user_id=user_id, total_price=0)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    total_price = 0.0

    for item in order.items:
        # Fetch the product from database to get its current price
        product = db.query(Product).filter(Product.id == item.product_id).first()
        
        if not product:
            # If a product doesn't exist, we should probably rollback, but for simplicity we raise an error
            raise HTTPException(status_code=404, detail=f"Product with ID {item.product_id} not found")
        
        if product.stock_quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Not enough stock for product {product.name}")

        # Reduce stock
        product.stock_quantity -= item.quantity

        db_order_item = OrderItem(
            order_id=db_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=product.price
        )
        db.add(db_order_item)
        total_price += (product.price * item.quantity)

    # Update the total price of the order
    db_order.total_price = total_price
    db.commit()
    db.refresh(db_order)

    return db_order

def get_orders_by_user(db: Session, user_id: int):
    """Retrieve all orders placed by a specific user."""
    return db.query(Order).filter(Order.user_id == user_id).all()
