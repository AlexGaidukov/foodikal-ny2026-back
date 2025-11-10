"""
Foodikal NY Backend - Main Entry Point
Python backend for restaurant food ordering system on Cloudflare Workers
"""
from js import Response, fetch
import asyncio

from database import Database, DatabaseError
from auth import authenticate_request, AuthenticationError
from validators import OrderValidator, MenuValidator, ValidationError
from telegram import create_notifier
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

        # Calculate total price from database prices
        try:
            enriched_items, total_price = calculate_order_total(data['order_items'], menu_dict)
        except ValueError as e:
            return error_response(str(e), 404, origin=origin)

        # Prepare order data for database
        # Convert None to empty string for D1 compatibility in Pyodide
        order_data = {
            'customer_name': data['customer_name'],
            'customer_contact': data['customer_contact'],
            'customer_email': data.get('customer_email') or '',
            'delivery_address': data['delivery_address'],
            'comments': data.get('comments') or '',
            'order_items': enriched_items,
            'total_price': total_price
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
        return json_response({
            "success": True,
            "order_id": order_id,
            "total_price": total_price,
            "message": "Order created successfully"
        }, status=201, origin=origin)

    except ValidationError as e:
        return error_response(e.message, 400, details=e.details, origin=origin)

    except DatabaseError as e:
        log_event("database_error", {"endpoint": "/api/create_order", "error": str(e)})
        return error_response("Failed to create order", 500, origin=origin)

    except Exception as e:
        log_event("unexpected_error", {"endpoint": "/api/create_order", "error": str(e)})
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


async def route_request(request, env) -> Response:
    """
    Main request router
    Handles all API endpoints
    """
    url = request.url
    method = request.method

    # Initialize database
    db = Database(env.DB)

    # Get environment
    environment = getattr(env, 'ENVIRONMENT', 'production')

    # Extract Origin header for CORS
    origin = request.headers.get("Origin")

    # Handle CORS preflight
    if method == "OPTIONS":
        return handle_cors_preflight(origin)

    # Public endpoints
    if method == "GET" and "/api/menu/category/" in url:
        category = extract_path_param(url, "/api/menu/category/", "category")
        return await handle_get_menu_by_category(db, category, origin)

    if method == "GET" and url.endswith("/api/menu"):
        return await handle_get_menu(db, origin)

    if method == "POST" and url.endswith("/api/create_order"):
        return await handle_create_order(
            request, db,
            env.TELEGRAM_BOT_TOKEN,
            env.TELEGRAM_CHAT_ID,
            environment,
            origin
        )

    # Admin endpoints - require authentication
    auth_header = request.headers.get("Authorization")

    # Check authentication for admin endpoints
    if "/api/admin/" in url:
        if not authenticate_request(auth_header, env.ADMIN_PASSWORD_HASH):
            log_event("auth_failed", {
                "endpoint": url,
                "ip": request.headers.get('CF-Connecting-IP', 'unknown')
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
