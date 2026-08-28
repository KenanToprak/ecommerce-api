from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from api.deps import get_current_user
from crud import order as crud_order
from schemas.order import OrderCreate, OrderResponse
from models.user import User

router = APIRouter()

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_in: OrderCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Require authentication!
):
    """
    Create a new order for the currently logged in user.
    """
    return crud_order.create_order(db=db, order=order_in, user_id=current_user.id)

@router.get("/my-orders", response_model=List[OrderResponse])
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Require authentication!
):
    """
    Get all orders belonging to the currently logged in user.
    """
    return crud_order.get_orders_by_user(db=db, user_id=current_user.id)
