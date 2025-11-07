# Foodikal NY Backend - Recommendations & Best Practices

## Implementation Recommendations

### 1. Start with MVP Approach

**Phase 1** (Week 1 - Core Functionality):
- ✅ Setup D1 database with schema
- ✅ Implement `GET /api/menu` endpoint
- ✅ Implement `POST /api/orders` endpoint (without Telegram)
- ✅ Test order creation flow

**Phase 2** (Week 2 - Manager Dashboard):
- ✅ Implement password authentication
- ✅ Implement `GET /api/admin/orders`
- ✅ Implement order update and delete
- ✅ Test admin panel integration

**Phase 3** (Week 3 - Notifications & Polish):
- ✅ Add Telegram webhook integration
- ✅ Add menu management endpoints
- ✅ Final testing and deployment

---

## Code Quality Tips

### 1. Use Type Hints (Python 3.9+)
```python
from typing import Dict, List, Optional

async def create_order(
    customer_name: str,
    customer_contact: str,
    order_items: List[Dict],
    delivery_address: str,
    customer_email: Optional[str] = None,
    comments: Optional[str] = None
) -> Dict:
    """Create new order with proper type hints"""
    pass
```

### 2. Input Validation Helper
```python
class OrderValidator:
    """Centralized validation logic"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        if not email:
            return True  # Optional field
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        # Accept: +381641234567, @telegram_handle
        return len(phone) > 5 and (phone.startswith('+') or phone.startswith('@'))
    
    @staticmethod
    def validate_order_items(items: List[Dict]) -> tuple[bool, str]:
        if not items or len(items) == 0:
            return False, "Order must contain at least 1 item"
        
        if len(items) > 20:
            return False, "Maximum 20 different items allowed"
        
        for item in items:
            if 'item_id' not in item or 'quantity' not in item:
                return False, "Each item must have item_id and quantity"
            
            if item['quantity'] <= 0 or item['quantity'] > 50:
                return False, "Quantity must be between 1 and 50"
        
        return True, ""
```

### 3. Database Query Builder
```python
class Database:
    """D1 database wrapper with prepared statements"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_menu_items(self, category: Optional[str] = None):
        if category:
            stmt = self.db.prepare(
                "SELECT * FROM menu_items WHERE category = ? ORDER BY name"
            )
            result = await stmt.bind(category).all()
        else:
            stmt = self.db.prepare(
                "SELECT * FROM menu_items ORDER BY category, name"
            )
            result = await stmt.all()
        
        return result.get('results', [])
    
    async def create_order(self, order_data: Dict) -> int:
        stmt = self.db.prepare("""
            INSERT INTO orders (
                customer_name, customer_contact, customer_email,
                delivery_address, comments, order_items, total_price
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """)
        
        result = await stmt.bind(
            order_data['customer_name'],
            order_data['customer_contact'],
            order_data.get('customer_email'),
            order_data['delivery_address'],
            order_data.get('comments'),
            json.dumps(order_data['order_items']),
            order_data['total_price']
        ).run()
        
        return result.meta.last_row_id
```

### 3. URL Decoding for Cyrillic Categories
```python
from urllib.parse import unquote

async def get_menu_by_category(request, env):
    """Handle Cyrillic category names in URLs"""
    # Extract category from URL path
    # E.g., /api/menu/category/%D0%93%D0%BE%D1%80%D1%8F%D1%87%D0%B5%D0%B5
    url_path = request.url.split('/')
    category_encoded = url_path[-1]
    
    # Decode URL-encoded Cyrillic
    category = unquote(category_encoded)  # "Горячее"
    
    # Query database with decoded category
    db = Database(env.DB)
    items = await db.get_menu_items(category=category)
    
    if not items:
        return Response(
            json.dumps({"success": False, "error": "Category not found"}, ensure_ascii=False),
            status=404,
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    return Response(
        json.dumps({
            "success": True,
            "category": category,
            "data": items
        }, ensure_ascii=False),  # Preserve Cyrillic in response
        status=200,
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
```

**Important for Cyrillic Support**: 
- Always use `ensure_ascii=False` in `json.dumps()` to preserve Cyrillic characters
- Always include `charset=utf-8` in Content-Type headers
- URL decoding happens automatically in most frameworks, but verify!
- Update `json.dumps()` in create_order to use `ensure_ascii=False` as well

---

## Security Best Practices

