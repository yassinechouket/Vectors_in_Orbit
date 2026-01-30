"""
Pydantic models for user preferences
"""
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class Priority(str, Enum):
    """Recommendation priority options"""
    PRICE = "price"
    QUALITY = "quality"
    SPEED = "speed"
    SUSTAINABILITY = "sustainability"


class FinancialInfo(BaseModel):
    """User financial information"""
    monthly_income: float = Field(default=0, ge=0, description="Monthly income")
    budget_categories: Dict[str, float] = Field(
        default_factory=dict,
        description="Budget per category: {category: amount}"
    )
    savings_goal: float = Field(default=0, ge=0, description="Monthly savings target")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "monthly_income": 3500,
                "budget_categories": {
                    "Electronics": 500,
                    "Clothing": 200,
                    "Home & Kitchen": 300
                },
                "savings_goal": 1000
            }
        }


class BrandBoycott(BaseModel):
    """Brand boycott entry"""
    brand: str = Field(..., description="Brand name to boycott")
    reason: str = Field(..., description="Reason for boycott")
    added_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = Field(default=True, description="Whether boycott is currently active")


class EthicalPreferences(BaseModel):
    """Ethical shopping preferences"""
    eco_friendly: bool = Field(default=False, description="Require eco-certified products")
    fair_trade: bool = Field(default=False, description="Require fair trade certification")
    cruelty_free: bool = Field(default=False, description="No animal testing")
    local_first: bool = Field(default=False, description="Prioritize local products")
    sustainable_materials: bool = Field(default=False, description="Require sustainable materials")


class NotificationSettings(BaseModel):
    """User notification preferences"""
    price_drops: bool = Field(default=True)
    stock_alerts: bool = Field(default=True)
    budget_warnings: bool = Field(default=True)
    new_deals: bool = Field(default=False)
    weekly_summary: bool = Field(default=True)


class UserPreferences(BaseModel):
    """Complete user preferences"""
    user_id: str = Field(..., description="User identifier")
    financial_info: FinancialInfo = Field(default_factory=FinancialInfo)
    boycotts: List[BrandBoycott] = Field(default_factory=list)
    ethical_preferences: EthicalPreferences = Field(default_factory=EthicalPreferences)
    priority: Priority = Field(default=Priority.PRICE)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
