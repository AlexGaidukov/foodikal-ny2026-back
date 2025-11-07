# Foodikal API Endpoints - Quick Reference

## Public Endpoints (No Authentication)

### 1. Get All Menu Items
```
GET /api/menu
```
Returns all menu items grouped by categories.

**Response**:
```json
{
  "success": true,
  "data": {
    "Брускетты": [
      {
        "id": 1,
        "name": "Брускетта с вяленой свининой (60г)",
        "description": "Состав блюда...",
        "price": 300,
        "image": "images/img1.jpg"
      }
    ],
    "Горячее": [...],
    "Закуски": [...],
    "Канапе": [...],
    "Салат": [],
    "Тарталетки": []
  }
}
```

### 2. Get Menu by Category
```
GET /api/menu/category/:category_name
```
**Note**: Category names must be URL-encoded (Cyrillic support)
Example: `GET /api/menu/category/%D0%93%D0%BE%D1%80%D1%8F%D1%87%D0%B5%D0%B5` (Горячее)

**Response**:
```json
{
  "success": true,
  "category": "Горячее",
  "data": [
    {
      "id": 4,
      "name": "Баранья нога (запеченая, 1780г)",
      "description": "Состав блюда...",
      "price": 15500,
      "image": "images/img1.jpg"
    }
  ]
}
```

### 3. Create Order
```
POST /api/create_order
Content-Type: application/json
```
**Body**:
```json
{
  "customer_name": "string (required)",
  "customer_contact": "string (required)",
  "customer_email": "string (optional)",
  "delivery_address": "string (required)",
  "comments": "string (optional)",
  "order_items": [
    {"item_id": 1, "quantity": 2}
  ]
}
```

---

## Admin Endpoints (Password Protected)

**Authentication**: `Authorization: Bearer <password>`

### 4. List All Orders
```
GET /api/admin/order_list
```
Returns all orders sorted by date (newest first).

### 5. Update Order Confirmations
```
PATCH /api/admin/orders/:id
Content-Type: application/json
```
**Body** (partial update):
```json
{
  "confirmed_after_creation": true,
  "confirmed_before_delivery": false
}
```

### 6. Delete Order
```
DELETE /api/admin/orders/:id
```

---

## Admin Menu Management (Optional)

### 7. Add Menu Item
```
POST /api/admin/menu_add
Content-Type: application/json
```
**Body**:
```json
{
  "name": "Салат Цезарь (250г)",
  "category": "Салат",
  "description": "Листья салата, курица, пармезан, сухарики, соус цезарь",
  "price": 1200,
  "image": "images/caesar.jpg"
}
```

### 8. Update Menu Item
```
PUT /api/admin/menu_update/:id
Content-Type: application/json
```
**Body** (partial update - all fields optional):
```json
{
  "name": "Салат Цезарь XL (350г)",
  "description": "Увеличенная порция салата цезарь",
  "price": 1500
}
```

### 9. Delete Menu Item
```
DELETE /api/admin/menu_delete/:id
```

---

## Categories (Static)

- **Брускетты** (Bruschetta)
- **Горячее** (Hot dishes)
- **Закуски** (Appetizers)
- **Канапе** (Canapes)
- **Салат** (Salads)
- **Тарталетки** (Tartlets)

---

## Testing Examples

### Test Public Endpoints
```bash
# Get menu
curl http://localhost:8787/api/menu | jq

# Get category (URL-encoded Cyrillic)
curl "http://localhost:8787/api/menu/category/%D0%93%D0%BE%D1%80%D1%8F%D1%87%D0%B5%D0%B5" | jq

# Create order
curl -X POST http://localhost:8787/api/create_order \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test User",
    "customer_contact": "+381641234567",
    "delivery_address": "Test Street 123",
    "order_items": [{"item_id": 1, "quantity": 2}]
  }' | jq
```

### Test Admin Endpoints
```bash
# List orders
curl http://localhost:8787/api/admin/order_list \
  -H "Authorization: Bearer your_password" | jq

# Update order
curl -X PATCH http://localhost:8787/api/admin/orders/42 \
  -H "Authorization: Bearer your_password" \
  -H "Content-Type: application/json" \
  -d '{"confirmed_after_creation": true}' | jq

# Delete order
curl -X DELETE http://localhost:8787/api/admin/orders/42 \
  -H "Authorization: Bearer your_password" | jq
```

### Test Menu Management
```bash
# Add menu item
curl -X POST http://localhost:8787/api/admin/menu_add \
  -H "Authorization: Bearer your_password" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Новое блюдо (150г)",
    "category": "Горячее",
    "description": "Описание ингредиентов блюда",
    "price": 1500,
    "image": "images/new-dish.jpg"
  }' | jq

# Update menu item
curl -X PUT http://localhost:8787/api/admin/menu_update/5 \
  -H "Authorization: Bearer your_password" \
  -H "Content-Type: application/json" \
  -d '{"price": 1600}' | jq

# Delete menu item
curl -X DELETE http://localhost:8787/api/admin/menu_delete/5 \
  -H "Authorization: Bearer your_password" | jq
```

---

## Response Formats

### Success Response
```json
{
  "success": true,
  "data": [...],
  "message": "Optional message"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message",
  "details": {}
}
```

---

## HTTP Status Codes

- **200** OK - Successful GET/PATCH/DELETE
- **201** Created - Successful POST
- **400** Bad Request - Invalid input
- **401** Unauthorized - Missing/invalid password
- **404** Not Found - Resource doesn't exist
- **500** Internal Server Error - Server error

---

## Important Notes

1. **Field naming**: Always use `item_id` (not `menu_item_id`)
2. **Cyrillic URLs**: Must be URL-encoded for category endpoints
3. **JSON encoding**: Use `ensure_ascii=False` to preserve Cyrillic
4. **Authentication**: Only admin endpoints require `Authorization` header
5. **Telegram**: Notifications sent only on order creation
6. **Price calculation**: Always from database, never trust frontend
