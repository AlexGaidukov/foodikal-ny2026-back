"""
Database operations module for Foodikal NY Backend
Handles all D1 database interactions with prepared statements
"""
import json
from typing import Dict, List, Optional
from datetime import datetime


class DatabaseError(Exception):
    """Custom exception for database errors"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def js_to_python(obj):
    """Convert JavaScript object to Python dict"""
    import json
    if obj is None:
        return None
    # Convert JS object to JSON string and back to Python dict
    try:
        return json.loads(json.dumps(obj.to_py() if hasattr(obj, 'to_py') else obj))
    except:
        # If conversion fails, return as is
        return obj


def extract_results(result):
    """
    Extract results from D1 query response
    Handles different result formats in Pyodide and converts JS objects to Python dicts
    """
    results = []

    if hasattr(result, 'results'):
        results = result.results or []
    elif isinstance(result, dict) and 'results' in result:
        results = result['results'] or []
    elif isinstance(result, list):
        results = result
    else:
        return []

    # Convert each result from JS object to Python dict
    python_results = []
    for item in results:
        try:
            # Try to convert to Python dict
            if hasattr(item, 'to_py'):
                python_results.append(item.to_py())
            elif hasattr(item, '_obj'):
                # PyProxy object
                python_results.append(dict(item))
            else:
                python_results.append(item)
        except:
            python_results.append(item)

    return python_results


class Database:
    """Wrapper for D1 database operations"""

    def __init__(self, db):
        """
        Initialize database wrapper

        Args:
            db: D1 database binding from env.DB
        """
        self.db = db

    async def get_menu_items(self, category: Optional[str] = None) -> List[Dict]:
        """
        Fetch menu items from database

        Args:
            category: Optional category filter (Cyrillic)

        Returns:
            List of menu items as dictionaries
        """
        try:
            if category:
                # Get items by category
                stmt = self.db.prepare(
                    "SELECT id, name, category, description, price, image FROM menu_items WHERE category = ? ORDER BY name"
                )
                result = await stmt.bind(category).all()
            else:
                # Get all items
                stmt = self.db.prepare(
                    "SELECT id, name, category, description, price, image FROM menu_items ORDER BY category, name"
                )
                result = await stmt.all()

            return extract_results(result)
        except Exception as e:
            print(f"Database error in get_menu_items: {str(e)}")
            raise DatabaseError("Failed to fetch menu items")

    async def get_menu_item_by_id(self, item_id: int) -> Optional[Dict]:
        """
        Fetch a single menu item by ID

        Args:
            item_id: Menu item ID

        Returns:
            Menu item dictionary or None if not found
        """
        try:
            stmt = self.db.prepare(
                "SELECT id, name, category, description, price, image FROM menu_items WHERE id = ?"
            )
            result = await stmt.bind(item_id).first()

            if not result:
                return None

            # Convert JS object to Python dict
            if hasattr(result, 'to_py'):
                return result.to_py()
            elif hasattr(result, '_obj'):
                return dict(result)
            else:
                return result
        except Exception as e:
            print(f"Database error in get_menu_item_by_id: {str(e)}")
            raise DatabaseError(f"Failed to fetch menu item {item_id}")

    async def get_menu_items_by_ids(self, item_ids: List[int]) -> List[Dict]:
        """
        Fetch multiple menu items by IDs

        Args:
            item_ids: List of menu item IDs

        Returns:
            List of menu items
        """
        try:
            # Build placeholders for IN clause
            placeholders = ','.join('?' * len(item_ids))
            query = f"SELECT id, name, category, description, price, image FROM menu_items WHERE id IN ({placeholders})"

            stmt = self.db.prepare(query)
            result = await stmt.bind(*item_ids).all()

            return extract_results(result)
        except Exception as e:
            print(f"Database error in get_menu_items_by_ids: {str(e)}")
            raise DatabaseError("Failed to fetch menu items")

    async def create_order(self, order_data: Dict) -> int:
        """
        Create a new order in database

        Args:
            order_data: Order data dictionary with all fields

        Returns:
            Created order ID
        """
        try:
            stmt = self.db.prepare("""
                INSERT INTO orders (
                    customer_name, customer_contact,
                    delivery_address, delivery_date, comments, order_items,
                    items_subtotal, delivery_fee, total_price,
                    promo_code, original_price, discount_amount
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """)

            result = await stmt.bind(
                order_data['customer_name'],
                order_data['customer_contact'],
                order_data['delivery_address'],
                order_data['delivery_date'],
                order_data['comments'],
                json.dumps(order_data['order_items'], ensure_ascii=False),
                order_data.get('items_subtotal', 0),
                order_data.get('delivery_fee', 0),
                order_data['total_price'],
                order_data.get('promo_code') or '',
                order_data.get('original_price') or order_data['total_price'],
                order_data.get('discount_amount', 0)
            ).run()

            # Get the last inserted row ID
            order_id = result.meta.last_row_id
            return order_id
        except Exception as e:
            print(f"Database error in create_order: {str(e)}")
            raise DatabaseError("Failed to create order")

    async def get_orders(self) -> List[Dict]:
        """
        Fetch all orders, newest first

        Returns:
            List of orders with parsed order_items
        """
        try:
            stmt = self.db.prepare("""
                SELECT id, customer_name, customer_contact,
                       delivery_address, delivery_date, comments, order_items,
                       items_subtotal, delivery_fee, total_price,
                       promo_code, original_price, discount_amount,
                       confirmed_after_creation, confirmed_before_delivery,
                       created_at, updated_at
                FROM orders
                ORDER BY created_at DESC
            """)

            result = await stmt.all()
            orders = extract_results(result)

            # Parse order_items JSON for each order
            for order in orders:
                if order.get('order_items'):
                    try:
                        order['order_items'] = json.loads(order['order_items'])
                    except json.JSONDecodeError:
                        order['order_items'] = []

            return orders
        except Exception as e:
            print(f"Database error in get_orders: {str(e)}")
            raise DatabaseError("Failed to fetch orders")

    async def get_order_by_id(self, order_id: int) -> Optional[Dict]:
        """
        Fetch a single order by ID

        Args:
            order_id: Order ID

        Returns:
            Order dictionary or None if not found
        """
        try:
            stmt = self.db.prepare("""
                SELECT id, customer_name, customer_contact,
                       delivery_address, delivery_date, comments, order_items,
                       items_subtotal, delivery_fee, total_price,
                       promo_code, original_price, discount_amount,
                       confirmed_after_creation, confirmed_before_delivery,
                       created_at, updated_at
                FROM orders
                WHERE id = ?
            """)

            result = await stmt.bind(order_id).first()

            if not result:
                return None

            # Convert JS object to Python dict
            if hasattr(result, 'to_py'):
                order = result.to_py()
            elif hasattr(result, '_obj'):
                order = dict(result)
            else:
                order = result

            if order and order.get('order_items'):
                try:
                    order['order_items'] = json.loads(order['order_items'])
                except json.JSONDecodeError:
                    order['order_items'] = []

            return order
        except Exception as e:
            print(f"Database error in get_order_by_id: {str(e)}")
            raise DatabaseError(f"Failed to fetch order {order_id}")

    async def update_order_confirmations(self, order_id: int, confirmations: Dict) -> bool:
        """
        Update order confirmation flags

        Args:
            order_id: Order ID
            confirmations: Dict with confirmed_after_creation and/or confirmed_before_delivery

        Returns:
            True if updated successfully
        """
        try:
            # Build dynamic UPDATE query based on provided fields
            fields = []
            values = []

            if 'confirmed_after_creation' in confirmations:
                fields.append("confirmed_after_creation = ?")
                values.append(1 if confirmations['confirmed_after_creation'] else 0)

            if 'confirmed_before_delivery' in confirmations:
                fields.append("confirmed_before_delivery = ?")
                values.append(1 if confirmations['confirmed_before_delivery'] else 0)

            if not fields:
                return False

            # Always update updated_at
            fields.append("updated_at = ?")
            values.append(datetime.utcnow().isoformat())

            # Add order_id as last parameter
            values.append(order_id)

            query = f"UPDATE orders SET {', '.join(fields)} WHERE id = ?"
            stmt = self.db.prepare(query)
            await stmt.bind(*values).run()

            return True
        except Exception as e:
            print(f"Database error in update_order_confirmations: {str(e)}")
            raise DatabaseError(f"Failed to update order {order_id}")

    async def delete_order(self, order_id: int) -> bool:
        """
        Delete an order

        Args:
            order_id: Order ID

        Returns:
            True if deleted successfully
        """
        try:
            stmt = self.db.prepare("DELETE FROM orders WHERE id = ?")
            await stmt.bind(order_id).run()
            return True
        except Exception as e:
            print(f"Database error in delete_order: {str(e)}")
            raise DatabaseError(f"Failed to delete order {order_id}")

    async def create_menu_item(self, item_data: Dict) -> int:
        """
        Create a new menu item

        Args:
            item_data: Menu item data

        Returns:
            Created menu item ID
        """
        try:
            stmt = self.db.prepare("""
                INSERT INTO menu_items (name, category, description, price, image)
                VALUES (?, ?, ?, ?, ?)
            """)

            result = await stmt.bind(
                item_data['name'],
                item_data['category'],
                item_data.get('description'),
                item_data['price'],
                item_data.get('image')
            ).run()

            return result.meta.last_row_id
        except Exception as e:
            error_msg = f"Database error in create_menu_item: {str(e)}"
            print(error_msg)
            raise DatabaseError(error_msg)

    async def update_menu_item(self, item_id: int, item_data: Dict) -> bool:
        """
        Update a menu item (partial update)

        Args:
            item_id: Menu item ID
            item_data: Fields to update

        Returns:
            True if updated successfully
        """
        try:
            # Build dynamic UPDATE query
            fields = []
            values = []

            if 'name' in item_data:
                fields.append("name = ?")
                values.append(item_data['name'])

            if 'category' in item_data:
                fields.append("category = ?")
                values.append(item_data['category'])

            if 'description' in item_data:
                fields.append("description = ?")
                values.append(item_data['description'])

            if 'price' in item_data:
                fields.append("price = ?")
                values.append(item_data['price'])

            if 'image' in item_data:
                fields.append("image = ?")
                values.append(item_data['image'])

            if not fields:
                return False

            values.append(item_id)

            query = f"UPDATE menu_items SET {', '.join(fields)} WHERE id = ?"
            stmt = self.db.prepare(query)
            await stmt.bind(*values).run()

            return True
        except Exception as e:
            print(f"Database error in update_menu_item: {str(e)}")
            raise DatabaseError(f"Failed to update menu item {item_id}")

    async def delete_menu_item(self, item_id: int) -> bool:
        """
        Delete a menu item

        Args:
            item_id: Menu item ID

        Returns:
            True if deleted successfully
        """
        try:
            stmt = self.db.prepare("DELETE FROM menu_items WHERE id = ?")
            await stmt.bind(item_id).run()
            return True
        except Exception as e:
            print(f"Database error in delete_menu_item: {str(e)}")
            raise DatabaseError(f"Failed to delete menu item {item_id}")

    async def create_promo_code(self, code: str) -> bool:
        """
        Create a new promo code

        Args:
            code: Promo code string

        Returns:
            True if created successfully
        """
        try:
            stmt = self.db.prepare("INSERT INTO promo_codes (code) VALUES (?)")
            await stmt.bind(code).run()
            return True
        except Exception as e:
            print(f"Database error in create_promo_code: {str(e)}")
            raise DatabaseError("Failed to create promo code")

    async def get_promo_codes(self) -> List[Dict]:
        """
        Fetch all promo codes

        Returns:
            List of promo codes
        """
        try:
            stmt = self.db.prepare("SELECT code, created_at FROM promo_codes ORDER BY created_at DESC")
            result = await stmt.all()
            return extract_results(result)
        except Exception as e:
            print(f"Database error in get_promo_codes: {str(e)}")
            raise DatabaseError("Failed to fetch promo codes")

    async def get_promo_code_by_code(self, code: str) -> Optional[Dict]:
        """
        Fetch a single promo code by code

        Args:
            code: Promo code string

        Returns:
            Promo code dictionary or None if not found
        """
        try:
            stmt = self.db.prepare("SELECT code, created_at FROM promo_codes WHERE code = ?")
            result = await stmt.bind(code).first()

            if not result:
                return None

            # Convert JS object to Python dict
            if hasattr(result, 'to_py'):
                return result.to_py()
            elif hasattr(result, '_obj'):
                return dict(result)
            else:
                return result
        except Exception as e:
            print(f"Database error in get_promo_code_by_code: {str(e)}")
            raise DatabaseError(f"Failed to fetch promo code {code}")

    async def delete_promo_code(self, code: str) -> bool:
        """
        Delete a promo code

        Args:
            code: Promo code string

        Returns:
            True if deleted successfully
        """
        try:
            stmt = self.db.prepare("DELETE FROM promo_codes WHERE code = ?")
            await stmt.bind(code).run()
            return True
        except Exception as e:
            print(f"Database error in delete_promo_code: {str(e)}")
            raise DatabaseError(f"Failed to delete promo code {code}")

    async def get_banners(self) -> List[Dict]:
        """
        Fetch all banners ordered by display_order

        Returns:
            List of banners
        """
        try:
            stmt = self.db.prepare("""
                SELECT id, name, item_link, image_url, display_order, created_at
                FROM banners
                ORDER BY display_order ASC
            """)

            result = await stmt.all()
            return extract_results(result)
        except Exception as e:
            print(f"Database error in get_banners: {str(e)}")
            raise DatabaseError("Failed to fetch banners")

    async def get_banner_by_id(self, banner_id: int) -> Optional[Dict]:
        """
        Fetch a single banner by ID

        Args:
            banner_id: Banner ID

        Returns:
            Banner dictionary or None if not found
        """
        try:
            stmt = self.db.prepare("""
                SELECT id, name, item_link, image_url, display_order, created_at
                FROM banners
                WHERE id = ?
            """)

            result = await stmt.bind(banner_id).first()

            if not result:
                return None

            # Convert JS object to Python dict
            if hasattr(result, 'to_py'):
                return result.to_py()
            elif hasattr(result, '_obj'):
                return dict(result)
            else:
                return result
        except Exception as e:
            print(f"Database error in get_banner_by_id: {str(e)}")
            raise DatabaseError(f"Failed to fetch banner {banner_id}")

    async def create_banner(self, banner_data: Dict) -> int:
        """
        Create a new banner

        Args:
            banner_data: Banner data dictionary

        Returns:
            Created banner ID
        """
        try:
            stmt = self.db.prepare("""
                INSERT INTO banners (name, item_link, image_url, display_order)
                VALUES (?, ?, ?, ?)
            """)

            result = await stmt.bind(
                banner_data['name'],
                banner_data['item_link'],
                banner_data['image_url'],
                banner_data['display_order']
            ).run()

            return result.meta.last_row_id
        except Exception as e:
            print(f"Database error in create_banner: {str(e)}")
            raise DatabaseError("Failed to create banner")

    async def update_banner(self, banner_id: int, banner_data: Dict) -> bool:
        """
        Update a banner (partial update)

        Args:
            banner_id: Banner ID
            banner_data: Fields to update

        Returns:
            True if updated successfully
        """
        try:
            # Build dynamic UPDATE query
            fields = []
            values = []

            if 'name' in banner_data:
                fields.append("name = ?")
                values.append(banner_data['name'])

            if 'item_link' in banner_data:
                fields.append("item_link = ?")
                values.append(banner_data['item_link'])

            if 'image_url' in banner_data:
                fields.append("image_url = ?")
                values.append(banner_data['image_url'])

            if 'display_order' in banner_data:
                fields.append("display_order = ?")
                values.append(banner_data['display_order'])

            if not fields:
                return False

            values.append(banner_id)

            query = f"UPDATE banners SET {', '.join(fields)} WHERE id = ?"
            stmt = self.db.prepare(query)
            await stmt.bind(*values).run()

            return True
        except Exception as e:
            print(f"Database error in update_banner: {str(e)}")
            raise DatabaseError(f"Failed to update banner {banner_id}")

    async def delete_banner(self, banner_id: int) -> bool:
        """
        Delete a banner

        Args:
            banner_id: Banner ID

        Returns:
            True if deleted successfully
        """
        try:
            stmt = self.db.prepare("DELETE FROM banners WHERE id = ?")
            await stmt.bind(banner_id).run()
            return True
        except Exception as e:
            print(f"Database error in delete_banner: {str(e)}")
            raise DatabaseError(f"Failed to delete banner {banner_id}")

    async def get_orders_for_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Fetch orders within a date range with parsed order_items

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List of orders with parsed order_items
        """
        try:
            stmt = self.db.prepare("""
                SELECT id, customer_name, customer_contact,
                       delivery_address, delivery_date, order_items,
                       items_subtotal, delivery_fee, total_price,
                       promo_code, original_price, discount_amount,
                       created_at
                FROM orders
                WHERE delivery_date BETWEEN ? AND ?
                ORDER BY delivery_date, customer_name
            """)

            result = await stmt.bind(start_date, end_date).all()
            orders = extract_results(result)

            # Parse order_items JSON for each order
            for order in orders:
                if order.get('order_items'):
                    try:
                        order['order_items'] = json.loads(order['order_items'])
                    except json.JSONDecodeError:
                        order['order_items'] = []

            return orders
        except Exception as e:
            print(f"Database error in get_orders_for_date_range: {str(e)}")
            raise DatabaseError("Failed to fetch orders for date range")
