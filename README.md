# Foodikal NY Backend

Python backend for Foodikal NY restaurant food ordering system, deployed on Cloudflare Workers with D1 database.

## Project Overview

- **Purpose**: RESTful API for food ordering without authentication or payment
- **Scale**: ~100 orders per 1.5 months (low traffic)
- **Tech Stack**: Python on Cloudflare Workers + D1 SQL Database
- **Features**: Menu browsing, order creation, Telegram notifications, admin dashboard

## Prerequisites

- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/install-and-update/) installed
- Cloudflare account
- Python 3.9+ (for local development)
- Telegram bot (optional, for notifications)

## Project Structure

```
foodikal-ny-backend/
├── src/
│   ├── index.py          # Main entry point, routing
│   ├── database.py       # D1 database operations
│   ├── auth.py           # Password authentication (PBKDF2)
│   ├── telegram.py       # Telegram notifications
│   ├── validators.py     # Input validation
│   └── utils.py          # Helper functions
├── schema.sql            # Database initialization
├── cf-requirements.txt   # Cloudflare Python packages (empty)
├── wrangler.toml         # Cloudflare Workers config
├── CLAUDE.md             # Project context
├── front_instructions.md # Frontend integration guide
└── README.md             # This file
```

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
cd foodikal-ny-back
pip install -r requirements.txt
```

### 2. Login to Cloudflare

```bash
wrangler login
```

### 3. Create D1 Database

```bash
wrangler d1 create foodikal_ny_db
```

This will output a `database_id`. Copy it and update `wrangler.toml`:

```toml
[[d1_databases]]
binding = "DB"
database_name = "foodikal_ny_db"
database_id = "YOUR_DATABASE_ID_HERE"
```

### 4. Initialize Database Schema

```bash
wrangler d1 execute foodikal_ny_db --file=./schema.sql
```

Verify tables were created:

```bash
wrangler d1 execute foodikal_ny_db --command="SELECT name FROM sqlite_master WHERE type='table'"
```

### 5. Setup Telegram Bot (Optional)

1. Create a bot with [@BotFather](https://t.me/BotFather) on Telegram
2. Get your bot token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
3. Get your chat ID:
   - Send a message to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your `chat_id` in the response

### 6. Generate Admin Password Hash

```bash
python3 src/auth.py YOUR_SECURE_PASSWORD
```

This will output a PBKDF2 hash. Save it for the next step.

### 7. Set Cloudflare Secrets

```bash
# Set Telegram bot token
wrangler secret put TELEGRAM_BOT_TOKEN
# Paste your bot token when prompted

# Set Telegram chat ID
wrangler secret put TELEGRAM_CHAT_ID
# Paste your chat ID when prompted

# Set admin password hash
wrangler secret put ADMIN_PASSWORD_HASH
# Paste the hash from step 6 when prompted
```

**Important:** Keep your plain password secure - you'll need it to access admin endpoints!

### 8. Test Locally

```bash
wrangler dev
```

The API will be available at `http://localhost:8787`

Test endpoints:

```bash
# Get menu
curl http://localhost:8787/api/menu | jq

# Create order
curl -X POST http://localhost:8787/api/create_order \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test User",
    "customer_contact": "+381641234567",
    "delivery_address": "Test Street 123",
    "order_items": [{"item_id": 1, "quantity": 2}]
  }' | jq

# List orders (admin)
curl http://localhost:8787/api/admin/order_list \
  -H "Authorization: Bearer YOUR_PASSWORD" | jq
```

### 9. Deploy to Production

```bash
wrangler deploy
```

Your API will be available at: `https://foodikal-ny-backend.workers.dev`

## API Endpoints

### Public Endpoints (No Authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/menu` | Get all menu items grouped by category |
| GET | `/api/menu/category/:category` | Get items by category (URL-encoded Cyrillic) |
| POST | `/api/create_order` | Create new order |

### Admin Endpoints (Password Protected)

Authentication: `Authorization: Bearer <password>`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/order_list` | List all orders |
| PATCH | `/api/admin/orders/:id` | Update order confirmations |
| DELETE | `/api/admin/orders/:id` | Delete order |
| POST | `/api/admin/menu_add` | Add menu item |
| PUT | `/api/admin/menu_update/:id` | Update menu item |
| DELETE | `/api/admin/menu_delete/:id` | Delete menu item |

See [api_endpoints_quick_reference.md](./api_endpoints_quick_reference.md) for detailed API documentation.

## Development

### Database Commands

```bash
# Execute SQL command
wrangler d1 execute foodikal_ny_db --command="SELECT * FROM orders"

# Backup database
wrangler d1 export foodikal_ny_db --output=backup.sql

# View logs
wrangler tail
```

### Testing Category URLs

Category names are in Cyrillic and must be URL-encoded:

```bash
# Encode category name
python3 -c "from urllib.parse import quote; print(quote('Горячее'))"
# Output: %D0%93%D0%BE%D1%80%D1%8F%D1%87%D0%B5%D0%B5

# Test endpoint
curl "http://localhost:8787/api/menu/category/%D0%93%D0%BE%D1%80%D1%8F%D1%87%D0%B5%D0%B5" | jq
```

## Important Notes

### Field Naming
- Always use `item_id` (not `menu_item_id`)
- Database fields: `description` (not `ingredients`), `image` (not `photo_url`)

### Cyrillic Support
- Use `ensure_ascii=False` in JSON responses
- Include `charset=utf-8` in Content-Type headers
- URL-decode category parameters

### Security
- Never trust client prices - always fetch from database
- Use parameterized queries (SQL injection prevention)
- Secrets stored in Cloudflare Secrets (NOT in code)
- CORS configured for: `https://ny2026.foodikal.rs`

### Telegram Notifications
- Sent only on order creation
- Non-blocking (order creation doesn't fail if Telegram fails)
- 5-second timeout with 3 retry attempts

## Troubleshooting

**Database not found:**
- Ensure D1 database is created and `database_id` in `wrangler.toml` is correct

**Telegram notification not sent:**
- Check bot token and chat ID are correct
- Verify bot can send messages to the chat

**Password authentication fails:**
- Verify PBKDF2 hash is set correctly in Cloudflare Secrets
- Check Authorization header format: `Bearer <password>`

**CORS errors:**
- Update `ALLOWED_ORIGINS` in `src/utils.py` to include your frontend domain

## Production Checklist

- [ ] Database created and initialized
- [ ] All secrets set (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ADMIN_PASSWORD_HASH)
- [ ] Admin password is secure and saved
- [ ] Tested all endpoints locally
- [ ] CORS configured for production domain
- [ ] Deployed to Cloudflare Workers
- [ ] Verified production endpoints work
- [ ] Telegram notifications working

## Documentation

- **CLAUDE.md** - Project context and conventions
- **foodikal_backend_specification.md** - Complete API specification
- **foodikal_recommendations.md** - Best practices and patterns
- **api_endpoints_quick_reference.md** - API endpoint reference
- **front_instructions.md** - Frontend integration guide with examples

## License

Proprietary - Foodikal NY Restaurant

## Support

For issues or questions, check:
1. Cloudflare Workers logs: `wrangler tail`
2. Test locally: `wrangler dev`
3. Verify database: `wrangler d1 execute foodikal_ny_db --command="SELECT * FROM sqlite_master"`
4. Review documentation files
