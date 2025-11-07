"""
Input validation module for Foodikal NY Backend
"""
import re
from typing import Dict, List, Tuple, Optional


class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class OrderValidator:
    """Validator for order-related data"""

    @staticmethod
    def validate_email(email: Optional[str]) -> bool:
        """
        Validate email format
        Returns True if valid or if email is None/empty (optional field)
        """
        if not email:
            return True
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """
        Validate phone or Telegram handle format
        Accepts: +381641234567 or @telegram_handle
        """
        if not phone or len(phone) < 5:
            return False
        return phone.startswith('+') or phone.startswith('@')

    @staticmethod
    def validate_order_items(items: List[Dict]) -> Tuple[bool, str]:
        """
        Validate order items array
        Returns: (is_valid, error_message)
        """
        if not items or len(items) == 0:
            return False, "Order must contain at least 1 item"

        if len(items) > 20:
            return False, "Maximum 20 different items allowed per order"

        for item in items:
            if 'item_id' not in item:
                return False, "Each item must have 'item_id' field"

            if 'quantity' not in item:
                return False, "Each item must have 'quantity' field"

            if not isinstance(item['quantity'], int) or item['quantity'] <= 0:
                return False, "Quantity must be a positive integer"

            if item['quantity'] > 50:
                return False, "Maximum quantity per item is 50"

        return True, ""

    @staticmethod
    def validate_order_data(data: Dict) -> Tuple[bool, Dict]:
        """
        Validate complete order data
        Returns: (is_valid, error_details)
        """
        errors = {}

        # Required fields
        if not data.get('customer_name'):
            errors['customer_name'] = "Customer name is required"

        if not data.get('customer_contact'):
            errors['customer_contact'] = "Customer contact is required"
        elif not OrderValidator.validate_phone(data['customer_contact']):
            errors['customer_contact'] = "Invalid phone format (use +381... or @username)"

        if not data.get('delivery_address'):
            errors['delivery_address'] = "Delivery address is required"

        if not data.get('order_items'):
            errors['order_items'] = "Order items are required"
        else:
            is_valid, msg = OrderValidator.validate_order_items(data['order_items'])
            if not is_valid:
                errors['order_items'] = msg

        # Optional fields validation
        if data.get('customer_email') and not OrderValidator.validate_email(data['customer_email']):
            errors['customer_email'] = "Invalid email format"

        if data.get('comments') and len(data['comments']) > 500:
            errors['comments'] = "Comments must not exceed 500 characters"

        return len(errors) == 0, errors


class MenuValidator:
    """Validator for menu-related data"""

    VALID_CATEGORIES = [
        'Брускетты',
        'Горячее',
        'Закуски',
        'Канапе',
        'Салат',
        'Тарталетки'
    ]

    @staticmethod
    def validate_category(category: str) -> bool:
        """Validate if category is in allowed list"""
        return category in MenuValidator.VALID_CATEGORIES

    @staticmethod
    def validate_menu_item(data: Dict, is_update: bool = False) -> Tuple[bool, Dict]:
        """
        Validate menu item data
        is_update: If True, all fields are optional (partial update)
        Returns: (is_valid, error_details)
        """
        errors = {}

        if not is_update:
            # For creation, these fields are required
            if not data.get('name'):
                errors['name'] = "Item name is required"

            if not data.get('category'):
                errors['category'] = "Category is required"
            elif not MenuValidator.validate_category(data['category']):
                errors['category'] = f"Invalid category. Must be one of: {', '.join(MenuValidator.VALID_CATEGORIES)}"

            if 'price' not in data:
                errors['price'] = "Price is required"
            elif not isinstance(data['price'], int) or data['price'] < 0:
                errors['price'] = "Price must be a non-negative integer"
        else:
            # For update, validate only provided fields
            if 'category' in data and not MenuValidator.validate_category(data['category']):
                errors['category'] = f"Invalid category. Must be one of: {', '.join(MenuValidator.VALID_CATEGORIES)}"

            if 'price' in data and (not isinstance(data['price'], int) or data['price'] < 0):
                errors['price'] = "Price must be a non-negative integer"

        return len(errors) == 0, errors


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string input
    - Strip leading/trailing whitespace
    - Optionally limit length
    """
    if not value:
        return ""

    sanitized = value.strip()

    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized
