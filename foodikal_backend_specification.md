# Foodikal NY Backend Application - Specification for Code Generation

## Project Overview
Create a Python backend application for "Foodikal NY" restaurant food ordering system, deployed on Cloudflare Workers with D1 SQL database.

**Scale**: ~100 orders per 1.5 months (low traffic)
**Tech Stack**: Python on Cloudflare Workers + D1 SQL Database
**Deployment**: Wrangler CLI

---

## Application Architecture

### 1. Frontend Flow
- Customer browses landing page with food categories and dishes
- Selects dishes and quantities
- Fills contact information form
- Submits order (no authentication, no payment)
- Manager gets notified via Telegram
- Manager confirms order by phone/telegram and updates status

### 2. Backend Components
- RESTful API endpoints
- D1 SQL database with 3 tables
- Telegram webhook integration
- Simple password authentication for manager dashboard

---

## Database Schema (D1 SQL)

### Table 1: `menu_items`
```sql
CREATE TABLE menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    price INTEGER NOT NULL,
    image TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Field Descriptions**:
- `name`: Item name with weight info (e.g., "Брускетта с вяленой свининой (60г)")
- `category`: One of: Брускетты, Горячее, Закуски, Канапе, Салат, Тарталетки
- `description`: Detailed ingredient list and description
- `price`: Price in RSD (Serbian Dinars)
- `image`: Relative or absolute path to image (e.g., "images/img1.jpg")

**Categories** (static): 
- Брускетты (Bruschetta)
- Горячее (Hot dishes)
- Закуски (Appetizers)
- Канапе (Canapes)
- Салат (Salads)
- Тарталетки (Tartlets)

**Note**: All menu items are always available (no availability status needed)

### Table 2: `orders`
```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    customer_contact TEXT NOT NULL,
    customer_email TEXT,
    delivery_address TEXT NOT NULL,
    comments TEXT,
    order_items TEXT NOT NULL,
    total_price INTEGER NOT NULL,
    confirmed_after_creation BOOLEAN DEFAULT 0,
    confirmed_before_delivery BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**order_items format** (JSON string):
```json
[
    {"item_id": 1, "name": "Свиная рулька", "quantity": 2, "price": 3100},
    {"item_id": 5, "name": "Брускетта с томатами", "quantity": 1, "price": 850}
]
```

---

## Secrets Management (Cloudflare)

All sensitive credentials are stored as **Cloudflare Secrets**, not in database or wrangler.toml:

### Required Secrets:
1. **TELEGRAM_BOT_TOKEN** - Telegram bot token from @BotFather
2. **TELEGRAM_CHAT_ID** - Your Telegram chat ID for notifications
3. **ADMIN_PASSWORD_HASH** - Bcrypt hash of admin password

### Setting Secrets:
```bash
# Set Telegram bot token
wrangler secret put TELEGRAM_BOT_TOKEN

# Set Telegram chat ID
wrangler secret put TELEGRAM_CHAT_ID

# Set admin password hash (generate hash first with bcrypt)
wrangler secret put ADMIN_PASSWORD_HASH
```

### Generating Password Hash:
```python
import bcrypt

password = "your_secure_password"  # Choose a strong password
salt = bcrypt.gensalt(rounds=12)
password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
print(f"Password hash: {password_hash}")
# Copy this hash and paste when running: wrangler secret put ADMIN_PASSWORD_HASH
```

### Accessing Secrets in Code:
```python
# Secrets are available in env object
async def handle_request(request, env, ctx):
    telegram_token = env.TELEGRAM_BOT_TOKEN
    telegram_chat = env.TELEGRAM_CHAT_ID
    admin_hash = env.ADMIN_PASSWORD_HASH
```

---

## API Endpoints

### Public Endpoints (No Authentication)

#### 1. Get Full Menu
```
GET /api/menu
```

