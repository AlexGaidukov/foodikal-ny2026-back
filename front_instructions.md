# Foodikal NY Backend - Frontend Integration Guide

## Base URL

**Production**: `https://foodikal-ny-backend.x-gs-x.workers.dev`

## CORS Configuration

The API is configured to accept requests from:
- Origin: `https://ny2026.foodikal.rs`
- Methods: `GET, POST, OPTIONS`
- Headers: `Content-Type, Authorization`

## Public Endpoints

### 1. Get All Menu Items

Fetch all menu items grouped by category.

**Endpoint**: `GET /api/menu`

**Request**:
```javascript
fetch('https://foodikal-ny-backend.x-gs-x.workers.dev/api/menu')
  .then(response => response.json())
  .then(data => console.log(data));
```

**Response** (200 OK):
```json
{
  "success": true,
  "grouped_menu": {
    "Брускетты": [
      {
        "id": 1,
        "name": "Брускетта с помидорами",
        "category": "Брускетты",
        "description": "Свежие помидоры с базиликом",
        "price": 1850,
        "image": "bruschetta_tomato.jpg"
      }
    ],
    "Горячее": [...],
    "Закуски": [...],
    "Канапе": [...],
    "Салат": [...],
    "Тарталетки": [...]
  },
  "total_items": 8
}
```

**Categories** (in order):
- Брускетты (Bruschetta)
- Горячее (Hot dishes)
- Закуски (Appetizers)
- Канапе (Canapes)
- Салат (Salads)
- Тарталетки (Tartlets)

---

### 2. Get Menu Items by Category

Fetch menu items filtered by a specific category.

**Endpoint**: `GET /api/menu/category/:category`

**URL Parameters**:
- `category` - Category name in Cyrillic (must be URL-encoded)

**Request Examples**:
```javascript
// For "Горячее" category
const category = encodeURIComponent('Горячее');
fetch(`https://foodikal-ny-backend.x-gs-x.workers.dev/api/menu/category/${category}`)
  .then(response => response.json())
  .then(data => console.log(data));

// Alternative approach using URLSearchParams
const params = new URLSearchParams({ category: 'Горячее' });
const categoryEncoded = params.get('category');
fetch(`https://foodikal-ny-backend.x-gs-x.workers.dev/api/menu/category/${categoryEncoded}`)
  .then(response => response.json())
  .then(data => console.log(data));
```

**Response** (200 OK):
```json
{
  "success": true,
  "category": "Горячее",
  "items": [
    {
      "id": 2,
      "name": "Мини-пицца",
      "category": "Горячее",
      "description": "Маленькая пицца с сыром",
      "price": 280,
      "image": "mini_pizza.jpg"
    },
    {
      "id": 6,
      "name": "Крокеты",
      "category": "Горячее",
      "description": "Хрустящие крокеты",
      "price": 1300,
      "image": "croquettes.jpg"
    }
  ],
  "count": 2
}
```

**Error Response** (400 Bad Request):
```json
{
  "success": false,
  "error": "Category parameter is required"
}
```

---

### 3. Create Order

Create a new customer order.

**Endpoint**: `POST /api/create_order`

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "customer_name": "Иван Иванов",
  "customer_contact": "+1234567890",
  "customer_email": "ivan@example.com",
  "delivery_address": "Нью-Йорк, улица Тест, 123",
  "comments": "Позвонить за 30 минут",
  "order_items": [
    {
      "item_id": 1,
      "quantity": 2
    },
    {
      "item_id": 3,
      "quantity": 1
    }
  ]
}
```

**Request Example**:
```javascript
const orderData = {
  customer_name: "Иван Иванов",
  customer_contact: "+1234567890",
  customer_email: "ivan@example.com",  // Optional
  delivery_address: "Нью-Йорк, улица Тест, 123",
  comments: "Позвонить за 30 минут",   // Optional
  order_items: [
    { item_id: 1, quantity: 2 },
    { item_id: 3, quantity: 1 }
  ]
};

fetch('https://foodikal-ny-backend.x-gs-x.workers.dev/api/create_order', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(orderData)
})
  .then(response => response.json())
  .then(data => console.log(data));
```

**Field Requirements**:

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `customer_name` | ✅ Yes | string | Customer full name (2-100 chars) |
| `customer_contact` | ✅ Yes | string | Phone number (10-20 chars) |
| `customer_email` | ❌ No | string | Email address |
| `delivery_address` | ✅ Yes | string | Full delivery address (5-200 chars) |
| `comments` | ❌ No | string | Order comments/notes |
| `order_items` | ✅ Yes | array | Array of items (1-50 items) |
| `order_items[].item_id` | ✅ Yes | integer | Menu item ID |
| `order_items[].quantity` | ✅ Yes | integer | Quantity (1-100) |

