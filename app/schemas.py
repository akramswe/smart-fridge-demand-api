from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=80)


class ProductRead(ProductCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    active: bool


class SaleCreate(BaseModel):
    product_id: int
    sale_date: date
    quantity_sold: int = Field(ge=0)
    waste_quantity: int = Field(default=0, ge=0)


class SaleRead(SaleCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ForecastRequest(BaseModel):
    product_id: int
    target_date: date


class ForecastResponse(BaseModel):
    product_id: int
    target_date: date
    predicted_demand: int
    training_samples: int
    model: str


class ProductAnalytics(BaseModel):
    product_id: int
    days_observed: int
    total_quantity_sold: int
    average_daily_demand: float
    average_daily_waste: float
    waste_rate: float
