from decimal import Decimal
from dataclasses import dataclass


@dataclass
class PaymentMethodConfig:
    min_modifier: Decimal
    max_modifier: Decimal
    points_rate: Decimal
    required_fields: list[str]
    allowed_values: dict | None = None
    
PAYMENT_METHODS = {
    "CASH": PaymentMethodConfig(
        min_modifier=Decimal("0.9"),
        max_modifier=Decimal("1.0"),
        points_rate=Decimal("0.05"),
        required_fields=[]
    ),
    "CASH_ON_DELIVERY": PaymentMethodConfig(
        min_modifier=Decimal("1.0"),
        max_modifier=Decimal("1.02"),
        points_rate=Decimal("0.05"),
        required_fields=["courier"],
        allowed_values={"courier": ["YAMATO", "SAGAWA"]}
    ),
    "VISA": PaymentMethodConfig(
        min_modifier=Decimal("0.95"),
        max_modifier=Decimal("1.0"),
        points_rate=Decimal("0.03"),
        required_fields=["last4"]
    ),
    "MASTERCARD": PaymentMethodConfig(
        min_modifier=Decimal("0.95"),
        max_modifier=Decimal("1.0"),
        points_rate=Decimal("0.03"),
        required_fields=["last4"]
    ),
    "AMEX": PaymentMethodConfig(
        min_modifier=Decimal("0.98"),
        max_modifier=Decimal("1.01"),
        points_rate=Decimal("0.02"),
        required_fields=["last4"]
    ),
    "JCB": PaymentMethodConfig(
        min_modifier=Decimal("0.95"),
        max_modifier=Decimal("1.0"),
        points_rate=Decimal("0.05"),
        required_fields=["last4"]
    ),
    "LINE_PAY": PaymentMethodConfig(
        min_modifier=Decimal("1.0"),
        max_modifier=Decimal("1.0"),
        points_rate=Decimal("0.01"),
        required_fields=[]
    ),
    "PAYPAY": PaymentMethodConfig(
        min_modifier=Decimal("1.0"),
        max_modifier=Decimal("1.0"),
        points_rate=Decimal("0.01"),
        required_fields=[]
    ),
    "POINTS": PaymentMethodConfig(
        min_modifier=Decimal("1.0"),
        max_modifier=Decimal("1.0"),
        points_rate=Decimal("0.0"),
        required_fields=[]
    ),
    "GRAB_PAY": PaymentMethodConfig(
        min_modifier=Decimal("1.0"),
        max_modifier=Decimal("1.0"),
        points_rate=Decimal("0.01"),
        required_fields=[]
    ),
    "BANK_TRANSFER": PaymentMethodConfig(
        min_modifier=Decimal("1.0"),
        max_modifier=Decimal("1.0"),
        points_rate=Decimal("0.0"),
        required_fields=["bank", "accountNumber"]
    ),
    "CHEQUE": PaymentMethodConfig(
        min_modifier=Decimal("0.9"),
        max_modifier=Decimal("1.0"),
        points_rate=Decimal("0.0"),
        required_fields=["bank", "chequeNumber"]
    ),
}


def validate_payment(
    payment_method: str,
    price_modifier: Decimal,
    additional_fields: dict | None) -> tuple[bool, str | None]:
    """Validate payment method, modifier, and additional fields."""
    
    if payment_method.upper() not in PAYMENT_METHODS:
        return False, f"Invalid payment method: {payment_method}"
        
    config = PAYMENT_METHODS[payment_method]
    
    # Validate price modifier range
    if not (config.min_modifier <= price_modifier <= config.max_modifier):
        return False, (
            f"Price modifier {price_modifier} out of range for {payment_method}. "
            f"Must be between {config.min_modifier} and {config.max_modifier}"
        )
        
    # Validate required fields
    additional_fields = additional_fields or {}
    for field in config.required_fields:
        if field not in additional_fields or not additional_fields[field]:
            return False, f"Missing required field: {field} for {payment_method}"
            
    # Validate last4 format
    if "last4" in config.required_fields:
        last4 = additional_fields.get("last4", "")
        if len(last4) != 4 or not last4.isdigit():
            return False, "last4 must be exactly 4 digits"

    # Validate allowed values
    if config.allowed_values:
        for field, allowed in config.allowed_values.items():
            value = additional_fields.get(field)
            if value not in allowed:
                return False, f"Invalid {field}: {value}. Must be one of: {allowed}"

    return True, None


def calculate_payment(
    payment_method: str,
    price: Decimal,
    price_modifier: Decimal) -> tuple[Decimal, int]:
    """Calculate final_price and points."""

    config = PAYMENT_METHODS[payment_method]

    final_price = (price * price_modifier).quantize(Decimal("0.01"))
    points = int(price * config.points_rate)

    return final_price, points