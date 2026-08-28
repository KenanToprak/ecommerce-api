from sqlalchemy.orm import Session
from models.product import Product
from schemas.product import ProductCreate

def get_product(db: Session, product_id: int):
    """Retrieve a single product by its ID."""
    return db.query(Product).filter(Product.id == product_id).first()

def get_products(db: Session, skip: int = 0, limit: int = 100):
    """Retrieve a list of products with pagination."""
    return db.query(Product).offset(skip).limit(limit).all()

def create_product(db: Session, product: ProductCreate):
    """Create a new product in the database."""
    db_product = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock_quantity=product.stock_quantity
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product