### 1. Password Hashing Example
```python
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False

# Generate admin password hash (run once)
def generate_admin_hash():
    """Run once to create admin password hash"""
    password = "your_secure_password_here"  # CHANGE THIS
    hashed = hash_password(password)
    print(f"Hashed password: {hashed}")
    print(f"\nRun this command:")
    print(f"wrangler secret put ADMIN_PASSWORD_HASH")
    print(f"Then paste the hash above")

# In request handler - verify against Cloudflare secret
def check_admin_auth(request, env):
    """Verify admin authentication"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False
    
    password = auth_header.replace("Bearer ", "", 1)
    return verify_password(password, env.ADMIN_PASSWORD_HASH)
```

### 2. Rate Limiting (Simple Implementation)
```python
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = defaultdict(list)
    
    def check_rate_limit(self, ip: str, limit: int = 5, window: int = 60) -> bool:
        """
        Check if IP is within rate limit
        limit: max requests
        window: time window in seconds
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=window)
        
        # Remove old requests
        self.requests[ip] = [
            req_time for req_time in self.requests[ip]
            if req_time > cutoff
        ]
        
        # Check limit
        if len(self.requests[ip]) >= limit:
            return False
        
        self.requests[ip].append(now)
        return True

# Usage in order creation
rate_limiter = RateLimiter()

async def create_order(request, env):
    client_ip = request.headers.get('CF-Connecting-IP', 'unknown')
    
    if not rate_limiter.check_rate_limit(client_ip, limit=5, window=60):
        return Response(
            json.dumps({
                "success": False,
                "error": "Too many requests. Please try again later."
            }),
            status=429,
            headers={"Content-Type": "application/json"}
        )
    
    # Continue with order creation...
```

### 3. SQL Injection Prevention
```python
# ❌ NEVER DO THIS
async def get_order_bad(order_id: str):
    query = f"SELECT * FROM orders WHERE id = {order_id}"  # DANGEROUS!
    result = await db.execute(query)

# ✅ ALWAYS DO THIS
async def get_order_good(order_id: int):
    stmt = db.prepare("SELECT * FROM orders WHERE id = ?")
    result = await stmt.bind(order_id).first()
```

---

## Telegram Integration Tips

### 1. Robust Telegram Notification
```python
import aiohttp
import asyncio

class TelegramNotifier:
    """Telegram notification service with retry logic"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    def format_message(self, order: Dict) -> str:
        """Format order as Telegram message"""
        items_text = "\n".join([
            f"• {item['name']} x{item['quantity']} ({item['price'] * item['quantity']} RSD)"
            for item in order['order_items']
        ])
        
        message = f"""🍽 **New Order #{order['id']}**

👤 Name: {order['customer_name']}
📞 Contact: {order['customer_contact']}"""
        
        if order.get('customer_email'):
            message += f"\n📧 Email: {order['customer_email']}"
        
        message += f"""
📍 Address: {order['delivery_address']}

📦 Items:
{items_text}

💰 Total: {order['total_price']} RSD"""
        
        if order.get('comments'):
            message += f"\n\n💬 Comments: {order['comments']}"
        
        message += f"\n\n🕒 Created: {order['created_at']}"
        
        return message
    
    async def send_notification(self, order: Dict, max_retries: int = 3) -> bool:
        """Send notification with retry logic"""
        message = self.format_message(order)
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.api_url,
                        json={
                            "chat_id": self.chat_id,
                            "text": message,
                            "parse_mode": "Markdown"
                        },
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            return True
                        
                        error_text = await response.text()
                        print(f"Telegram API error: {error_text}")
                        
            except asyncio.TimeoutError:
                print(f"Telegram timeout (attempt {attempt + 1}/{max_retries})")
            except Exception as e:
                print(f"Telegram error: {str(e)}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(1)  # Wait before retry
        
        return False

# Usage
async def create_order_with_notification(order_data: Dict, env):
    # Save order to database
    order_id = await db.create_order(order_data)
    
    # Send Telegram notification (don't fail if this fails)
    notifier = TelegramNotifier(env.TELEGRAM_BOT_TOKEN, env.TELEGRAM_CHAT_ID)
    success = await notifier.send_notification({
        'id': order_id,
        **order_data
    })
    
    if not success:
        print(f"Warning: Failed to send Telegram notification for order #{order_id}")
    
    return order_id
```

