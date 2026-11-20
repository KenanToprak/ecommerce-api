from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from api.deps import get_current_active_user
from core.database import get_db
from crud import order as crud_order
from models.user import User
from schemas.order import OrderCreate, OrderResponse

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new order for the currently logged-in active user."""
    return crud_order.create_order(db=db, order=order_in, user_id=current_user.id)


@router.get("/my-orders", response_model=List[OrderResponse])
def get_my_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get paginated orders belonging to the currently logged-in active user."""
    return crud_order.get_orders_by_user(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
