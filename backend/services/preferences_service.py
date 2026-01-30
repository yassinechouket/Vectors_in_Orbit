"""
Preferences Service

Manages user preferences including financial info, boycotts, and ethical settings
"""
from typing import Dict, List, Optional
from datetime import datetime

from schemas.preferences import (
    UserPreferences,
    FinancialInfo,
    BrandBoycott,
    EthicalPreferences,
    Priority,
    NotificationSettings
)


class PreferencesService:
    """Manages user preferences and settings"""
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self.preferences: Dict[str, UserPreferences] = {}
    
    def get_preferences(self, user_id: str) -> UserPreferences:
        """
        Get user preferences, creating default if doesn't exist
        
        Args:
            user_id: User identifier
            
        Returns:
            UserPreferences
        """
        if user_id not in self.preferences:
            self.preferences[user_id] = UserPreferences(user_id=user_id)
        
        return self.preferences[user_id]
    
    def update_financial_info(self, user_id: str, info: FinancialInfo) -> None:
        """
        Update user's financial information
        
        Args:
            user_id: User identifier
            info: FinancialInfo to update
        """
        prefs = self.get_preferences(user_id)
        prefs.financial_info = info
        prefs.updated_at = datetime.utcnow()
    
    def add_boycott(self, user_id: str, boycott: BrandBoycott) -> str:
        """
        Add brand boycott
        
        Args:
            user_id: User identifier
            boycott: BrandBoycott to add
            
        Returns:
            Boycott ID
        """
        prefs = self.get_preferences(user_id)
        
        # Check if boycott already exists
        existing = next(
            (b for b in prefs.boycotts if b.brand.lower() == boycott.brand.lower()),
            None
        )
        
        if existing:
            # Update existing
            existing.reason = boycott.reason
            existing.active = boycott.active
            return f"boycott_updated_{boycott.brand}"
        
        prefs.boycotts.append(boycott)
        prefs.updated_at = datetime.utcnow()
        
        return f"boycott_{len(prefs.boycotts)}"
    
    def remove_boycott(self, user_id: str, brand: str) -> bool:
        """
        Remove brand boycott
        
        Args:
            user_id: User identifier
            brand: Brand name to remove
            
        Returns:
            True if removed, False if not found
        """
        prefs = self.get_preferences(user_id)
        
        original_len = len(prefs.boycotts)
        prefs.boycotts = [
            b for b in prefs.boycotts
            if b.brand.lower() != brand.lower()
        ]
        
        if len(prefs.boycotts) < original_len:
            prefs.updated_at = datetime.utcnow()
            return True
        
        return False
    
    def update_ethical_preferences(
        self, 
        user_id: str, 
        ethical_prefs: EthicalPreferences
    ) -> None:
        """
        Update ethical preferences
        
        Args:
            user_id: User identifier
            ethical_prefs: EthicalPreferences to update
        """
        prefs = self.get_preferences(user_id)
        prefs.ethical_preferences = ethical_prefs
        prefs.updated_at = datetime.utcnow()
    
    def set_priority(self, user_id: str, priority: Priority) -> None:
        """
        Set recommendation priority
        
        Args:
            user_id: User identifier
            priority: Priority setting
        """
        prefs = self.get_preferences(user_id)
        prefs.priority = priority
        prefs.updated_at = datetime.utcnow()
    
    def update_notifications(
        self, 
        user_id: str, 
        notifications: NotificationSettings
    ) -> None:
        """
        Update notification settings
        
        Args:
            user_id: User identifier
            notifications: NotificationSettings to update
        """
        prefs = self.get_preferences(user_id)
        prefs.notifications = notifications
        prefs.updated_at = datetime.utcnow()
    
    def get_active_boycotts(self, user_id: str) -> List[str]:
        """
        Get list of boycotted brand names
        
        Args:
            user_id: User identifier
            
        Returns:
            List of brand names
        """
        prefs = self.get_preferences(user_id)
        return [b.brand for b in prefs.boycotts if b.active]
    
    def check_budget_status(
        self, 
        user_id: str, 
        category: str, 
        amount: float
    ) -> Dict[str, any]:
        """
        Check if purchase fits within budget
        
        Args:
            user_id: User identifier
            category: Product category
            amount: Purchase amount
            
        Returns:
            Dict with budget status info
        """
        prefs = self.get_preferences(user_id)
        budgets = prefs.financial_info.budget_categories
        
        if category not in budgets:
            return {
                "has_budget": False,
                "can_afford": True,  # No budget set means no restriction
                "message": f"No budget set for {category}"
            }
        
        budget = budgets[category]
        # In real app, would track current spending
        current_spent = 0  # TODO: Track actual spending
        
        remaining = budget - current_spent
        
        return {
            "has_budget": True,
            "budget": budget,
            "spent": current_spent,
            "remaining": remaining,
            "can_afford": amount <= remaining,
            "message": (
                f"You have ${remaining:.2f} remaining in {category} budget"
                if amount <= remaining
                else f"This exceeds your {category} budget by ${amount - remaining:.2f}"
            )
        }


# Singleton instance
preferences_service = PreferencesService()