### 2. Testing Telegram Without Real Bot
```python
class MockTelegramNotifier:
    """Mock for testing"""
    
    async def send_notification(self, order: Dict) -> bool:
        print(f"[MOCK] Would send Telegram: Order #{order['id']}")
        return True

# Use environment variable to switch
if env.ENVIRONMENT == "development":
    notifier = MockTelegramNotifier()
else:
    notifier = TelegramNotifier(env.TELEGRAM_BOT_TOKEN, env.TELEGRAM_CHAT_ID)
```

---

## Error Handling Patterns

### 1. Custom Exception Classes
```python
class FoodikalException(Exception):
    """Base exception for Foodikal application"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ValidationError(FoodikalException):
    """Input validation error"""
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, status_code=400)
        self.details = details or {}

class AuthenticationError(FoodikalException):
    """Authentication failed"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)

class NotFoundError(FoodikalException):
    """Resource not found"""
    def __init__(self, message: str = "Not found"):
        super().__init__(message, status_code=404)

# Usage
async def get_order(order_id: int):
    order = await db.get_order(order_id)
    if not order:
        raise NotFoundError(f"Order #{order_id} not found")
    return order
```

### 2. Global Error Handler
```python
async def handle_request_with_error_handling(request, env, ctx):
    """Main request handler with error handling"""
    try:
        # Route to appropriate handler
        response = await route_request(request, env)
        return response
        
    except ValidationError as e:
        return Response(
            json.dumps({
                "success": False,
                "error": e.message,
                "details": e.details
            }),
            status=400,
            headers={"Content-Type": "application/json"}
        )
    
    except AuthenticationError as e:
        return Response(
            json.dumps({
                "success": False,
                "error": e.message
            }),
            status=401,
            headers={"Content-Type": "application/json"}
        )
    
    except NotFoundError as e:
        return Response(
            json.dumps({
                "success": False,
                "error": e.message
            }),
            status=404,
            headers={"Content-Type": "application/json"}
        )
    
    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        return Response(
            json.dumps({
                "success": False,
                "error": "Internal server error"
            }),
            status=500,
            headers={"Content-Type": "application/json"}
        )
```

---

## Testing Strategy

### 1. Unit Tests Example
```python
import pytest
from validators import OrderValidator

def test_email_validation():
    assert OrderValidator.validate_email("test@example.com") == True
    assert OrderValidator.validate_email("invalid-email") == False
    assert OrderValidator.validate_email("") == True  # Optional field
    assert OrderValidator.validate_email(None) == True

def test_phone_validation():
    assert OrderValidator.validate_phone("+381641234567") == True
    assert OrderValidator.validate_phone("@telegram_user") == True
    assert OrderValidator.validate_phone("123") == False
    assert OrderValidator.validate_phone("") == False

def test_order_items_validation():
    valid, msg = OrderValidator.validate_order_items([
        {"menu_item_id": 1, "quantity": 2}
    ])
    assert valid == True
    
    valid, msg = OrderValidator.validate_order_items([])
    assert valid == False
    assert "at least 1 item" in msg
```

### 2. Integration Test with curl
```bash
#!/bin/bash
# test_api.sh - Integration testing script

BASE_URL="http://localhost:8787"

echo "Testing GET /api/menu..."
curl -s "$BASE_URL/api/menu" | jq

echo -e "\n\nTesting GET /api/menu/category with Cyrillic (URL encoded)..."
# Category "Горячее" URL-encoded
curl -s "$BASE_URL/api/menu/category/%D0%93%D0%BE%D1%80%D1%8F%D1%87%D0%B5%D0%B5" | jq

echo -e "\n\nTesting POST /api/create_order..."
curl -s -X POST "$BASE_URL/api/create_order" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test User",
    "customer_contact": "+381641234567",
    "customer_email": "test@example.com",
    "delivery_address": "Test Street 123",
    "comments": "Test order",
    "order_items": [
      {"item_id": 1, "quantity": 2}
    ]
  }' | jq

echo -e "\n\nTesting GET /api/admin/order_list (with auth)..."
curl -s "$BASE_URL/api/admin/order_list" \
  -H "Authorization: Bearer your_password_here" | jq

echo -e "\n\nTesting invalid auth..."
curl -s "$BASE_URL/api/admin/order_list" \
  -H "Authorization: Bearer wrong_password" | jq
```

**Note on Cyrillic URLs**: Modern browsers auto-encode Cyrillic, but in scripts you must manually encode:
```bash
# Python helper to encode category names
python3 -c "from urllib.parse import quote; print(quote('Горячее'))"
# Output: %D0%93%D0%BE%D1%80%D1%8F%D1%87%D0%B5%D0%B5
```

