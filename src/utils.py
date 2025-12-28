"""
Utility functions for Foodikal NY Backend
"""
import json
from typing import Dict, Any, Optional, List
from urllib.parse import unquote, urlparse, parse_qs
from js import Response as JSResponse


# Allowed CORS origins
ALLOWED_ORIGINS = [
    'https://ny2026.foodikal.rs',
    'https://foodikal.rs'
]

# Date range presets for weekly workbook generation
WEEKLY_WORKBOOK_RANGES = {
    'full_week': {
        'start': '2025-12-25',
        'end': '2025-12-31',
        'description': 'Full week (Dec 25-31)'
    },
    'first_half': {
        'start': '2025-12-25',
        'end': '2025-12-28',
        'description': 'First half (Thu-Sun, Dec 25-28)'
    },
    'second_half': {
        'start': '2025-12-29',
        'end': '2025-12-31',
        'description': 'Second half (Mon-Wed, Dec 29-31)'
    }
}

DEFAULT_RANGE = 'full_week'


def get_cors_origin(request_origin: Optional[str] = None) -> str:
    """
    Get the appropriate CORS origin based on the request origin

    Args:
        request_origin: The Origin header from the request

    Returns:
        The origin to use in Access-Control-Allow-Origin header
    """
    if request_origin and request_origin in ALLOWED_ORIGINS:
        return request_origin
    # Default to first allowed origin
    return ALLOWED_ORIGINS[0]


