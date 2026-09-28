from datetime import date, timedelta
from math import sin, pi
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, select

from app.database import Base, SessionLocal, engine
from app.models import Product, Sale

PRODUCTS = [
    ("Chicken Teriyaki Bowl", "Main"),
    ("Vegan Curry", "Main"),
    ("Caesar Salad", "Salad"),
    ("Greek Yogurt & Granola", "Breakfast"),
    ("Protein Snack Box", "Snack"),
]


def demand_for(product_id: int, day_index: int, weekday: int) -> int:
    random.seed(product_id * 10_000 + day_index)

    base = {
        1: 42,
        2: 34,
        3: 29,
        4: 24,
        5: 31,
    }[product_id]

    weekday_effect = {
        0: 5,
        1: 8,
        2: 9,
        3: 6,
        4: -2,
        5: -14,
        6: -16,
    }[weekday]

    seasonal = 4 * sin(2 * pi * day_index / 28)
    noise = random.randint(-4, 4)

    return max(0, round(base + weekday_effect + seasonal + noise))


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        db.execute(delete(Sale))
        db.execute(delete(Product))
        db.commit()

        products = [
            Product(name=name, category=category)
            for name, category in PRODUCTS
        ]
        db.add_all(products)
        db.commit()

        for product in products:
            db.refresh(product)

        start = date.today() - timedelta(days=90)

        for day_index in range(90):
            current = start + timedelta(days=day_index)

            for product in products:
                sold = demand_for(product.id, day_index, current.weekday())

                random.seed(product.id * 20_000 + day_index)
                waste = max(0, round(random.gauss(3, 2)))

                db.add(
                    Sale(
                        product_id=product.id,
                        sale_date=current,
                        quantity_sold=sold,
                        waste_quantity=waste,
                    )
                )

        db.commit()

        count = len(
            db.scalars(select(Sale)).all()
        )
        print(f"Seed complete: {len(products)} products, {count} daily sales rows.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