### 3. Load Testing (Optional)
```bash
# Using Apache Bench
ab -n 100 -c 10 http://localhost:8787/api/menu

# Using wrk
wrk -t4 -c10 -d30s http://localhost:8787/api/menu
```

---

## Production Deployment Checklist

### Before Deployment
- [ ] Change default admin password
- [ ] Set production Telegram bot token
- [ ] Configure CORS for your frontend domain
- [ ] Test all endpoints in staging environment
- [ ] Review database schema and indexes
- [ ] Enable Cloudflare Analytics
- [ ] Setup error logging/monitoring
- [ ] Document API for frontend team

### After Deployment
- [ ] Test production API endpoints
- [ ] Send test order and verify Telegram notification
- [ ] Test admin dashboard access
- [ ] Monitor logs for first 24 hours
- [ ] Setup backup strategy for D1 database
- [ ] Document deployment process

---

## Database Management Tips

### 1. Backup Strategy
```bash
# Export database to SQL
wrangler d1 export foodikal_ny_db --output=backup-$(date +%Y%m%d).sql

# Schedule daily backups (cron job)
0 2 * * * /usr/local/bin/wrangler d1 export foodikal_ny_db --output=/backups/foodikal-ny-$(date +\%Y\%m\%d).sql
```

### 2. Migration Script Template
```sql
-- migrations/001_add_order_notes.sql
-- Add notes field to orders table

ALTER TABLE orders ADD COLUMN manager_notes TEXT;

-- Create index if needed
CREATE INDEX IF NOT EXISTS idx_orders_notes ON orders(manager_notes);
```

### 3. Data Seeding Script
```sql
-- seed_menu.sql
-- Insert sample menu items for testing

INSERT INTO menu_items (name, category, description, price, image) VALUES
('Брускетта с вяленой свининой (60г)', 'Брускетты', 'Хлеб, вяленая свинина, соус', 300, 'images/bruschetta-pork.jpg'),
('Брускетта с гравлаксом (60г)', 'Брускетты', 'Хлеб, гравлакс, соус', 220, 'images/bruschetta-gravlax.jpg'),
('Баранья нога (запеченая, 1780г)', 'Горячее', 'Баранья нога, запеченная с травами', 15500, 'images/lamb-leg.jpg'),
('Куриный шашлычок с картофелем фри (200г)', 'Горячее', 'Курица, картофель, специи', 550, 'images/chicken-skewer.jpg'),
('Ассорти сыров и мясных деликатесов (300г)', 'Закуски', 'Разные сыры и мясные деликатесы', 2000, 'images/cheese-meat-platter.jpg'),
('Канапе овощное (45г)', 'Канапе', 'Хлеб, овощи', 75, 'images/canape-vegetable.jpg'),
('Канапе с грушей и пршутом (25г)', 'Канапе', 'Хлеб, груша, пршут', 140, 'images/canape-pear.jpg');
```

---

## Performance Optimization

### 1. Response Caching (if menu rarely changes)
```python
from datetime import datetime, timedelta

class CachedMenuService:
    """Cache menu items to reduce database queries"""
    
    def __init__(self):
        self.cache = None
        self.cache_time = None
        self.cache_ttl = timedelta(hours=1)
    
    async def get_menu(self, db):
        now = datetime.now()
        
        # Return cached if still valid
        if self.cache and self.cache_time:
            if now - self.cache_time < self.cache_ttl:
                return self.cache
        
        # Fetch from database
        items = await db.get_menu_items()
        
        # Update cache
        self.cache = items
        self.cache_time = now
        
        return items

# Global instance
menu_service = CachedMenuService()
```

### 2. Database Query Optimization
```sql
-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_menu_category ON menu_items(category);
CREATE INDEX IF NOT EXISTS idx_orders_confirmations ON orders(confirmed_after_creation, confirmed_before_delivery);

-- Query with index hint
SELECT * FROM orders 
WHERE confirmed_after_creation = 1 
ORDER BY created_at DESC 
LIMIT 50;
```

---

## Monitoring & Alerting

### 1. Key Metrics to Track
- Order creation rate (per hour/day)
- API response times
- Error rate (4xx, 5xx)
- Telegram notification success rate
- Database query duration
- Failed authentication attempts

### 2. Simple Logging
```python
import json
from datetime import datetime

def log_event(event_type: str, data: Dict):
    """Structured logging for Cloudflare Workers"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event_type,
        **data
    }
    print(json.dumps(log_entry))

# Usage
log_event("order_created", {
    "order_id": 42,
    "total_price": 7050,
    "items_count": 3,
    "telegram_sent": True
})

log_event("auth_failed", {
    "ip": request.headers.get('CF-Connecting-IP'),
    "endpoint": "/api/admin/orders"
})
```