def json_response(data: Any, status: int = 200, success: bool = True, origin: str = None):
    """
    Create JSON response with proper headers for Cyrillic support

    Args:
        data: Response data (will be wrapped in standard format)
        status: HTTP status code
        success: Success flag
        origin: Request origin for CORS (optional)

    Returns:
        Response object with JSON body
    """
    if isinstance(data, dict) and 'success' in data:
        # Data already in response format
        body = data
    else:
        # Wrap data in standard format
        if success:
            body = {"success": True, "data": data}
        else:
            body = {"success": False, "error": data}

    # Determine CORS origin
    cors_origin = get_cors_origin(origin)

    # Return response with headers - simple dictionary approach
    return JSResponse.new(
        json.dumps(body, ensure_ascii=False),
        {
            "status": status,
            "headers": {
                "Content-Type": "application/json; charset=utf-8",
                "Access-Control-Allow-Origin": cors_origin,
                "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        }
    )


def error_response(error: str, status: int = 400, details: Dict = None, origin: str = None):
    """
    Create error response

    Args:
        error: Error message
        status: HTTP status code
        details: Optional error details
        origin: Request origin for CORS (optional)

    Returns:
        Response object with error
    """
    body = {
        "success": False,
        "error": error
    }

    if details:
        body["details"] = details

    return json_response(body, status=status, success=False, origin=origin)


def decode_category(category_encoded: str) -> str:
    """
    Decode URL-encoded Cyrillic category name

    Args:
        category_encoded: URL-encoded category (e.g., %D0%93%D0%BE%D1%80%D1%8F%D1%87%D0%B5%D0%B5)

    Returns:
        Decoded category name (e.g., Горячее)
    """
    return unquote(category_encoded)


def group_menu_by_category(menu_items: list) -> Dict[str, list]:
    """
    Group menu items by category

    Args:
        menu_items: List of menu item dictionaries

    Returns:
        Dictionary with categories as keys and lists of items as values
    """
    categories = [
        'Брускетты',
        'Горячее',
        'Закуски',
        'Канапе',
        'Салаты',
        'Тарталетки'
    ]

    grouped = {cat: [] for cat in categories}

    for item in menu_items:
        category = item.get('category')
        if category in grouped:
            grouped[category].append(item)

    return grouped


def calculate_order_total(order_items: list, menu_items_dict: Dict[int, Dict]) -> tuple:
    """
    Calculate order total from database prices and enrich order items

    CRITICAL: Never trust client prices - always fetch from database

    Args:
        order_items: List of order items with item_id and quantity (can be float for fractional items)
        menu_items_dict: Dictionary of menu items keyed by ID

    Returns:
        Tuple of (enriched_items, total_price)
        enriched_items includes name, price, and unit from database
        total_price is rounded to integer (RSD)
    """
    total = 0.0
    enriched_items = []

    for item in order_items:
        item_id = item['item_id']
        quantity = item['quantity']

        # Get menu item from database
        menu_item = menu_items_dict.get(item_id)
        if not menu_item:
            raise ValueError(f"Menu item {item_id} not found")

        # Calculate item total (handle float quantities)
        price = menu_item['price']
        item_total = price * quantity

        # Create enriched item with unit info
        enriched_item = {
            'item_id': item_id,
            'name': menu_item['name'],
            'quantity': quantity,
            'price': price
        }

        # Include unit if item supports fractional quantities
        if menu_item.get('allow_fractional'):
            enriched_item['unit'] = menu_item.get('unit', 'кг')

        enriched_items.append(enriched_item)
        total += item_total

    # Round total to integer (RSD doesn't have fractional units)
    return enriched_items, int(round(total))


async def parse_request_body(request) -> Dict:
    """
    Parse JSON request body

    Args:
        request: Request object

    Returns:
        Parsed JSON as dictionary

    Raises:
        ValueError if body is not valid JSON
    """
    try:
        body_text = await request.text()
        if not body_text:
            return {}
        return json.loads(body_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in request body: {str(e)}")


def extract_path_param(url: str, pattern: str, param_name: str) -> str:
    """
    Extract path parameter from URL

    Args:
        url: Request URL
        pattern: URL pattern (e.g., "/api/menu/category/")
        param_name: Name of parameter to extract

    Returns:
        Extracted parameter value
    """
    # Simple extraction - find the part after the pattern
    if pattern in url:
        parts = url.split(pattern)
        if len(parts) > 1:
            # Get the part after pattern and remove query string
            param = parts[1].split('?')[0]
            # Remove trailing slash
            return param.rstrip('/')

    return ""


def log_event(event_type: str, data: Dict) -> None:
    """
    Structured logging for important events

    Args:
        event_type: Type of event (e.g., "order_created", "auth_failed")
        data: Event data
    """
    from datetime import datetime

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event_type,
        **data
    }

    print(json.dumps(log_entry, ensure_ascii=False))


def handle_cors_preflight(origin: str = None):
    """
    Handle CORS preflight (OPTIONS) requests

    Args:
        origin: Request origin for CORS (optional)

    Returns:
        Response with CORS headers
    """
    # Determine CORS origin
    cors_origin = get_cors_origin(origin)

    # Return response with headers - simple dictionary approach
    return JSResponse.new(
        None,
        {
            "status": 204,
            "headers": {
                "Access-Control-Allow-Origin": cors_origin,
                "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Max-Age": "86400"
            }
        }
    )


def parse_query_params(url: str) -> Dict[str, str]:
    """
    Parse query parameters from URL

    Args:
        url: Full request URL (e.g., "https://example.com/api/endpoint?range=first_half")

    Returns:
        Dictionary of query parameters

    Example:
        >>> parse_query_params("https://api.com/path?range=first_half&foo=bar")
        {'range': 'first_half', 'foo': 'bar'}
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    # Convert lists to single values (take first value)
    return {key: values[0] if values else '' for key, values in params.items()}


def validate_and_get_date_range(range_param: Optional[str] = None) -> tuple:
    """
    Validate range parameter and return date range tuple

    Args:
        range_param: Range parameter from query string (e.g., 'first_half', 'second_half')
                     If None or empty, returns default full week range

    Returns:
        Tuple of (start_date, end_date, range_name) as strings

    Raises:
        ValueError: If range_param is invalid

    Example:
        >>> validate_and_get_date_range('first_half')
        ('2025-12-25', '2025-12-28', 'first_half')
    """
    # Default to full week if no parameter provided
    if not range_param:
        range_param = DEFAULT_RANGE

    # Validate range exists
    if range_param not in WEEKLY_WORKBOOK_RANGES:
        valid_ranges = ', '.join(WEEKLY_WORKBOOK_RANGES.keys())
        raise ValueError(
            f"Invalid range parameter: '{range_param}'. "
            f"Valid values: {valid_ranges}"
        )

    range_config = WEEKLY_WORKBOOK_RANGES[range_param]
    return (
        range_config['start'],
        range_config['end'],
        range_param
    )


def aggregate_order_data(orders: List[Dict], start_date: str, end_date: str) -> tuple:
    """
    Aggregate order quantities by customer, date, and item_id
    Filters data to only include dates within the specified range

    Args:
        orders: List of order dictionaries from database
        start_date: Start of date range (YYYY-MM-DD)
        end_date: End of date range (YYYY-MM-DD)

    Returns:
        Tuple of (customers_list, aggregated_data_dict)

        customers_list: Sorted list of customer names (only those with orders in range)
        aggregated_data_dict: {customer: {date: {item_id: quantity}}}

    Example:
        orders = [
            {
                'customer_name': 'John',
                'delivery_date': '2025-12-25',
                'order_items': [{'item_id': 1, 'quantity': 2}]
            },
            {
                'customer_name': 'John',
                'delivery_date': '2025-12-29',
                'order_items': [{'item_id': 1, 'quantity': 3}]
            }
        ]

        # First half range
        customers, data = aggregate_order_data(orders, '2025-12-25', '2025-12-28')
        # Returns: (['John'], {'John': {'2025-12-25': {1: 2}}})
        # Note: Dec 29 order excluded (outside range)
    """
    aggregated_data = {}

    for order in orders:
        customer = order['customer_name']
        date = order['delivery_date']

        # CRITICAL: Skip orders outside the date range
        # This ensures only relevant dates are included
        if date < start_date or date > end_date:
            continue

        if customer not in aggregated_data:
            aggregated_data[customer] = {}

        if date not in aggregated_data[customer]:
            aggregated_data[customer][date] = {}

        # Sum quantities for each item
        for item in order['order_items']:
            item_id = item['item_id']
            quantity = item['quantity']

            if item_id not in aggregated_data[customer][date]:
                aggregated_data[customer][date][item_id] = 0

            aggregated_data[customer][date][item_id] += quantity

    # Extract unique customers (only those with orders in date range)
    customers = sorted(list(aggregated_data.keys()))

    return customers, aggregated_data