**Response** (200 OK):
```json
{
  "success": true,
  "order_id": 3,
  "total_price": 31300,
  "message": "Order created successfully"
}
```

**Important Notes**:
- **Prices are calculated server-side** - do not send price from frontend
- Total price is calculated from database prices (security feature)
- Telegram notification is automatically sent to manager
- Empty strings for optional fields are acceptable

**Validation Error Response** (400 Bad Request):
```json
{
  "success": false,
  "error": "Invalid order data",
  "details": {
    "customer_name": ["Required field"],
    "order_items": ["Must contain at least 1 item"]
  }
}
```

**Not Found Error** (404 Not Found):
```json
{
  "success": false,
  "error": "Menu items not found",
  "details": {
    "invalid_ids": [999]
  }
}
```

---

## Error Handling

All endpoints return consistent error format:

```json
{
  "success": false,
  "error": "Error message here",
  "details": { /* Optional additional details */ }
}
```

**HTTP Status Codes**:
- `200` - Success
- `400` - Bad Request (validation error)
- `404` - Not Found (invalid item IDs)
- `500` - Internal Server Error

**Example Error Handling**:
```javascript
fetch(url, options)
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  })
  .then(data => {
    if (data.success) {
      // Handle success
      console.log('Success:', data);
    } else {
      // Handle API error
      console.error('API Error:', data.error);
      if (data.details) {
        console.error('Details:', data.details);
      }
    }
  })
  .catch(error => {
    // Handle network error
    console.error('Network Error:', error);
  });
```

---

## Cyrillic Character Support

All text fields support Cyrillic characters (Russian). The API uses UTF-8 encoding.

**Important**: When filtering by category, always URL-encode Cyrillic characters:

```javascript
// ✅ Correct
const category = encodeURIComponent('Горячее');
// Result: %D0%93%D0%BE%D1%80%D1%8F%D1%87%D0%B5%D0%B5

// ❌ Incorrect (will not work)
fetch('/api/menu/category/Горячее');
```

---

## Complete Integration Example

```javascript
class FoodikalAPI {
  constructor() {
    this.baseURL = 'https://foodikal-ny-backend.x-gs-x.workers.dev';
  }

  async getMenu() {
    try {
      const response = await fetch(`${this.baseURL}/api/menu`);
      const data = await response.json();

      if (data.success) {
        return data.grouped_menu;
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      console.error('Failed to fetch menu:', error);
      throw error;
    }
  }

  async getMenuByCategory(category) {
    try {
      const encodedCategory = encodeURIComponent(category);
      const response = await fetch(
        `${this.baseURL}/api/menu/category/${encodedCategory}`
      );
      const data = await response.json();

      if (data.success) {
        return data.items;
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      console.error('Failed to fetch category:', error);
      throw error;
    }
  }

  async createOrder(orderData) {
    try {
      const response = await fetch(`${this.baseURL}/api/create_order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData)
      });

      const data = await response.json();

      if (data.success) {
        return {
          orderId: data.order_id,
          totalPrice: data.total_price
        };
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      console.error('Failed to create order:', error);
      throw error;
    }
  }
}

// Usage
const api = new FoodikalAPI();

// Get all menu items
api.getMenu()
  .then(menu => console.log('Menu:', menu))
  .catch(error => console.error(error));

// Get items by category
api.getMenuByCategory('Горячее')
  .then(items => console.log('Hot dishes:', items))
  .catch(error => console.error(error));

// Create order
const order = {
  customer_name: "Иван Иванов",
  customer_contact: "+1234567890",
  customer_email: "ivan@example.com",
  delivery_address: "Нью-Йорк, улица Тест, 123",
  comments: "Позвонить за 30 минут",
  order_items: [
    { item_id: 1, quantity: 2 },
    { item_id: 3, quantity: 1 }
  ]
};

api.createOrder(order)
  .then(result => {
    console.log('Order created!');
    console.log('Order ID:', result.orderId);
    console.log('Total:', result.totalPrice, 'RSD');
  })
  .catch(error => console.error(error));
```

---

## Testing

Use browser DevTools or tools like Postman/curl to test:

```bash
# Get menu
curl https://foodikal-ny-backend.x-gs-x.workers.dev/api/menu

# Get category (URL-encoded)
curl "https://foodikal-ny-backend.x-gs-x.workers.dev/api/menu/category/%D0%93%D0%BE%D1%80%D1%8F%D1%87%D0%B5%D0%B5"

# Create order
curl -X POST https://foodikal-ny-backend.x-gs-x.workers.dev/api/create_order \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test User",
    "customer_contact": "+1234567890",
    "delivery_address": "Test Address 123",
    "order_items": [{"item_id": 1, "quantity": 2}]
  }'
```

---

## Support

For issues or questions, contact the backend team or check the repository at the project location.
