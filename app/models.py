from sqlalchemy import Column, Integer, String, DateTime, Numeric, JSON
from .database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    customer_id = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    price_modifier = Column(Numeric(5, 2), nullable=False)
    final_price = Column(Numeric(10, 2), nullable=False)
    points = Column(Integer, nullable=False)
    payment_method = Column(String, nullable=False)
    datetime = Column(DateTime(timezone=True), nullable=False)
    additional_item = Column(JSON, nullable=True)