from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Sale
from app.schemas import (
    ForecastRequest,
    ForecastResponse,
    ProductAnalytics,
    ProductCreate,
    ProductRead,
    SaleCreate,
    SaleRead,
)
from app.services.forecasting import predict_demand

router = APIRouter(prefix="/api")


@router.post(
    "/products",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = Product(name=payload.name.strip(), category=payload.category.strip())
    db.add(product)

    try:
        db.commit()
        db.refresh(product)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this name already exists.",
        ) from exc

    return product


@router.get("/products", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db)):
    return db.scalars(select(Product).order_by(Product.name)).all()


@router.post(
    "/sales",
    response_model=SaleRead,
    status_code=status.HTTP_201_CREATED,
)
def create_sale(payload: SaleCreate, db: Session = Depends(get_db)):
    product = db.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    sale = Sale(**payload.model_dump())
    db.add(sale)

    try:
        db.commit()
        db.refresh(sale)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A sales record already exists for this product and date.",
        ) from exc

    return sale


@router.get(
    "/products/{product_id}/analytics",
    response_model=ProductAnalytics,
)
def product_analytics(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    result = db.execute(
        select(
            func.count(Sale.id),
            func.coalesce(func.sum(Sale.quantity_sold), 0),
            func.coalesce(func.avg(Sale.quantity_sold), 0.0),
            func.coalesce(func.avg(Sale.waste_quantity), 0.0),
            func.coalesce(func.sum(Sale.waste_quantity), 0),
        ).where(Sale.product_id == product_id)
    ).one()

    days, total_sold, avg_sold, avg_waste, total_waste = result
    stocked = int(total_sold) + int(total_waste)
    waste_rate = (int(total_waste) / stocked) if stocked else 0.0

    return ProductAnalytics(
        product_id=product_id,
        days_observed=int(days),
        total_quantity_sold=int(total_sold),
        average_daily_demand=round(float(avg_sold), 2),
        average_daily_waste=round(float(avg_waste), 2),
        waste_rate=round(waste_rate, 4),
    )


@router.post("/forecast", response_model=ForecastResponse)
def forecast(payload: ForecastRequest, db: Session = Depends(get_db)):
    product = db.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    rows = db.execute(
        select(Sale)
        .where(Sale.product_id == payload.product_id)
        .order_by(Sale.sale_date)
    ).scalars().all()

    records = [
        {
            "sale_date": row.sale_date,
            "quantity_sold": row.quantity_sold,
        }
        for row in rows
    ]

    try:
        prediction, samples = predict_demand(records, payload.target_date)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return ForecastResponse(
        product_id=payload.product_id,
        target_date=payload.target_date,
        predicted_demand=prediction,
        training_samples=samples,
        model="RandomForestRegressor",
    )