**Response** (200 OK):
```json
{
    "success": true,
    "data": {
        "Брускетты": [
            {
                "id": 1,
                "name": "Брускетта с вяленой свининой (60г)",
                "description": "Состав составов: блюдо состоит из кучи разных штук например штука1 и штука2 и штука3 и штука4.",
                "price": 300,
                "image": "images/img1.jpg"
            },
            {
                "id": 2,
                "name": "Брускетта с гравлаксом (60г)",
                "description": "Состав составов: блюдо состоит из кучи разных штук например штука1 и штука2 и штука3 и штука4.",
                "price": 220,
                "image": "images/img1.jpg"
            }
        ],
        "Горячее": [
            {
                "id": 4,
                "name": "Баранья нога (запеченая, 1780г)",
                "description": "Состав составов: блюдо состоит из кучи разных штук например штука1 и штука2 и штука3 и штука4.",
                "price": 15500,
                "image": "images/img1.jpg"
            }
        ],
        "Закуски": [
            {
                "id": 7,
                "name": "Ассорти сыров и мясных деликатесов (300г)",
                "description": "Состав составов: блюдо состоит из кучи разных штук например штука1 и штука2 и штука3 и штука4.",
                "price": 2000,
                "image": "images/img1.jpg"
            }
        ],
        "Канапе": [
            {
                "id": 9,
                "name": "Канапе овощное (45г)",
                "description": "Состав составов: блюдо состоит из кучи разных штук например штука1 и штука2 и штука3 и штука4.",
                "price": 75,
                "image": "images/img1.jpg"
            }
        ],
        "Салат": [],
        "Тарталетки": []
    }
}
```

**Response Structure**:
- `success`: boolean
- `data`: object with category names as keys
  - Each category key contains an array of menu items
  - Menu items have: `id`, `name`, `description`, `price`, `image`
  - Weight information is included in the `name` field (e.g., "(60г)")
  - Empty arrays for categories with no items

#### 2. Get Menu by Category
```
GET /api/menu/category/:category_name
```

**Important**: Category names contain Cyrillic characters and must be URL-encoded in requests.

**Examples**: 
- `GET /api/menu/category/Горячее` → URL encode as `/api/menu/category/%D0%93%D0%BE%D1%80%D1%8F%D1%87%D0%B5%D0%B5`
- `GET /api/menu/category/Брускетты` → URL encode as `/api/menu/category/%D0%91%D1%80%D1%83%D1%81%D0%BA%D0%B5%D1%82%D1%82%D1%8B`

**Implementation Note**: Backend should URL-decode the category parameter before querying database.

```python
# Example decoding
from urllib.parse import unquote

category = unquote(category_param)  # "%D0%93%D0%BE%D1%80%D1%8F%D1%87%D0%B5%D0%B5" → "Горячее"
```

**Response** (200 OK):
```json
{
    "success": true,
    "category": "Горячее",
    "data": [
        {
            "id": 4,
            "name": "Баранья нога (запеченая, 1780г)",
            "description": "Состав составов: блюдо состоит из кучи разных штук например штука1 и штука2 и штука3 и штука4.",
            "price": 15500,
            "image": "images/img1.jpg"
        },
        {
            "id": 5,
            "name": "Куриный шашлычок с картофелем фри (200г)",
            "description": "Состав составов: блюдо состоит из кучи разных штук например штука1 и штука2 и штука3 и штука4.",
            "price": 550,
            "image": "images/img1.jpg"
        }
    ]
}
```

**Response Structure**:
- `success`: boolean
- `category`: string (the requested category name)
- `data`: array of menu items
  - Each item has: `id`, `name`, `description`, `price`, `image`
  - No `category` field in items (already filtered by category)

**Error Response** (404 Not Found):
```json
{
    "success": false,
    "error": "Category not found"
}
```

#### 3. Create Order
```
POST /api/create_order
Content-Type: application/json
```

**Request Body**:
```json
{
    "customer_name": "Иван Петров",
    "customer_contact": "+381641234567",
    "customer_email": "ivan@example.com",
    "delivery_address": "Улица Пушкина, дом 5, квартира 12",
    "comments": "Позвоните за 30 минут до доставки",
    "order_items": [
        {
            "item_id": 1,
            "quantity": 2
        },
        {
            "item_id": 5,
            "quantity": 1
        }
    ]
}
```

**Validation Rules**:
- `customer_name`: required, non-empty string
- `customer_contact`: required, non-empty string (phone or telegram handle)
- `customer_email`: optional, valid email format if provided
- `delivery_address`: required, non-empty string
- `comments`: optional string
- `order_items`: required array, at least 1 item
  - Each item: `item_id` (integer), `quantity` (integer > 0)

