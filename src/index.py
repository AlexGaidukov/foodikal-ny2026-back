"""
Foodikal NY Backend - Main Entry Point
Python backend for restaurant food ordering system on Cloudflare Workers
"""
from js import Response
import asyncio
import json

from database import Database, DatabaseError
from auth import authenticate_request, AuthenticationError
from validators import OrderValidator, MenuValidator, PromoCodeValidator, BannerValidator, ValidationError
from telegram import create_notifier
from rate_limiter import RateLimiter
from utils import (
    json_response,
    error_response,
    decode_category,
    group_menu_by_category,
    calculate_order_total,
    parse_request_body,
    extract_path_param,
    log_event,
    handle_cors_preflight
)


async def handle_get_menu(db: Database, origin: str = None) -> Response:
    """
    GET /api/menu
    Returns all menu items grouped by category
    """
    try:
        menu_items = await db.get_menu_items()
        grouped_menu = group_menu_by_category(menu_items)

        return json_response(grouped_menu, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/menu", "error": str(e)})
        return error_response("Failed to fetch menu", 500, origin=origin)


async def handle_get_menu_by_category(db: Database, category_encoded: str, origin: str = None) -> Response:
    """
    GET /api/menu/category/:category
    Returns menu items for specific category
    """
    try:
        # Decode URL-encoded Cyrillic category
        category = decode_category(category_encoded)

        # Validate category
        if not MenuValidator.validate_category(category):
            return error_response("Invalid category", 404, origin=origin)

        # Fetch items
        items = await db.get_menu_items(category=category)

        return json_response({
            "success": True,
            "category": category,
            "data": items
        }, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/menu/category", "error": str(e)})
        return error_response("Failed to fetch menu category", 500, origin=origin)


async def handle_create_order(request, db: Database, telegram_bot_token: str, telegram_chat_id: str, environment: str, origin: str = None) -> Response:
    """
    POST /api/create_order
    Create new customer order
    """
    try:
        # Parse request body
        try:
            data = await parse_request_body(request)
        except ValueError as e:
            return error_response(str(e), 400, origin=origin)

        # Validate order data
        is_valid, errors = OrderValidator.validate_order_data(data)
        if not is_valid:
            return error_response("Invalid order data", 400, details=errors, origin=origin)

        # Get item IDs from order
        item_ids = [item['item_id'] for item in data['order_items']]

        # Fetch menu items from database to verify they exist and get prices
        menu_items = await db.get_menu_items_by_ids(item_ids)

        # Check if all items exist
        found_ids = {item['id'] for item in menu_items}
        missing_ids = [item_id for item_id in item_ids if item_id not in found_ids]

        if missing_ids:
            return error_response(
                "Menu items not found",
                404,
                details={"invalid_ids": missing_ids},
                origin=origin
            )

        # Create lookup dictionary
        menu_dict = {item['id']: item for item in menu_items}

        # Calculate original price from database prices
        try:
            enriched_items, original_price = calculate_order_total(data['order_items'], menu_dict)
        except ValueError as e:
            return error_response(str(e), 404, origin=origin)

        # Apply promo code discount if provided
        promo_code = None
        discount_amount = 0

        if data.get('promo_code'):
            # Validate promo code format
            if not OrderValidator.validate_promo_code(data['promo_code']):
                return error_response("Invalid promo code format", 400, origin=origin)

            # Check if promo code exists in database
            promo = await db.get_promo_code_by_code(data['promo_code'])
            if not promo:
                return error_response("Promo code not found", 400,
                                    details={"promo_code": "Invalid promo code"}, origin=origin)

            promo_code = data['promo_code']
            # Calculate 5% discount and round final price to nearest 50 RSD
            price_after_discount = original_price - int(original_price * 0.05)
            total_price = round(price_after_discount / 50) * 50
            discount_amount = original_price - total_price

        if not promo_code:
            total_price = original_price

        # Prepare order data for database
        # Convert None to empty string for D1 compatibility in Pyodide
        order_data = {
            'customer_name': data['customer_name'],
            'customer_contact': data['customer_contact'],
            'delivery_address': data['delivery_address'],
            'delivery_date': data['delivery_date'],
            'comments': data.get('comments') or '',
            'order_items': enriched_items,
            'total_price': total_price,
            'promo_code': promo_code,
            'original_price': original_price,
            'discount_amount': discount_amount
        }

        # Save order to database
        order_id = await db.create_order(order_data)

        log_event("order_created", {
            "order_id": order_id,
            "total_price": total_price,
            "items_count": len(enriched_items)
        })

        # Send Telegram notification (non-blocking - don't fail if this fails)
        order_for_telegram = {
            'id': order_id,
            **order_data
        }

        notifier = create_notifier(telegram_bot_token, telegram_chat_id, environment)
        telegram_success = await notifier.send_notification(order_for_telegram)

        log_event("telegram_notification", {
            "order_id": order_id,
            "success": telegram_success
        })

        # Return success response
        response_data = {
            "success": True,
            "order_id": order_id,
            "total_price": total_price,
            "message": "Order created successfully"
        }

        if promo_code:
            response_data["original_price"] = original_price
            response_data["discount_amount"] = discount_amount
            response_data["promo_code"] = promo_code

        return json_response(response_data, status=201, origin=origin)

    except ValidationError as e:
        return error_response(e.message, 400, details=e.details, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/create_order", "error": str(e)})
        return error_response("Failed to create order", 500, origin=origin)

    except Exception as e:
        log_event("unexpected_error", {"endpoint": "/api/create_order", "error": str(e)})
        return error_response("Internal server error", 500, origin=origin)


async def handle_validate_promo(request, db: Database, origin: str = None) -> Response:
    """
    POST /api/validate_promo
    Validate promo code and calculate discount (public endpoint)
    """
    try:
        # Parse request body
        try:
            data = await parse_request_body(request)
        except ValueError as e:
            return error_response(str(e), 400, origin=origin)

        # Validate request data
        is_valid, errors = PromoCodeValidator.validate_promo_validation_request(data)
        if not is_valid:
            return error_response("Invalid request data", 400, details=errors, origin=origin)

        # Fetch all menu items
        menu_items = await db.get_menu_items()
        if not menu_items:
            return error_response("Menu is empty", 400, origin=origin)

        # Create lookup dictionary
        menu_dict = {item['id']: item for item in menu_items}

        # Calculate subtotal from database prices
        try:
            enriched_items, subtotal = calculate_order_total(data['order_items'], menu_dict)
        except ValueError as e:
            return error_response(str(e), 404, origin=origin)

        # Check if promo code exists in database
        promo = await db.get_promo_code_by_code(data['promo_code'])
        if not promo:
            return json_response({
                "success": True,
                "valid": False,
                "error": "Промокод не найден"
            }, origin=origin)

        # Calculate discount with rounding
        price_after_discount = subtotal - int(subtotal * 0.05)
        final_total = round(price_after_discount / 50) * 50
        discount_amount = subtotal - final_total

        # Return success with pricing details
        return json_response({
            "success": True,
            "valid": True,
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "final_total": final_total
        }, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/validate_promo", "error": str(e)})
        return error_response("Failed to validate promo code", 500, origin=origin)

    except Exception as e:
        log_event("unexpected_error", {"endpoint": "/api/validate_promo", "error": str(e)})
        return error_response("Internal server error", 500, origin=origin)


async def handle_get_orders(db: Database, origin: str = None) -> Response:
    """
    GET /api/admin/order_list
    List all orders (admin only)
    """
    try:
        orders = await db.get_orders()

        return json_response({
            "success": True,
            "count": len(orders),
            "orders": orders
        }, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/admin/order_list", "error": str(e)})
        return error_response("Failed to fetch orders", 500, origin=origin)


async def handle_update_order(request, db: Database, order_id: int, origin: str = None) -> Response:
    """
    PATCH /api/admin/orders/:id
    Update order confirmations (admin only)
    """
    try:
        # Parse request body
        try:
            data = await parse_request_body(request)
        except ValueError as e:
            return error_response(str(e), 400, origin=origin)

        # Check if order exists
        order = await db.get_order_by_id(order_id)
        if not order:
            return error_response("Order not found", 404, origin=origin)

        # Extract confirmation flags
        confirmations = {}
        if 'confirmed_after_creation' in data:
            confirmations['confirmed_after_creation'] = bool(data['confirmed_after_creation'])
        if 'confirmed_before_delivery' in data:
            confirmations['confirmed_before_delivery'] = bool(data['confirmed_before_delivery'])

        if not confirmations:
            return error_response("No valid fields to update", 400, origin=origin)

        # Update order
        await db.update_order_confirmations(order_id, confirmations)

        log_event("order_updated", {
            "order_id": order_id,
            "confirmations": confirmations
        })

        # Fetch updated order
        updated_order = await db.get_order_by_id(order_id)

        return json_response({
            "success": True,
            "message": "Order updated successfully",
            "order": updated_order
        }, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/admin/orders/:id", "error": str(e)})
        return error_response("Failed to update order", 500, origin=origin)


async def handle_delete_order(db: Database, order_id: int, origin: str = None) -> Response:
    """
    DELETE /api/admin/orders/:id
    Delete order (admin only)
    """
    try:
        # Check if order exists
        order = await db.get_order_by_id(order_id)
        if not order:
            return error_response("Order not found", 404, origin=origin)

        # Delete order
        await db.delete_order(order_id)

        log_event("order_deleted", {"order_id": order_id})

        return json_response({
            "success": True,
            "message": "Order deleted successfully"
        }, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/admin/orders/:id", "error": str(e)})
        return error_response("Failed to delete order", 500, origin=origin)


async def handle_add_menu_item(request, db: Database, origin: str = None) -> Response:
    """
    POST /api/admin/menu_add
    Add new menu item (admin only)
    """
    try:
        # Parse request body
        try:
            data = await parse_request_body(request)
        except ValueError as e:
            return error_response(str(e), 400, origin=origin)

        # Validate menu item data
        is_valid, errors = MenuValidator.validate_menu_item(data, is_update=False)
        if not is_valid:
            return error_response("Invalid menu item data", 400, details=errors, origin=origin)

        # Create menu item
        item_id = await db.create_menu_item(data)

        log_event("menu_item_created", {"item_id": item_id, "name": data['name']})

        return json_response({
            "success": True,
            "menu_item_id": item_id,
            "message": "Menu item created successfully"
        }, status=201, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/admin/menu_add", "error": str(e)})
        return error_response("Failed to create menu item", 500, origin=origin)


async def handle_update_menu_item(request, db: Database, item_id: int, origin: str = None) -> Response:
    """
    PUT /api/admin/menu_update/:id
    Update menu item (admin only)
    """
    try:
        # Parse request body
        try:
            data = await parse_request_body(request)
        except ValueError as e:
            return error_response(str(e), 400, origin=origin)

        # Check if menu item exists
        item = await db.get_menu_item_by_id(item_id)
        if not item:
            return error_response("Menu item not found", 404, origin=origin)

        # Validate update data
        is_valid, errors = MenuValidator.validate_menu_item(data, is_update=True)
        if not is_valid:
            return error_response("Invalid menu item data", 400, details=errors, origin=origin)

        # Update menu item
        await db.update_menu_item(item_id, data)

        log_event("menu_item_updated", {"item_id": item_id})

        return json_response({
            "success": True,
            "message": "Menu item updated successfully"
        }, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/admin/menu_update/:id", "error": str(e)})
        return error_response("Failed to update menu item", 500, origin=origin)


async def handle_delete_menu_item(db: Database, item_id: int, origin: str = None) -> Response:
    """
    DELETE /api/admin/menu_delete/:id
    Delete menu item (admin only)
    """
    try:
        # Check if menu item exists
        item = await db.get_menu_item_by_id(item_id)
        if not item:
            return error_response("Menu item not found", 404, origin=origin)

        # Delete menu item
        await db.delete_menu_item(item_id)

        log_event("menu_item_deleted", {"item_id": item_id})

        return json_response({
            "success": True,
            "message": "Menu item deleted successfully"
        }, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/admin/menu_delete/:id", "error": str(e)})
        return error_response("Failed to delete menu item", 500, origin=origin)


async def handle_get_promo_codes(db: Database, origin: str = None) -> Response:
    """
    GET /api/admin/promo_codes
    List all promo codes (admin only)
    """
    try:
        promo_codes = await db.get_promo_codes()

        return json_response({
            "success": True,
            "count": len(promo_codes),
            "promo_codes": promo_codes
        }, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/admin/promo_codes", "error": str(e)})
        return error_response("Failed to fetch promo codes", 500, origin=origin)


async def handle_create_promo_code(request, db: Database, origin: str = None) -> Response:
    """
    POST /api/admin/promo_codes
    Create new promo code (admin only)
    """
    try:
        # Parse request body
        try:
            data = await parse_request_body(request)
        except ValueError as e:
            return error_response(str(e), 400, origin=origin)

        # Validate promo code data
        is_valid, errors = PromoCodeValidator.validate_promo_code_data(data)
        if not is_valid:
            return error_response("Invalid promo code data", 400, details=errors, origin=origin)

        # Check if promo code already exists
        existing = await db.get_promo_code_by_code(data['code'])
        if existing:
            return error_response("Promo code already exists", 400,
                                details={"code": "Promo code already exists"}, origin=origin)

        # Create promo code
        await db.create_promo_code(data['code'])

        log_event("promo_code_created", {"code": data['code']})

        return json_response({
            "success": True,
            "code": data['code'],
            "message": "Promo code created successfully"
        }, status=201, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/admin/promo_codes", "error": str(e)})
        return error_response("Failed to create promo code", 500, origin=origin)


async def handle_delete_promo_code(db: Database, code: str, origin: str = None) -> Response:
    """
    DELETE /api/admin/promo_codes/:code
    Delete promo code (admin only)
    """
    try:
        # Check if promo code exists
        promo = await db.get_promo_code_by_code(code)
        if not promo:
            return error_response("Promo code not found", 404, origin=origin)

        # Delete promo code
        await db.delete_promo_code(code)

        log_event("promo_code_deleted", {"code": code})

        return json_response({
            "success": True,
            "message": "Promo code deleted successfully"
        }, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/admin/promo_codes/:code", "error": str(e)})
        return error_response("Failed to delete promo code", 500, origin=origin)


async def handle_get_banners(db: Database, origin: str = None) -> Response:
    """
    GET /api/banners (public)
    Returns all banners ordered by display_order
    """
    try:
        banners = await db.get_banners()

        return json_response({
            "success": True,
            "count": len(banners),
            "banners": banners
        }, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/banners", "error": str(e)})
        return error_response("Failed to fetch banners", 500, origin=origin)


async def handle_get_admin_banners(db: Database, origin: str = None) -> Response:
    """
    GET /api/admin/banners
    List all banners (admin only)
    """
    try:
        banners = await db.get_banners()

        return json_response({
            "success": True,
            "count": len(banners),
            "banners": banners
        }, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/admin/banners", "error": str(e)})
        return error_response("Failed to fetch banners", 500, origin=origin)


async def handle_create_banner(request, db: Database, origin: str = None) -> Response:
    """
    POST /api/admin/banners
    Create new banner (admin only)
    """
    try:
        # Parse request body
        try:
            data = await parse_request_body(request)
        except ValueError as e:
            return error_response(str(e), 400, origin=origin)

        # Validate banner data
        is_valid, errors = BannerValidator.validate_banner_data(data, is_update=False)
        if not is_valid:
            return error_response("Invalid banner data", 400, details=errors, origin=origin)

        # Create banner
        banner_id = await db.create_banner(data)

        log_event("banner_created", {"banner_id": banner_id, "name": data['name']})

        return json_response({
            "success": True,
            "banner_id": banner_id,
            "message": "Banner created successfully"
        }, status=201, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/admin/banners", "error": str(e)})
        return error_response("Failed to create banner", 500, origin=origin)


async def handle_update_banner(request, db: Database, banner_id: int, origin: str = None) -> Response:
    """
    PUT /api/admin/banners/:id
    Update banner (admin only)
    """
    try:
        # Parse request body
        try:
            data = await parse_request_body(request)
        except ValueError as e:
            return error_response(str(e), 400, origin=origin)

        # Check if banner exists
        banner = await db.get_banner_by_id(banner_id)
        if not banner:
            return error_response("Banner not found", 404, origin=origin)

        # Validate update data
        is_valid, errors = BannerValidator.validate_banner_data(data, is_update=True)
        if not is_valid:
            return error_response("Invalid banner data", 400, details=errors, origin=origin)

        # Update banner
        await db.update_banner(banner_id, data)

        log_event("banner_updated", {"banner_id": banner_id})

        # Fetch updated banner
        updated_banner = await db.get_banner_by_id(banner_id)

        return json_response({
            "success": True,
            "message": "Banner updated successfully",
            "banner": updated_banner
        }, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/admin/banners/:id", "error": str(e)})
        return error_response("Failed to update banner", 500, origin=origin)


async def handle_delete_banner(db: Database, banner_id: int, origin: str = None) -> Response:
    """
    DELETE /api/admin/banners/:id
    Delete banner (admin only)
    """
    try:
        # Check if banner exists
        banner = await db.get_banner_by_id(banner_id)
        if not banner:
            return error_response("Banner not found", 404, origin=origin)

        # Delete banner
        await db.delete_banner(banner_id)

        log_event("banner_deleted", {"banner_id": banner_id})

        return json_response({
            "success": True,
            "message": "Banner deleted successfully"
        }, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/admin/banners/:id", "error": str(e)})
        return error_response("Failed to delete banner", 500, origin=origin)


async def handle_get_weekly_workbook_data(db: Database, origin: str = None) -> Response:
    """
    GET /api/admin/weekly_workbook_data
    Returns aggregated order data for weekly Excel workbook generation (Dec 25-31, 2025)
    """
    try:
        START_DATE = "2025-12-25"
        END_DATE = "2025-12-31"

        # Fetch orders for the week
        orders = await db.get_orders_for_date_range(START_DATE, END_DATE)

        # Fetch all menu items
        menu_items = await db.get_menu_items()

        # Create menu items lookup
        menu_dict = {item['id']: item for item in menu_items}

        # Extract unique customers
        customers = sorted(list(set(order['customer_name'] for order in orders)))

        # Aggregate quantities by customer, date, and item_id
        # Structure: {customer: {date: {item_id: quantity}}}
        aggregated_data = {}

        for order in orders:
            customer = order['customer_name']
            date = order['delivery_date']

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

        # Prepare response data
        response_data = {
            "success": True,
            "date_range": {
                "start": START_DATE,
                "end": END_DATE
            },
            "customers": customers,
            "menu_items": menu_items,
            "orders": orders,
            "aggregated_data": aggregated_data
        }

        return json_response(response_data, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/admin/weekly_workbook_data", "error": str(e)})
        return error_response("Failed to fetch weekly workbook data", 500, origin=origin)

    except Exception as e:
        log_event("unexpected_error", {"endpoint": "/api/admin/weekly_workbook_data", "error": str(e)})
        return error_response("Internal server error", 500, origin=origin)


async def handle_generate_weekly_workbook(db: Database, env, origin: str = None) -> Response:
    """
    GET /api/admin/generate_weekly_workbook
    Generates and returns Excel workbook file for the week (Dec 25-31, 2025)
    """
    try:
        START_DATE = "2025-12-25"
        END_DATE = "2025-12-31"

        # Fetch orders for the week
        orders = await db.get_orders_for_date_range(START_DATE, END_DATE)

        # Fetch all menu items
        menu_items = await db.get_menu_items()

        # Extract unique customers
        customers = sorted(list(set(order['customer_name'] for order in orders)))

        # Aggregate quantities by customer, date, and item_id
        aggregated_data = {}

        for order in orders:
            customer = order['customer_name']
            date = order['delivery_date']

            if customer not in aggregated_data:
                aggregated_data[customer] = {}

            if date not in aggregated_data[customer]:
                aggregated_data[customer][date] = {}

            for item in order['order_items']:
                item_id = item['item_id']
                quantity = item['quantity']

                if item_id not in aggregated_data[customer][date]:
                    aggregated_data[customer][date][item_id] = 0

                aggregated_data[customer][date][item_id] += quantity

        # Prepare data for Excel generator
        excel_data = {
            "date_range": {
                "start": START_DATE,
                "end": END_DATE
            },
            "customers": customers,
            "menu_items": menu_items,
            "orders": orders,
            "aggregated_data": aggregated_data
        }

        # Call Excel generator worker via service binding
        excel_generator = getattr(env, 'EXCEL_GENERATOR', None)
        if not excel_generator:
            log_event("excel_generator_error", {"error": "Excel generator service not bound"})
            return error_response("Excel generator service not available", 500, origin=origin)

        # Create request to Excel generator
        # Import Request from js module
        from js import Request as JSRequest
        import pyodide
        import js

        # Convert Python dict to JavaScript object for request options
        request_options = pyodide.ffi.to_js({
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(excel_data, ensure_ascii=False)
        }, dict_converter=js.Object.fromEntries)

        excel_request = JSRequest.new("https://dummy.url/generate", request_options)

        # Call Excel generator
        excel_response = await excel_generator.fetch(excel_request)

        # Check if Excel generation was successful
        if excel_response.status != 200:
            error_text = await excel_response.text()
            log_event("excel_generator_error", {"status": excel_response.status, "error": error_text})
            return error_response("Excel generation failed", 500, origin=origin)

        log_event("workbook_generated", {
            "customers_count": len(customers),
            "orders_count": len(orders)
        })

        # Return the Excel response directly
        # The CORS wrapper will add CORS headers if needed
        return excel_response

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/admin/generate_weekly_workbook", "error": str(e)})
        return error_response("Failed to generate workbook", 500, origin=origin)

    except Exception as e:
        log_event("unexpected_error", {"endpoint": "/api/admin/generate_weekly_workbook", "error": str(e)})
        return error_response("Internal server error", 500, origin=origin)


async def route_request(request, env) -> Response:
    """
    Main request router
    Handles all API endpoints
    """
    url = request.url
    method = request.method

    # Initialize database
    db = Database(env.DB)

    # Initialize rate limiter
    rate_limiter = RateLimiter(getattr(env, 'RATE_LIMIT_KV', None))

    # Get client IP address
    client_ip = request.headers.get('CF-Connecting-IP', 'unknown')

    # Get environment
    environment = getattr(env, 'ENVIRONMENT', 'production')

    # Extract Origin header for CORS
    origin = request.headers.get("Origin")

    # Handle CORS preflight
    if method == "OPTIONS":
        return handle_cors_preflight(origin)

    # Public endpoints
    if method == "GET" and "/api/menu/category/" in url:
        # Rate limit check for menu API
        is_allowed, retry_after = await rate_limiter.check_public_api_rate_limit(client_ip)
        if not is_allowed:
            return error_response(
                "Too many requests. Please try again later.",
                429,
                details={"retry_after": retry_after},
                origin=origin
            )

        category = extract_path_param(url, "/api/menu/category/", "category")
        return await handle_get_menu_by_category(db, category, origin)

    if method == "GET" and url.endswith("/api/menu"):
        # Rate limit check for menu API
        is_allowed, retry_after = await rate_limiter.check_public_api_rate_limit(client_ip)
        if not is_allowed:
            return error_response(
                "Too many requests. Please try again later.",
                429,
                details={"retry_after": retry_after},
                origin=origin
            )

        return await handle_get_menu(db, origin)

    if method == "POST" and url.endswith("/api/create_order"):
        # Rate limit check for order creation
        is_allowed, retry_after = await rate_limiter.check_order_creation_rate_limit(client_ip)
        if not is_allowed:
            return error_response(
                "Too many order attempts. Please try again later.",
                429,
                details={"retry_after": retry_after},
                origin=origin
            )

        return await handle_create_order(
            request, db,
            env.TELEGRAM_BOT_TOKEN,
            env.TELEGRAM_CHAT_ID,
            environment,
            origin
        )

    if method == "POST" and url.endswith("/api/validate_promo"):
        # Rate limit check for promo validation
        is_allowed, retry_after = await rate_limiter.check_promo_validation_rate_limit(client_ip)
        if not is_allowed:
            return error_response(
                "Too many validation attempts. Please try again later.",
                429,
                details={"retry_after": retry_after},
                origin=origin
            )

        return await handle_validate_promo(request, db, origin)

    if method == "GET" and url.endswith("/api/banners"):
        # Rate limit check for banners API
        is_allowed, retry_after = await rate_limiter.check_public_api_rate_limit(client_ip)
        if not is_allowed:
            return error_response(
                "Too many requests. Please try again later.",
                429,
                details={"retry_after": retry_after},
                origin=origin
            )

        return await handle_get_banners(db, origin)

    # Admin endpoints - require authentication
    auth_header = request.headers.get("Authorization")

    # Check authentication for admin endpoints
    if "/api/admin/" in url:
        if not authenticate_request(auth_header, env.ADMIN_PASSWORD_HASH):
            # Record failed authentication attempt and check if rate limited
            is_allowed, retry_after = await rate_limiter.record_failed_auth(client_ip)

            if not is_allowed:
                # Too many failed attempts - rate limit exceeded
                log_event("rate_limit_exceeded", {
                    "endpoint": url,
                    "ip": client_ip,
                    "retry_after": retry_after,
                    "reason": "too_many_failed_auth"
                })
                return error_response(
                    "Too many failed authentication attempts. Please try again later.",
                    429,
                    details={"retry_after": retry_after},
                    origin=origin
                )

            log_event("auth_failed", {
                "endpoint": url,
                "ip": client_ip
            })
            return error_response("Unauthorized", 401, origin=origin)

    # Admin: Order management
    if method == "GET" and url.endswith("/api/admin/order_list"):
        return await handle_get_orders(db, origin)

    if method == "PATCH" and "/api/admin/orders/" in url:
        order_id_str = extract_path_param(url, "/api/admin/orders/", "id")
        try:
            order_id = int(order_id_str)
            return await handle_update_order(request, db, order_id, origin)
        except ValueError:
            return error_response("Invalid order ID", 400, origin=origin)

    if method == "DELETE" and "/api/admin/orders/" in url:
        order_id_str = extract_path_param(url, "/api/admin/orders/", "id")
        try:
            order_id = int(order_id_str)
            return await handle_delete_order(db, order_id, origin)
        except ValueError:
            return error_response("Invalid order ID", 400, origin=origin)

    # Admin: Menu management
    if method == "POST" and url.endswith("/api/admin/menu_add"):
        return await handle_add_menu_item(request, db, origin)

    if method == "PUT" and "/api/admin/menu_update/" in url:
        item_id_str = extract_path_param(url, "/api/admin/menu_update/", "id")
        try:
            item_id = int(item_id_str)
            return await handle_update_menu_item(request, db, item_id, origin)
        except ValueError:
            return error_response("Invalid menu item ID", 400, origin=origin)

    if method == "DELETE" and "/api/admin/menu_delete/" in url:
        item_id_str = extract_path_param(url, "/api/admin/menu_delete/", "id")
        try:
            item_id = int(item_id_str)
            return await handle_delete_menu_item(db, item_id, origin)
        except ValueError:
            return error_response("Invalid menu item ID", 400, origin=origin)

    # Admin: Promo Code management
    if method == "GET" and url.endswith("/api/admin/promo_codes"):
        return await handle_get_promo_codes(db, origin)

    if method == "POST" and url.endswith("/api/admin/promo_codes"):
        return await handle_create_promo_code(request, db, origin)

    if method == "DELETE" and "/api/admin/promo_codes/" in url:
        code = extract_path_param(url, "/api/admin/promo_codes/", "code")
        return await handle_delete_promo_code(db, code, origin)

    # Admin: Banner management
    if method == "GET" and url.endswith("/api/admin/banners"):
        return await handle_get_admin_banners(db, origin)

    if method == "POST" and url.endswith("/api/admin/banners"):
        return await handle_create_banner(request, db, origin)

    if method == "PUT" and "/api/admin/banners/" in url:
        banner_id_str = extract_path_param(url, "/api/admin/banners/", "id")
        try:
            banner_id = int(banner_id_str)
            return await handle_update_banner(request, db, banner_id, origin)
        except ValueError:
            return error_response("Invalid banner ID", 400, origin=origin)

    if method == "DELETE" and "/api/admin/banners/" in url:
        banner_id_str = extract_path_param(url, "/api/admin/banners/", "id")
        try:
            banner_id = int(banner_id_str)
            return await handle_delete_banner(db, banner_id, origin)
        except ValueError:
            return error_response("Invalid banner ID", 400, origin=origin)

    # Admin: Weekly workbook data (JSON)
    if method == "GET" and url.endswith("/api/admin/weekly_workbook_data"):
        return await handle_get_weekly_workbook_data(db, origin)

    # Admin: Generate weekly workbook (Excel file)
    if method == "GET" and url.endswith("/api/admin/generate_weekly_workbook"):
        return await handle_generate_weekly_workbook(db, env, origin)

    # No route matched
    return error_response("Not found", 404, origin=origin)


async def on_fetch(request, env, ctx):
    """
    Main Cloudflare Workers entry point
    Called for every HTTP request
    """
    try:
        return await route_request(request, env)
    except Exception as e:
        # Catch-all error handler
        origin = request.headers.get("Origin")
        log_event("fatal_error", {
            "error": str(e),
            "url": request.url,
            "method": request.method
        })
        return error_response("Internal server error", 500, origin=origin)
