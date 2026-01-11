from datetime import datetime as dt
from decimal import Decimal, InvalidOperation
import strawberry
from typing import Union, Annotated

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from app.database import async_session
from app.models import Payment
from app.payment_methods import validate_payment, calculate_payment


@strawberry.type
class PaymentResponse:
    final_price: str
    points: int


@strawberry.type
class ErrorResponse:
    error: str


@strawberry.type
class SalesEntry:
    datetime: str
    sales: str
    points: int


@strawberry.input
class AdditionalItemInput:
    last4: str | None = None
    courier: str | None = None
    bank: str | None = None
    account_number: str | None = None
    cheque_number: str | None = None


PaymentResult = Annotated[Union[PaymentResponse, ErrorResponse], strawberry.union("PaymentResult")]


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def make_payment(
        self,
        customer_id: str,
        price: str,
        price_modifier: float,
        payment_method: str,
        datetime: str,
        additional_item: AdditionalItemInput | None = None,
    ) -> PaymentResult:
        try:
            price_decimal = None

            # Validate price is in valid format
            try:
                price_decimal = Decimal(price)
            except InvalidOperation:
                return ErrorResponse(error="Invalid price format")

            modifier_decimal = Decimal(str(price_modifier))
            parsed_datetime = dt.fromisoformat(datetime.replace("Z", "+00:00"))
            
            # Convert additional_item to dict
            additional_dict = None
            if additional_item:
                additional_dict = {
                    k: v for k, v in {
                        "last4": additional_item.last4,
                        "courier": additional_item.courier,
                        "bank": additional_item.bank,
                        "accountNumber": additional_item.account_number,
                        "chequeNumber": additional_item.cheque_number,
                    }.items() if v is not None
                }

            # import pdb;pdb.set_trace()

            # Validate customer id
            if customer_id == "":
                return ErrorResponse(error="Customer ID is not provided")

            # Validate price is positive
            if price_decimal < 0:
                return ErrorResponse(error="Price cannot be negative")

            # Validate payment
            is_valid, error = validate_payment(payment_method, modifier_decimal, additional_dict)
            if not is_valid:
                return ErrorResponse(error=error)
            
            # Calculate
            final_price, points = calculate_payment(payment_method, price_decimal, modifier_decimal)
            
            # Save to database
            async with async_session() as session:
                payment = Payment(
                    customer_id=customer_id,
                    price=price_decimal,
                    price_modifier=modifier_decimal,
                    final_price=final_price,
                    points=points,
                    payment_method=payment_method.upper(),
                    datetime=parsed_datetime,
                    additional_item=additional_dict
                )
                session.add(payment)
                await session.commit()
            
            return PaymentResponse(final_price=str(final_price), points=points)
        
        except ValueError as e:
            return ErrorResponse(error=str(e))
        except SQLAlchemyError as e:
            return ErrorResponse(error=f"Database error: {str(e)}")


@strawberry.type
class Query:
    @strawberry.field
    async def sales_report(
        self,
        start_datetime: str,
        end_datetime: str,
    ) -> list[SalesEntry]:
        try:
            start = dt.fromisoformat(start_datetime.replace("Z", "+00:00"))
            end = dt.fromisoformat(end_datetime.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Invalid date format. Use ISO 8601 (e.g., 2022-09-01T00:00:00Z)")
        
        if start > end:
            raise ValueError("Start date must be before end date.")
        
        async with async_session() as session:
            time_bucket = func.date_trunc('hour', Payment.datetime)
            
            query = (
                select(
                    time_bucket.label("datetime"),
                    func.sum(Payment.final_price).label("sales"),
                    func.sum(Payment.points).label("points")
                )
                .where(Payment.datetime >= start)
                .where(Payment.datetime <= end)
                .group_by(time_bucket)
                .order_by(time_bucket)
            )
            
            result = await session.execute(query)
            rows = result.all()
            
            return [
                SalesEntry(
                    datetime=row.datetime.isoformat() + "Z",
                    sales=str(row.sales),
                    points=int(row.points)
                )
                for row in rows
            ]


schema = strawberry.Schema(query=Query, mutation=Mutation)