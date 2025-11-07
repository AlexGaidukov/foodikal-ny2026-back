# Foodikal NY Backend - Project Context

## Project Overview
**Foodikal NY** is a food ordering system for a restaurant. Customers browse menu items on a landing page, select dishes with quantities, provide contact information, and place orders without authentication or payment. Managers receive Telegram notifications and confirm orders manually via a protected admin dashboard.

**Scale**: ~100 orders over 1.5 months (low traffic)  
**Language**: Application serves Russian-speaking users (Cyrillic text)

---

## Tech Stack

### Core
- **Backend**: Python on Cloudflare Workers
- **Database**: Cloudflare D1 (SQLite)
- **Deployment**: Wrangler CLI
- **Authentication**: Simple password (bcrypt-hashed) stored in Cloudflare Secrets
- **Notifications**: Telegram Bot API

### Dependencies
```
bcrypt>=4.0.0
```

---

## Architecture

### Database Schema (2 tables)
```sql
-- Table 1: Menu items
menu_items (id, name, category, description, price, image, created_at)

-- Table 2: Customer orders
orders (id, customer_name, customer_contact, customer_email, delivery_address, 
        comments, order_items, total_price, confirmed_after_creation, 
        confirmed_before_delivery, created_at, updated_at)
```

**Important**: 
- Only 2 tables (NO admin_credentials table)
- `order_items` is JSON string with format: `[{"item_id": 1, "name": "...", "quantity": 2, "price": 3100}]`
- Menu items use `description` (not `ingredients`) and `image` (not `photo_url`)
- Item names include weight: "Брускетта с вяленой свининой (60г)"

### API Endpoints
#### Public (No Auth)
- `GET /api/menu` - Get all menu items
- `GET /api/menu/category/:category` - Get items by category
- `POST /api/create_order` - Create new order

#### Admin (Password Protected)
- `GET /api/admin/order_list` - List all orders
- `PATCH /api/admin/orders/:id` - Update order confirmations
- `DELETE /api/admin/orders/:id` - Delete order

#### Optional (Admin)
- `POST /api/admin/menu_add` - Add menu item
- `PUT /api/admin/menu_update/:id` - Update menu item
- `DELETE /api/admin/menu_delete/:id` - Delete menu item

---

## Critical Conventions

### 1. Field Naming
✅ **ALWAYS use `item_id`** (not `menu_item_id`)
```json
{"item_id": 1, "quantity": 2}
```

### 2. Cyrillic Support
**Categories**: Брускетты, Горячее, Закуски, Канапе, Салат, Тарталетки

**URL Encoding Required**:
```python
from urllib.parse import unquote

# URLs come encoded: /api/menu/category/%D0%93%D0%BE%D1%80%D1%8F%D1%87%D0%B5%D0%B5
category = unquote(category_param)  # Decodes to "Горячее"
```

**JSON Responses**:
```python
# ALWAYS preserve Cyrillic characters
json.dumps(data, ensure_ascii=False)

# ALWAYS include charset
headers={"Content-Type": "application/json; charset=utf-8"}
```

### 3. Secrets Management
**All sensitive data in Cloudflare Secrets** (NOT in database or wrangler.toml):
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `ADMIN_PASSWORD_HASH`

Access via `env` object:
```python
async def handle_request(request, env, ctx):
    token = env.TELEGRAM_BOT_TOKEN
    chat_id = env.TELEGRAM_CHAT_ID
    admin_hash = env.ADMIN_PASSWORD_HASH
```

### 4. Authentication
```python
import bcrypt

# Verify against Cloudflare secret
def verify_password(provided: str, env) -> bool:
    return bcrypt.checkpw(
        provided.encode('utf-8'),
        env.ADMIN_PASSWORD_HASH.encode('utf-8')
    )

# Extract from header
auth = request.headers.get("Authorization", "")
password = auth.replace("Bearer ", "", 1)
```

---

## Data Flow

