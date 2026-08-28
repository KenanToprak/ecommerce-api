from fastapi import FastAPI
from core.config import settings
from core.database import Base, engine
from api.endpoints import auth, products, orders
from models import user, product, order # Import models so SQLAlchemy knows about them

# Create database tables (if they don't exist yet)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="E-Commerce API Project - Built for portfolio."
)

# Include Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the E-Commerce API!"}
