from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    sales: Mapped[list["Sale"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        UniqueConstraint("product_id", "sale_date", name="uq_product_sale_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
    )
    sale_date: Mapped[date] = mapped_column(Date, index=True)
    quantity_sold: Mapped[int] = mapped_column(Integer)
    waste_quantity: Mapped[int] = mapped_column(Integer, default=0)

    product: Mapped["Product"] = relationship(back_populates="sales")