**Business Logic**:
1. Validate all required fields
2. Check that all `item_id` exist in database
3. Calculate `total_price` by fetching prices from menu_items table
4. Store order in database with current timestamp
5. Send Telegram notification immediately
6. Return created order with ID

**Response** (201 Created):
```json
{
    "success": true,
    "order_id": 42,
    "total_price": 7050,
    "message": "Order created successfully"
}
```

**Error Responses**:
```json
// 400 Bad Request
{
    "success": false,
    "error": "Invalid order data",
    "details": {
        "customer_name": "Field is required",
        "order_items": "Must contain at least 1 item"
    }
}

// 404 Not Found
{
    "success": false,
    "error": "Menu item not found",
    "invalid_ids": [99]
}
```

---

### Manager Dashboard Endpoints (Password Protected)

**Authentication Method**: Simple password in request header
```
Authorization: Bearer <password>
```

All protected endpoints must:
1. Check if Authorization header is present
2. Extract password from "Bearer <password>" format
3. Hash the provided password using bcrypt
4. Compare with `env.ADMIN_PASSWORD_HASH` (Cloudflare secret)
5. Return 401 Unauthorized if invalid

**Important**: Password is compared using bcrypt's constant-time comparison to prevent timing attacks.

```python
import bcrypt

def verify_password(provided_password: str, stored_hash: str) -> bool:
    """Verify password against bcrypt hash"""
    try:
        return bcrypt.checkpw(
            provided_password.encode('utf-8'),
            stored_hash.encode('utf-8')
        )
    except Exception:
        return False

# In request handler
auth_header = request.headers.get("Authorization", "")
if not auth_header.startswith("Bearer "):
    return Response(401, "Unauthorized")

password = auth_header.replace("Bearer ", "", 1)
if not verify_password(password, env.ADMIN_PASSWORD_HASH):
    return Response(401, "Unauthorized")
```

#### 4. Get All Orders
```
GET /api/admin/order_list
Authorization: Bearer <password>
```

**Response** (200 OK):
```json
{
    "success": true,
    "count": 3,
    "orders": [
        {
            "id": 42,
            "customer_name": "Иван Петров",
            "customer_contact": "+381641234567",
            "customer_email": "ivan@example.com",
            "delivery_address": "Улица Пушкина, дом 5, квартира 12",
            "comments": "Позвоните за 30 минут",
            "order_items": [
                {
                    "menu_item_id": 1,
                    "name": "Свиная рулька",
                    "quantity": 2,
                    "price": 3100
                }
            ],
            "total_price": 6200,
            "confirmed_after_creation": true,
            "confirmed_before_delivery": false,
            "created_at": "2025-11-06T14:30:00Z",
            "updated_at": "2025-11-06T15:00:00Z"
        }
    ]
}
```

**Sort Order**: Most recent orders first (ORDER BY created_at DESC)

#### 5. Update Order Confirmations
```
PATCH /api/admin/orders/:id
Authorization: Bearer <password>
Content-Type: application/json
```

**Request Body** (partial update):
```json
{
    "confirmed_after_creation": true,
    "confirmed_before_delivery": false
}
```

**Allowed Fields**:
- `confirmed_after_creation`: boolean (optional)
- `confirmed_before_delivery`: boolean (optional)

**Business Logic**:
1. Validate order ID exists
2. Update only provided fields
3. Set `updated_at` to current timestamp
4. Return updated order

**Response** (200 OK):
```json
{
    "success": true,
    "message": "Order updated successfully",
    "order": {
        "id": 42,
        "confirmed_after_creation": true,
        "confirmed_before_delivery": false,
        "updated_at": "2025-11-06T16:00:00Z"
    }
}
```

**Error Response** (404 Not Found):
```json
{
    "success": false,
    "error": "Order not found"
}
```

#### 6. Delete Order
```
DELETE /api/admin/orders/:id
Authorization: Bearer <password>
```

**Response** (200 OK):
```json
{
    "success": true,
    "message": "Order deleted successfully"
}
```

