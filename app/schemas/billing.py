from pydantic import BaseModel, Field, validator
from typing import List
import re
from datetime import datetime

class PlanFeature(BaseModel):
    description: str

class Plan(BaseModel):
    id: str
    name: str
    price: float
    features: List[PlanFeature]
    currency: str = "USD"

class PlansResponse(BaseModel):
    plans: List[Plan]

class CardInfo(BaseModel):
    card_number: str = Field(..., min_length=15, max_length=16)
    expiration_date: str = Field(..., pattern="^(0[1-9]|1[0-2])/([0-9]{2})$")  # Changed from regex to pattern
    cvv: str = Field(..., min_length=3, max_length=4)
    card_holder_name: str = Field(..., min_length=1)

    @validator('card_number')
    def validate_card_number(cls, v):
        if not v.isdigit():
            raise ValueError('Card number must contain only digits')
        
        # Luhn algorithm for card number validation
        digits = [int(d) for d in v]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(divmod(d * 2, 10))
        if checksum % 10 != 0:
            raise ValueError('Invalid card number')
        return v

    @validator('expiration_date')
    def validate_expiration(cls, v):
        try:
            month, year = map(int, v.split('/'))
            current_year = datetime.now().year % 100
            current_month = datetime.now().month

            if year < current_year or (year == current_year and month < current_month):
                raise ValueError('Card has expired')
        except ValueError as e:
            if str(e) == 'Card has expired':
                raise
            raise ValueError('Invalid expiration date format')
        return v

    @validator('cvv')
    def validate_cvv(cls, v):
        if not v.isdigit():
            raise ValueError('CVV must contain only digits')
        return v

    @validator('card_holder_name')
    def validate_card_holder(cls, v):
        if not re.match("^[a-zA-Z ]+$", v):
            raise ValueError('Card holder name must contain only letters and spaces')
        return v

class SubscriptionRequest(BaseModel):
    plan_id: str
    company_id: str
    card_info: CardInfo

class SubscriptionResponse(BaseModel):
    subscription_id: str
    status: str
    message: str
    plan_id: str
    company_id: str

class UserManagementSubscriptionRequest(BaseModel):
    plan_id: str
    company_id: str