### 3. Health Check Endpoint
```python
async def health_check(env):
    """System health check"""
    checks = {
        "database": False,
        "telegram": False
    }
    
    # Test database
    try:
        result = await env.DB.prepare("SELECT 1").first()
        checks["database"] = result is not None
    except Exception as e:
        print(f"Database health check failed: {e}")
    
    # Test Telegram (optional)
    try:
        # Ping Telegram API
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{env.TELEGRAM_BOT_TOKEN}/getMe"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                checks["telegram"] = resp.status == 200
    except Exception as e:
        print(f"Telegram health check failed: {e}")
    
    all_healthy = all(checks.values())
    
    return Response(
        json.dumps({
            "status": "healthy" if all_healthy else "degraded",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }),
        status=200 if all_healthy else 503,
        headers={"Content-Type": "application/json"}
    )
```

---

## Cost Estimation

### Cloudflare Workers Pricing (Free Tier)
- **Requests**: 100,000 per day (FREE)
- **D1 Database**: 
  - Storage: 5GB (FREE)
  - Reads: 5M per day (FREE)
  - Writes: 100k per day (FREE)

### Expected Usage
- **Menu requests**: ~100/day
- **Order creation**: ~3/day
- **Admin requests**: ~20/day
- **Total**: ~123 requests/day

**Conclusion**: Your application will easily fit within FREE tier limits! 🎉

### Paid Features (if needed later)
- Custom domain: $0.50/month
- Analytics retention: $5/month
- Advanced logging: Variable

---

## Common Pitfalls to Avoid

### 1. ❌ Not Validating Input
```python
# Bad: Trusting user input
total = sum([item['price'] for item in order_items])

# Good: Fetch prices from database
items = await db.get_items_by_ids(item_ids)
total = sum([item['price'] * quantity for item, quantity in zip(items, quantities)])
```

### 2. ❌ Exposing Sensitive Data
```python
# Bad: Returning password hash
return {"user": {"id": 1, "password_hash": "..."}}

# Good: Filter sensitive fields
return {"user": {"id": 1, "name": "Admin"}}
```

### 3. ❌ Not Handling Timezones
```python
# Bad: Using local time
created_at = datetime.now()  # Ambiguous timezone

# Good: Always use UTC
from datetime import datetime, timezone
created_at = datetime.now(timezone.utc).isoformat()
```

### 4. ❌ Ignoring CORS
```python
# Bad: No CORS headers
return Response(json.dumps(data))

# Good: Include CORS headers
return Response(
    json.dumps(data),
    headers={
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "https://ny2026.foodikal.rs",
        "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    }
)
```

---

## Additional Resources

### Documentation
- Cloudflare Workers: https://developers.cloudflare.com/workers/
- D1 Database: https://developers.cloudflare.com/d1/
- Wrangler CLI: https://developers.cloudflare.com/workers/wrangler/
- Python on Workers: https://developers.cloudflare.com/workers/languages/python/

### Useful Tools
- **Postman**: API testing
- **Insomnia**: API testing alternative
- **DB Browser for SQLite**: View D1 database locally
- **Telegram Bot API**: https://core.telegram.org/bots/api

### Community
- Cloudflare Discord: https://discord.gg/cloudflaredev
- Cloudflare Community: https://community.cloudflare.com/

---

## Next Steps

1. **Review specification document** - Make sure all requirements are clear
2. **Setup development environment** - Install Wrangler, Python, dependencies
3. **Create D1 database** - Initialize schema
4. **Start with MVP** - Implement core features first
5. **Test thoroughly** - Use provided test scripts
6. **Deploy to production** - Follow deployment checklist
7. **Monitor & iterate** - Track usage, fix issues, add features

Good luck with your Foodikal NY project! 🍽️🚀

---

## Questions or Issues?

If you encounter any problems during implementation:

1. Check Cloudflare Workers logs: `wrangler tail`
2. Test endpoints locally: `wrangler dev`
3. Verify database schema: `wrangler d1 execute foodikal_ny_db --command="SELECT * FROM sqlite_master"`
4. Review error messages carefully
5. Consult Cloudflare documentation
6. Ask in Cloudflare Discord community

**Remember**: Start simple, test often, deploy confidently! ✨