**Error Response** (404 Not Found):
```json
{
    "success": false,
    "error": "Order not found"
}
```

---

### Admin Menu Management Endpoints (Optional but Recommended)

#### 7. Add Menu Item
```
POST /api/admin/menu_add
Authorization: Bearer <password>
Content-Type: application/json
```

**Request Body**:
```json
{
    "name": "Салат Цезарь",
    "category": "Салат",
    "description": "Листья салата, курица, сыр пармезан, сухарики, соус цезарь",
    "price": 1200,
    "image": "images/caesar-salad.jpg"
}
```

**Response** (201 Created):
```json
{
    "success": true,
    "menu_item_id": 15,
    "message": "Menu item created successfully"
}
```

#### 8. Update Menu Item
```
PUT /api/admin/menu_update/:id
Authorization: Bearer <password>
Content-Type: application/json
```

**Request Body** (all fields optional for partial update):
```json
{
    "name": "Салат Цезарь XL",
    "price": 1500
}
```

**Response** (200 OK):
```json
{
    "success": true,
    "message": "Menu item updated successfully"
}
```

#### 9. Delete Menu Item
```
DELETE /api/admin/menu_delete/:id
Authorization: Bearer <password>
```

**Response** (200 OK):
```json
{
    "success": true,
    "message": "Menu item deleted successfully"
}
```

---

## Telegram Webhook Integration

### Configuration
Telegram credentials are stored as **Cloudflare Secrets** (see Secrets Management section above):
- `TELEGRAM_BOT_TOKEN` - Your bot token from @BotFather
- `TELEGRAM_CHAT_ID` - Your chat ID for receiving notifications

Access in code via `env.TELEGRAM_BOT_TOKEN` and `env.TELEGRAM_CHAT_ID`

### When to Send
- **Only** when new order is created via `POST /api/create_order`
- Do NOT send for order updates or deletions

### Message Format
```
🍽 **New Order #42**

👤 Name: Иван Петров
📞 Contact: +381641234567
📧 Email: ivan@example.com
📍 Address: Улица Пушкина, дом 5, квартира 12

📦 Items:
• Свиная рулька x2 (6200 RSD)
• Брускетта с помидорами x1 (850 RSD)

💰 Total: 7050 RSD

💬 Comments: Позвоните за 30 минут до доставки

🕒 Created: 2025-11-06 14:30
```

### Implementation Requirements
1. Send notification immediately after order is saved to database
2. If Telegram API fails, log error but don't fail order creation
3. Use async/non-blocking request if possible
4. Timeout: 5 seconds max

### Telegram API Endpoint
```
POST https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/sendMessage
Content-Type: application/json

{
    "chat_id": "<TELEGRAM_CHAT_ID>",
    "text": "<formatted_message>",
    "parse_mode": "Markdown"
}
```

---

## Error Handling

### Standard Error Response Format
```json
{
    "success": false,
    "error": "Human-readable error message",
    "code": "ERROR_CODE",
    "details": {}  // Optional additional context
}
```

### HTTP Status Codes
- `200 OK`: Successful GET/PATCH/DELETE
- `201 Created`: Successful POST
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Missing or invalid password
- `404 Not Found`: Resource doesn't exist
- `500 Internal Server Error`: Server-side error

### Required Error Handling
1. **Database Connection Errors**: Retry once, then return 500
2. **Validation Errors**: Return 400 with specific field errors
3. **Telegram API Errors**: Log error, continue with order creation
4. **Invalid Password**: Return 401 immediately
5. **Missing Required Fields**: Return 400 with list of missing fields

---

## Security Requirements

### 1. Password Authentication
- Store only bcrypt-hashed passwords in database
- Use salt rounds: 10-12
- Never log or expose passwords in responses
- Compare using constant-time comparison

### 2. CORS Configuration
```python
ALLOWED_ORIGINS = [
    "https://ny2026.foodikal.rs",  # Your production domain
    "http://localhost:3000",  # Development
]
```

### 3. Rate Limiting (Optional but Recommended)
- Public endpoints: 100 requests per minute per IP
- Admin endpoints: 50 requests per minute per IP
- Order creation: 5 requests per minute per IP

