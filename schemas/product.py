import math
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator

Money = Annotated[
    Decimal,
    PlainSerializer(lambda v: float(v), return_type=float, when_used="json"),
]


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0, allow_inf_nan=False)
    stock_quantity: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def validate_non_blank_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Product name must not be empty or whitespace.")
        return stripped

    @field_validator("price", mode="before")
    @classmethod
    def coerce_finite_price(cls, value):
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError("Price must be a finite number.")
            return Decimal(str(value))
        return value


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    price: Money

    model_config = ConfigDict(from_attributes=True)
