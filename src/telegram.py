"""
Telegram notification module for Foodikal NY Backend
Sends order notifications to manager via Telegram Bot API
"""
import json
from typing import Dict
from datetime import datetime
import js
from js import fetch, Promise


class TelegramNotifier:
    """Service for sending Telegram notifications"""

    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram notifier

        Args:
            bot_token: Telegram bot token from env.TELEGRAM_BOT_TOKEN
            chat_id: Telegram chat ID from env.TELEGRAM_CHAT_ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    @staticmethod
    def escape_markdown(text: str) -> str:
        """
        Escape special Markdown characters to prevent formatting issues

        Args:
            text: Text that may contain special characters

        Returns:
            Text with escaped Markdown characters
        """
        if not text:
            return text

        # Characters that need escaping in Telegram's legacy Markdown mode
        # Only: _ * ` [
        # Note: () and other chars are only special in MarkdownV2, not in legacy Markdown
        special_chars = ['_', '*', '`', '[']

        escaped_text = text
        for char in special_chars:
            escaped_text = escaped_text.replace(char, f'\\{char}')

        return escaped_text

    def format_order_message(self, order: Dict) -> str:
        """
        Format order data as Telegram message with emoji markers

        Args:
            order: Order dictionary with all fields

        Returns:
            Formatted message string
        """
        # Format order items (escape item names to prevent Markdown issues)
        items_text = []
        for item in order.get('order_items', []):
            item_total = item['price'] * item['quantity']
            escaped_name = self.escape_markdown(item['name'])
            items_text.append(
                f"• {escaped_name} x{item['quantity']} ({item_total} RSD)"
            )

        items_str = "\n".join(items_text)

        # Escape user-provided fields to prevent Markdown formatting issues
        customer_name = self.escape_markdown(order['customer_name'])
        customer_contact = self.escape_markdown(order['customer_contact'])
        delivery_address = self.escape_markdown(order['delivery_address'])

        # Build message
        message = f"""🍽 **Новый заказ #{order['id']}**

👤 Имя: {customer_name}
📞 Контакт: {customer_contact}
📍 Адрес доставки: {delivery_address}
📅 Дата доставки: {order.get('delivery_date', 'Не указана')}

📦 Товары:
{items_str}
"""

        # Add pricing breakdown
        items_subtotal = order.get('items_subtotal', order['total_price'])
        delivery_fee = order.get('delivery_fee', 0)

        message += f"\n💵 Стоимость товаров: {items_subtotal} RSD"

        if delivery_fee > 0:
            message += f"\n🚚 Доставка: {delivery_fee} RSD"

        # Add promo code info if applied
        if order.get('promo_code'):
            escaped_promo = self.escape_markdown(order['promo_code'])
            message += f"\n🎟 Промокод: {escaped_promo}"
            message += f"\n🎁 Скидка: -{order.get('discount_amount', 0)} RSD"

        message += f"\n\n💰 **Итого: {order['total_price']} RSD**"

        if order.get('comments'):
            escaped_comments = self.escape_markdown(order['comments'])
            message += f"\n\n💬 Комментарии: {escaped_comments}"

        # Add timestamp
        created_at = order.get('created_at', datetime.utcnow().isoformat())
        try:
            # Parse and format timestamp
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            formatted_time = dt.strftime('%Y-%m-%d %H:%M')
        except:
            formatted_time = created_at

        message += f"\n\n🕒 Создано: {formatted_time}"

        return message

    async def send_notification(self, order: Dict, max_retries: int = 3) -> bool:
        """
        Send order notification to Telegram with retry logic

        Args:
            order: Order dictionary
            max_retries: Maximum number of retry attempts

        Returns:
            True if sent successfully, False otherwise
        """
        message = self.format_order_message(order)

        for attempt in range(max_retries):
            try:
                # Make HTTP request to Telegram API
                # Use pyodide.ffi.to_js to convert Python dict to JS object
                from pyodide.ffi import to_js

                options = to_js({
                    'method': 'POST',
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'chat_id': self.chat_id,
                        'text': message,
                        'parse_mode': 'Markdown'
                    })
                }, dict_converter=js.Object.fromEntries)

                response = await fetch(self.api_url, options)

                if response.ok:
                    print(f"Telegram notification sent successfully for order #{order['id']}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"Telegram API error (attempt {attempt + 1}/{max_retries}): {error_text}")

            except Exception as e:
                print(f"Telegram notification error (attempt {attempt + 1}/{max_retries}): {str(e)}")

            # Note: In Pyodide environment, we skip the retry delay
            # as asyncio.sleep is not available

        # All retries failed
        print(f"Failed to send Telegram notification for order #{order['id']} after {max_retries} attempts")
        return False


class MockTelegramNotifier:
    """Mock notifier for testing/development"""

    def __init__(self, bot_token: str = "", chat_id: str = ""):
        """Initialize mock notifier"""
        self.bot_token = bot_token
        self.chat_id = chat_id

    def format_order_message(self, order: Dict) -> str:
        """Format message (same as real notifier)"""
        notifier = TelegramNotifier(self.bot_token, self.chat_id)
        return notifier.format_order_message(order)

    async def send_notification(self, order: Dict, max_retries: int = 3) -> bool:
        """Mock send - just logs the message"""
        message = self.format_order_message(order)
        print(f"\n{'='*60}")
        print(f"[MOCK] Telegram notification for order #{order['id']}")
        print(f"{'='*60}")
        print(message)
        print(f"{'='*60}\n")
        return True


def create_notifier(bot_token: str, chat_id: str, environment: str = "production") -> TelegramNotifier:
    """
    Factory function to create appropriate notifier based on environment

    Args:
        bot_token: Telegram bot token
        chat_id: Telegram chat ID
        environment: "production" or "development"

    Returns:
        TelegramNotifier or MockTelegramNotifier
    """
    if environment == "development":
        return MockTelegramNotifier(bot_token, chat_id)
    else:
        return TelegramNotifier(bot_token, chat_id)