### 4. Input Validation
- Sanitize all string inputs
- Validate email format if provided
- Reject orders with quantity > 50 per item
- Reject orders with > 20 different items
- Maximum comment length: 500 characters

### 5. SQL Injection Prevention
- Use parameterized queries ONLY
- Never concatenate user input into SQL strings

---

## Cloudflare Workers Configuration

### wrangler.toml
```toml
name = "foodikal-ny-backend"
main = "src/index.py"
compatibility_date = "2025-11-06"

[build]
command = "pip install -r requirements.txt -t ./deps"

[[d1_databases]]
binding = "DB"
database_name = "foodikal_ny_db"
database_id = "<your-database-id>"

# Note: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, and ADMIN_PASSWORD_HASH
# are stored as Cloudflare Secrets, not in this file
# Use: wrangler secret put <SECRET_NAME>

[env.production]
vars = { ENVIRONMENT = "production" }

[env.development]
vars = { ENVIRONMENT = "development" }
```

### Python Dependencies (requirements.txt)
```
bcrypt>=4.0.0
python-telegram-bot>=20.0  # Or requests for simple HTTP calls
```

---

## Database Initialization

### Initial Setup SQL Script
```sql
-- Create tables
CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    price INTEGER NOT NULL,
    image TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    customer_contact TEXT NOT NULL,
    customer_email TEXT,
    delivery_address TEXT NOT NULL,
    comments TEXT,
    order_items TEXT NOT NULL,
    total_price INTEGER NOT NULL,
    confirmed_after_creation BOOLEAN DEFAULT 0,
    confirmed_before_delivery BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX idx_menu_category ON menu_items(category);

-- Insert sample menu items (based on your menu)
INSERT INTO menu_items (name, category, description, price, image) VALUES
('Брускетта с вяленой свининой (60г)', 'Брускетты', 'Состав составов: блюдо состоит из кучи разных штук например штука1 и штука2 и штука3 и штука4.', 300, 'images/img1.jpg'),
('Брускетта с гравлаксом (60г)', 'Брускетты', 'Состав составов: блюдо состоит из кучи разных штук например штука1 и штука2 и штука3 и штука4.', 220, 'images/img1.jpg'),
('Брускетта с грибной икрой (60г)', 'Брускетты', 'Состав составов: блюдо состоит из кучи разных штук например штука1 и штука2 и штука3 и штука4.', 120, 'images/img1.jpg'),
('Баранья нога (запеченая, 1780г)', 'Горячее', 'Состав составов: блюдо состоит из кучи разных штук например штука1 и штука2 и штука3 и штука4.', 15500, 'images/img1.jpg'),
('Куриный шашлычок с картофелем фри (200г)', 'Горячее', 'Состав составов: блюдо состоит из кучи разных штук например штука1 и штука2 и штука3 и штука4.', 550, 'images/img1.jpg'),
('Овощи гриль (550г)', 'Горячее', 'Состав составов: блюдо состоит из кучи разных штук например штука1 и штука2 и штука3 и штука4.', 650, 'images/img1.jpg'),
('Ассорти сыров и мясных деликатесов (300г)', 'Закуски', 'Состав составов: блюдо состоит из кучи разных штук например штука1 и штука2 и штука3 и штука4.', 2000, 'images/img1.jpg'),
('Хумус с баклажаном (закуска, 1шт 50г)', 'Закуски', 'Состав составов: блюдо состоит из кучи разных штук например штука1 и штука2 и штука3 и штука4.', 120, 'images/img1.jpg'),
('Канапе овощное (45г)', 'Канапе', 'Состав составов: блюдо состоит из кучи разных штук например штука1 и штука2 и штука3 и штука4.', 75, 'images/img1.jpg'),
('Канапе с ветчиной (40г)', 'Канапе', 'Состав составов: блюдо состоит из кучи разных штук например штука1 и штука2 и штука3 и штука4.', 90, 'images/img1.jpg'),
('Канапе с грушей и пршутом (25г)', 'Канапе', 'Состав составов: блюдо состоит из кучи разных штук например штука1 и штука2 и штука3 и штука4.', 140, 'images/img1.jpg');
```

**Note**: Admin password is NOT stored in database. It's stored as Cloudflare secret `ADMIN_PASSWORD_HASH`.

