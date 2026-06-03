from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    created_at: Optional[datetime] = None
    onboarding_completed: bool = False
    subscription_until: Optional[datetime] = None
    tariff: str = "free"
    id: Optional[int] = None


@dataclass
class UserProfile:
    user_id: int
    work_type: Optional[str] = None
    work_sphere: Optional[str] = None
    income_range: Optional[str] = None
    spending_style: Optional[str] = None
    financial_literacy: Optional[str] = None
    impulsive_spending: Optional[str] = None
    expense_tracking: Optional[str] = None
    debts_status: Optional[str] = None
    salary_end_status: Optional[str] = None
    money_before_salary: Optional[str] = None
    financial_score: int = 0
    main_risk: Optional[str] = None
    id: Optional[int] = None


@dataclass
class Consultation:
    user_id: int
    consultation_type: str
    input_data: str
    ai_response: str
    is_paid: bool = False
    created_at: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class Goal:
    user_id: int
    goal_name: str
    target_amount: float
    monthly_saving: float
    created_at: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class CreditCard:
    user_id: int
    card_name: str
    debt_amount: float
    interest_rate: float
    min_payment: float
    created_at: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class Payment:
    user_id: int
    amount_stars: int
    product_name: str
    status: str = "pending"
    created_at: Optional[datetime] = None
    id: Optional[int] = None
