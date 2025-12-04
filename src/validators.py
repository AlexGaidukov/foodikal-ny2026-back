"""
Input validation module for Foodikal NY Backend
"""
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta


class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class OrderValidator:
    """Validator for order-related data"""

    @staticmethod
    def validate_promo_code(code: Optional[str]) -> bool:
        """
        Validate promo code format
        Returns True if valid or if code is None/empty (optional field)
        Allows Latin letters, Cyrillic letters, and numbers
        """
        if not code:
            return True
        # Length check: 3-20 characters
        if len(code) < 3 or len(code) > 20:
            return False
        # Allow Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я, Ё, ё), and numbers (0-9)
        # Pattern allows alphanumeric in both Latin and Cyrillic
        pattern = r'^[A-Za-zА-Яа-яЁё0-9]+$'
        return bool(re.match(pattern, code))

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
        Validate contact field
        Accepts any format with minimum 3 characters
        """
        if not phone or len(phone) < 3:
            return False
        return True

    @staticmethod
    def validate_delivery_date(date_str: str) -> Tuple[bool, str]:
        """
        Validate delivery date
        - Must be in YYYY-MM-DD format
        - Must be today or in the future
        - Must be within 90 days from now

        Returns: (is_valid, error_message)
        """
        if not date_str:
            return False, "Delivery date is required"

        # Validate format
        try:
            delivery_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return False, "Invalid date format. Use YYYY-MM-DD (e.g., 2025-12-31)"

        # Get today's date
        today = datetime.utcnow().date()

        # Check if date is not in the past
        if delivery_date < today:
            return False, "Delivery date cannot be in the past"

        # Check if date is within 90 days
        max_date = today + timedelta(days=90)
        if delivery_date > max_date:
            return False, "Delivery date must be within 90 days from today"

        return True, ""

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
            errors['customer_contact'] = "Customer contact must be at least 3 characters"

        if not data.get('delivery_address'):
            errors['delivery_address'] = "Delivery address is required"

        if not data.get('delivery_date'):
            errors['delivery_date'] = "Delivery date is required"
        else:
            is_valid, msg = OrderValidator.validate_delivery_date(data['delivery_date'])
            if not is_valid:
                errors['delivery_date'] = msg

        if not data.get('order_items'):
            errors['order_items'] = "Order items are required"
        else:
            is_valid, msg = OrderValidator.validate_order_items(data['order_items'])
            if not is_valid:
                errors['order_items'] = msg

        # Optional fields validation
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
        'Салаты',
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


class PromoCodeValidator:
    """Validator for promo code-related data"""

    @staticmethod
    def validate_promo_code_data(data: Dict) -> Tuple[bool, Dict]:
        """
        Validate promo code data for creation
        Returns: (is_valid, error_details)
        """
        errors = {}

        # Required field
        if not data.get('code'):
            errors['code'] = "Promo code is required"
        elif not OrderValidator.validate_promo_code(data['code']):
            errors['code'] = "Promo code must be alphanumeric (Latin/Cyrillic letters and numbers) and 3-20 characters long"

        return len(errors) == 0, errors

    @staticmethod
    def validate_promo_validation_request(data: Dict) -> Tuple[bool, Dict]:
        """
        Validate promo code validation request
        Returns: (is_valid, error_details)
        """
        errors = {}

        # Required field: promo_code
        if not data.get('promo_code'):
            errors['promo_code'] = "Promo code is required"
        elif not OrderValidator.validate_promo_code(data['promo_code']):
            errors['promo_code'] = "Invalid promo code format"

        # Required field: order_items
        if not data.get('order_items'):
            errors['order_items'] = "Order items are required"
        else:
            is_valid, msg = OrderValidator.validate_order_items(data['order_items'])
            if not is_valid:
                errors['order_items'] = msg

        return len(errors) == 0, errors


class BannerValidator:
    """Validator for banner-related data"""

    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate URL format
        Basic validation - checks for http/https and basic structure
        """
        if not url:
            return False

        # Check if starts with http:// or https://
        if not url.startswith('http://') and not url.startswith('https://'):
            return False

        # Basic length check
        if len(url) < 10 or len(url) > 500:
            return False

        return True

    @staticmethod
    def validate_banner_data(data: Dict, is_update: bool = False) -> Tuple[bool, Dict]:
        """
        Validate banner data
        is_update: If True, all fields are optional (partial update)
        Returns: (is_valid, error_details)
        """
        errors = {}

        if not is_update:
            # For creation, these fields are required
            if not data.get('name'):
                errors['name'] = "Banner name is required"
            elif len(data['name']) > 200:
                errors['name'] = "Banner name must not exceed 200 characters"

            if not data.get('item_link'):
                errors['item_link'] = "Item link is required"
            elif not BannerValidator.validate_url(data['item_link']):
                errors['item_link'] = "Item link must be a valid URL (http:// or https://)"

            if not data.get('image_url'):
                errors['image_url'] = "Image URL is required"
            elif not BannerValidator.validate_url(data['image_url']):
                errors['image_url'] = "Image URL must be a valid URL (http:// or https://)"

            if 'display_order' not in data:
                errors['display_order'] = "Display order is required"
            elif not isinstance(data['display_order'], int) or data['display_order'] < 0:
                errors['display_order'] = "Display order must be a non-negative integer"
        else:
            # For update, validate only provided fields
            if 'name' in data:
                if not data['name']:
                    errors['name'] = "Banner name cannot be empty"
                elif len(data['name']) > 200:
                    errors['name'] = "Banner name must not exceed 200 characters"

            if 'item_link' in data and not BannerValidator.validate_url(data['item_link']):
                errors['item_link'] = "Item link must be a valid URL (http:// or https://)"

            if 'image_url' in data and not BannerValidator.validate_url(data['image_url']):
                errors['image_url'] = "Image URL must be a valid URL (http:// or https://)"

            if 'display_order' in data and (not isinstance(data['display_order'], int) or data['display_order'] < 0):
                errors['display_order'] = "Display order must be a non-negative integer"

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