### Wrangler Commands for Database Setup
```bash
# Create D1 database
wrangler d1 create foodikal_ny_db

# Execute initialization script
wrangler d1 execute foodikal_ny_db --file=./schema.sql

# View data (for testing)
wrangler d1 execute foodikal_ny_db --command="SELECT * FROM menu_items"
```

---

## Development Workflow

### 1. Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run local development server with D1 local database
wrangler dev

# Test endpoints
curl http://localhost:8787/api/menu
```

### 2. Testing
Create test cases for:
- Menu retrieval (all items, by category)
- Order creation with valid/invalid data
- Password authentication (valid/invalid)
- Order management (update, delete)
- Edge cases (empty orders, missing fields, SQL injection attempts)

### 3. Deployment
```bash
# Deploy to production
wrangler deploy

# View logs
wrangler tail

# Rollback if needed
wrangler rollback
```

---

## Code Structure Recommendations

```
foodikal-ny-backend/
├── src/
│   ├── index.py              # Main entry point, route handling
│   ├── database.py           # D1 database operations
│   ├── auth.py               # Password authentication
│   ├── telegram.py           # Telegram notification service
│   ├── validators.py         # Input validation functions
│   └── utils.py              # Helper functions
├── schema.sql                # Database initialization
├── requirements.txt          # Python dependencies
├── wrangler.toml            # Cloudflare Workers config
└── README.md                # Setup and deployment instructions
```

### Key Implementation Patterns

#### 1. Request Handler Pattern
```python
async def handle_request(request, env, ctx):
    """Main request router"""
    url = request.url
    method = request.method
    
    # Route matching
    if method == "GET" and url.endswith("/api/menu"):
        return await get_menu(env)
    elif method == "POST" and url.endswith("/api/create_order"):
        return await create_order(request, env)
    # ... more routes
    
    return Response("Not Found", status=404)
```

#### 2. Database Query Pattern
```python
async def get_menu_items(db):
    """Fetch all menu items from D1"""
    result = await db.prepare(
        "SELECT * FROM menu_items ORDER BY category, name"
    ).all()
    return result
```

#### 3. Authentication Middleware
```python
def require_auth(handler):
    """Decorator for protected endpoints"""
    async def wrapper(request, env):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not verify_password(auth_header, env):
            return Response(
                json.dumps({"success": False, "error": "Unauthorized"}),
                status=401,
                headers={"Content-Type": "application/json"}
            )
        return await handler(request, env)
    return wrapper
```

---

## Testing Checklist

### Manual Testing Steps

#### Phase 1: Menu API
- [ ] GET /api/menu returns all items
- [ ] GET /api/menu/category/Горячее returns only hot dishes
- [ ] Invalid category returns 404

#### Phase 2: Order Creation
- [ ] Valid order creates successfully
- [ ] Telegram notification sent
- [ ] Missing required fields rejected
- [ ] Invalid menu_item_id rejected
- [ ] Total price calculated correctly

#### Phase 3: Admin Dashboard
- [ ] Invalid password returns 401
- [ ] Valid password accesses orders
- [ ] Can update confirmations
- [ ] Can delete orders
- [ ] Orders sorted by date (newest first)

#### Phase 4: Edge Cases
- [ ] Order with 0 quantity rejected
- [ ] Order with 50+ items rejected
- [ ] Very long comment (>500 chars) rejected
- [ ] SQL injection attempts blocked
- [ ] Empty order_items array rejected

---

## Performance Considerations

### Expected Load
- **Peak**: 5 orders per day
- **Average**: 2-3 orders per day
- **Menu requests**: 50-100 per day

### Optimization Tips
1. Menu items rarely change → consider caching with 1-hour TTL
2. No need for connection pooling at this scale
3. D1 database is sufficient (no need for separate cache)
4. Telegram webhook timeout should be 5 seconds max

---

## Monitoring & Logging

### What to Log
- All order creations (success/failure)
- Admin authentication attempts
- Telegram notification status
- Database errors
- API response times > 1 second

### Log Format
```json
{
    "timestamp": "2025-11-06T14:30:00Z",
    "level": "INFO",
    "event": "order_created",
    "order_id": 42,
    "total_price": 7050,
    "telegram_sent": true
}
```

### Cloudflare Analytics
Monitor:
- Request count per endpoint
- Error rate (4xx, 5xx)
- Average response time
- Geographic distribution of requests

---

## Future Enhancements (Not Required Now)

1. **Email Notifications**: Send confirmation email to customer
2. **Order Status History**: Track status changes with timestamps
3. **Customer Portal**: Allow customers to track their orders
4. **Payment Integration**: Stripe, PayPal, or local payment gateways
5. **Inventory Management**: Track ingredient availability
6. **Analytics Dashboard**: Sales reports, popular dishes
7. **Multi-language Support**: Serbian, English translations

---

## Deployment Instructions

### Step 1: Setup Cloudflare Account
1. Create Cloudflare account
2. Install Wrangler CLI: `npm install -g wrangler`
3. Login: `wrangler login`

### Step 2: Create D1 Database
```bash
wrangler d1 create foodikal_ny_db
# Copy database_id from output
```

### Step 3: Initialize Database
```bash
# Create schema.sql with tables
wrangler d1 execute foodikal_ny_db --file=./schema.sql