### Order Creation Flow
1. Frontend sends POST to `/api/create_order` with customer info + items
2. Backend validates all fields
3. Verify all `item_id` exist in `menu_items` table
4. Calculate `total_price` from database prices (don't trust frontend)
5. Store order in database
6. **Immediately** send Telegram notification
7. Return order_id + total_price to frontend

### Telegram Notification Format
```
🍽 **New Order #42**

👤 Name: Иван Петров
📞 Contact: +381641234567
📧 Email: ivan@example.com
📍 Address: Улица Пушкина, дом 5

📦 Items:
• Свиная рулька x2 (6200 RSD)
• Брускетта с томатами x1 (850 RSD)

💰 Total: 7050 RSD

💬 Comments: Позвоните за 30 минут

🕒 Created: 2025-11-06 14:30
```

**Important**: 
- Send only for NEW orders (not updates/deletions)
- If Telegram fails, log error but don't fail order creation

---

## Security Requirements

### Input Validation
- Max 20 items per order
- Max 50 quantity per item
- Max 500 chars for comments
- Email format validation (if provided)
- Phone/Telegram format: `+381...` or `@username`

### SQL Injection Prevention
```python
# ✅ ALWAYS use parameterized queries
stmt = db.prepare("SELECT * FROM orders WHERE id = ?")
result = await stmt.bind(order_id).first()

# ❌ NEVER concatenate
query = f"SELECT * FROM orders WHERE id = {order_id}"  # DANGEROUS!
```

### CORS
```python
headers = {
    "Access-Control-Allow-Origin": "https://ny2026.foodikal.rs",
    "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE",
    "Access-Control-Allow-Headers": "Content-Type, Authorization"
}
```

---

## Common Patterns

### Error Response Format
```json
{
    "success": false,
    "error": "Human-readable message",
    "details": {}  // Optional
}
```

### Success Response Format
```json
{
    "success": true,
    "data": [...],
    "message": "Optional message"
}
```

### Database Query Pattern
```python
# With parameters
stmt = env.DB.prepare("SELECT * FROM menu_items WHERE category = ?")
result = await stmt.bind(category).all()

# Get results
items = result.get('results', [])
```

---

## Deployment Commands

```bash
# Setup
wrangler d1 create foodikal_ny_db
wrangler d1 execute foodikal_ny_db --file=./schema.sql

# Set secrets
wrangler secret put TELEGRAM_BOT_TOKEN
wrangler secret put TELEGRAM_CHAT_ID
wrangler secret put ADMIN_PASSWORD_HASH

# Deploy
wrangler dev              # Local testing
wrangler deploy          # Production
wrangler tail            # View logs
```

---

## File Structure
```
foodikal-ny-backend/
├── src/
│   ├── index.py          # Main entry point, routing
│   ├── database.py       # D1 operations
│   ├── auth.py           # Password verification
│   ├── telegram.py       # Telegram notifications
│   ├── validators.py     # Input validation
│   └── utils.py          # Helpers
├── schema.sql            # Database initialization
├── requirements.txt      # Python dependencies
├── wrangler.toml        # Cloudflare config
└── README.md            # Setup instructions
```

---

## Testing Checklist

- [ ] Menu retrieval works (all + by category)
- [ ] Category URLs decode Cyrillic correctly
- [ ] Order creation validates all fields
- [ ] Total price calculated from DB, not frontend
- [ ] Telegram notification sent and formatted correctly
- [ ] Invalid password returns 401
- [ ] Valid password accesses admin endpoints
- [ ] Can update order confirmations
- [ ] Can delete orders
- [ ] SQL injection attempts blocked
- [ ] Cyrillic text preserved in responses

---

## Common Mistakes to Avoid

1. ❌ Using `menu_item_id` instead of `item_id`
2. ❌ Not decoding Cyrillic category URLs
3. ❌ Using `ensure_ascii=True` (loses Cyrillic)
4. ❌ Storing secrets in wrangler.toml or database
5. ❌ Trusting frontend price calculations
6. ❌ Failing order if Telegram fails
7. ❌ String concatenation in SQL queries
8. ❌ Missing `charset=utf-8` in Content-Type

---

## Quick Reference

### Test Category URL Encoding
```bash
# Encode Cyrillic
python3 -c "from urllib.parse import quote; print(quote('Горячее'))"
# Output: %D0%93%D0%BE%D1%80%D1%8F%D1%87%D0%B5%D0%B5

# Test endpoint
curl "http://localhost:8787/api/menu/category/%D0%93%D0%BE%D1%80%D1%8F%D1%87%D0%B5%D0%B5"
```

### Generate Password Hash
```bash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'YOUR_PASSWORD', bcrypt.gensalt(12)).decode())"
```

### Test Order Creation
```bash
curl -X POST http://localhost:8787/api/create_order \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test",
    "customer_contact": "+381641234567",
    "delivery_address": "Test Street 123",
    "order_items": [{"item_id": 1, "quantity": 2}]
  }'
```

---

## Documentation Files

1. **foodikal_backend_specification.md** - Complete API specification with all endpoints, schemas, and requirements
2. **foodikal_recommendations.md** - Implementation best practices, code examples, security patterns
3. **CLAUDE.md** - This file (project context)

---

## Project Status

✅ **Specification Complete** - Ready for implementation  
📋 **Database Schema** - 2 tables defined  
🔐 **Security Model** - Cloudflare Secrets + bcrypt  
🌐 **Internationalization** - Cyrillic support configured  
📱 **Notifications** - Telegram integration specified  

**Next Step**: Generate implementation code following the specification

---

## When Working on This Project

1. **Always read specification** before making changes
2. **Test with Cyrillic** - Don't assume ASCII only
3. **Use `item_id`** - Never `menu_item_id`
4. **Secrets in Cloudflare** - Never in code/DB
5. **Price from DB** - Never trust frontend calculations
6. **UTF-8 everywhere** - `ensure_ascii=False` + `charset=utf-8`

---

## Contact & Scale

- **Target Users**: Russian-speaking customers
- **Expected Load**: ~100 orders in 1.5 months
- **Geography**: Serbia (based on +381 phone codes)
- **Currency**: RSD (Serbian Dinar)

**Note**: This is a small-scale local business application. Over-engineering is not needed. Focus on simplicity, security, and correctness.