# Verify tables created
wrangler d1 execute foodikal_ny_db --command="SELECT name FROM sqlite_master WHERE type='table'"
```

### Step 4: Setup Telegram Bot
1. Create bot with @BotFather on Telegram
2. Get bot token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
3. Get your chat ID:
   - Send a message to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your chat ID in the response

### Step 5: Configure Secrets
```bash
# Set Telegram bot token
wrangler secret put TELEGRAM_BOT_TOKEN
# Paste your bot token when prompted

# Set Telegram chat ID
wrangler secret put TELEGRAM_CHAT_ID
# Paste your chat ID when prompted

# Generate admin password hash first
python3 -c "import bcrypt; password='YOUR_SECURE_PASSWORD'; print(bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8'))"

# Set admin password hash
wrangler secret put ADMIN_PASSWORD_HASH
# Paste the generated hash when prompted
```

**Important**: Keep your original password secure - you'll need it to access admin endpoints!

### Step 6: Deploy
```bash
# Test locally first
wrangler dev

# Deploy to production
wrangler deploy

# Your API will be at:
# https://foodikal-ny-backend.workers.dev
```

### Step 7: Test Production Endpoints
```bash
# Test menu
curl https://foodikal-ny-backend.workers.dev/api/menu

# Test order creation
curl -X POST https://foodikal-ny-backend.workers.dev/api/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"Test","customer_contact":"+123","delivery_address":"Test St",...}'
```

---

## Support & Troubleshooting

### Common Issues

**Issue**: "Database not found"
- **Solution**: Ensure D1 database is created and database_id in wrangler.toml matches

**Issue**: "Telegram notification not sent"
- **Solution**: Check bot token, chat ID, and network connectivity

**Issue**: "Password authentication fails"
- **Solution**: Verify bcrypt hash is correct, check header format

**Issue**: "CORS errors from frontend"
- **Solution**: Add frontend domain to ALLOWED_ORIGINS

### Debug Mode
Add debug logging to see detailed request/response info:
```python
DEBUG = True  # Set to False in production

if DEBUG:
    print(f"Request: {method} {url}")
    print(f"Headers: {dict(request.headers)}")
    print(f"Body: {await request.text()}")
```

---

## Final Notes

This specification provides complete requirements for generating a production-ready Python backend for the Foodikal NY food ordering system. The generated code should:

1. ✅ Run on Cloudflare Workers with D1 database
2. ✅ Handle all specified API endpoints
3. ✅ Include proper error handling and validation
4. ✅ Send Telegram notifications for new orders
5. ✅ Secure admin endpoints with password authentication
6. ✅ Follow Python best practices and clean code principles
7. ✅ Include comprehensive comments and documentation
8. ✅ Be ready for deployment with minimal configuration

**Expected Deliverables**:
- Complete Python code (all modules)
- Database schema SQL file
- wrangler.toml configuration
- requirements.txt with dependencies
- README.md with setup instructions
- Sample test requests (curl commands or Postman collection)

Good luck with your project! 🚀
