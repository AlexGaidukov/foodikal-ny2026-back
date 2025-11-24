# Admin Site - Promo Code Feature Implementation Guide

## Overview

The backend now supports promo code management with 3 new admin endpoints. This guide will help you implement the promo code management interface on the admin site.

---

## Backend Changes Summary

### What Changed:
- **New Feature**: Promo codes that give 5% discount on all orders
- **Database**: New `promo_codes` table created
- **Order Tracking**: Orders now store `promo_code`, `original_price`, `discount_amount`, `total_price`
- **Admin Endpoints**: 3 new endpoints for managing promo codes

---

## Admin Endpoints

All promo code endpoints require admin authentication using the same credentials as other admin endpoints.

### 1. Get All Promo Codes

**Endpoint**: `GET /api/admin/promo_codes`

**Headers**:
```
Authorization: Basic <base64_encoded_credentials>
```

**Response** (200 OK):
```json
{
  "success": true,
  "count": 2,
  "promo_codes": [
    {
      "code": "NEWYEAR2026",
      "created_at": "2025-11-16T12:30:45.000Z"
    },
    {
      "code": "SUMMER10",
      "created_at": "2025-11-15T10:20:30.000Z"
    }
  ]
}
```

**Example JavaScript**:
```javascript
async function getPromoCodes() {
  const credentials = btoa('admin:your_password');

  const response = await fetch('https://foodikal-ny-backend.x-gs-x.workers.dev/api/admin/promo_codes', {
    headers: {
      'Authorization': `Basic ${credentials}`
    }
  });

  const data = await response.json();
  return data.promo_codes;
}
```

---

### 2. Create New Promo Code

**Endpoint**: `POST /api/admin/promo_codes`

**Headers**:
```
Authorization: Basic <base64_encoded_credentials>
Content-Type: application/json
```

**Request Body**:
```json
{
  "code": "NEWYEAR2026"
}
```

**Validation Rules**:
- `code` is required
- Must be alphanumeric: Latin letters (A-Z), Cyrillic letters (А-Я, Ё), and numbers (0-9)
- Must be between 3-20 characters
- Case-sensitive (recommend using UPPERCASE for consistency)
- No spaces or special characters allowed

**Response** (201 Created):
```json
{
  "success": true,
  "code": "NEWYEAR2026",
  "message": "Promo code created successfully"
}
```

**Error Response** (400 Bad Request):
```json
{
  "success": false,
  "error": "Invalid promo code data",
  "details": {
    "code": "Promo code must be alphanumeric and 3-20 characters long"
  }
}
```

**Error Response** (400 Bad Request - Duplicate):
```json
{
  "success": false,
  "error": "Promo code already exists",
  "details": {
    "code": "Promo code already exists"
  }
}
```

**Example JavaScript**:
```javascript
async function createPromoCode(code) {
  const credentials = btoa('admin:your_password');

  const response = await fetch('https://foodikal-ny-backend.x-gs-x.workers.dev/api/admin/promo_codes', {
    method: 'POST',
    headers: {
      'Authorization': `Basic ${credentials}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ code })
  });

  const data = await response.json();

  if (!data.success) {
    throw new Error(data.error);
  }

  return data;
}
```

---

### 3. Delete Promo Code

**Endpoint**: `DELETE /api/admin/promo_codes/:code`

**URL Parameters**:
- `:code` - The promo code to delete (e.g., "NEWYEAR2026")

**Headers**:
```
Authorization: Basic <base64_encoded_credentials>
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Promo code deleted successfully"
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "error": "Promo code not found"
}
```

**Example JavaScript**:
```javascript
async function deletePromoCode(code) {
  const credentials = btoa('admin:your_password');

  const response = await fetch(
    `https://foodikal-ny-backend.x-gs-x.workers.dev/api/admin/promo_codes/${code}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Basic ${credentials}`
      }
    }
  );

  const data = await response.json();

  if (!data.success) {
    throw new Error(data.error);
  }

  return data;
}
```

---

## Order List Changes

The existing `GET /api/admin/order_list` endpoint now returns additional fields for orders that used promo codes:

```json
{
  "success": true,
  "orders": [
    {
      "id": 16,
      "customer_name": "Test User",
      "customer_contact": "+1234567890",
      "delivery_address": "123 Test Street, NY",
      "delivery_date": "2025-12-25",
      "comments": "Test order",
      "order_items": [...],
      "total_price": 494,
      "promo_code": "NEWYEAR2026",
      "original_price": 520,
      "discount_amount": 26,
      "confirmed_after_creation": false,
      "confirmed_before_delivery": false,
      "created_at": "2025-11-16T12:30:00.000Z",
      "updated_at": "2025-11-16T12:30:00.000Z"
    }
  ]
}
```

**New Fields** (only present when promo code was used):
- `promo_code` - The promo code that was applied (or empty string `""`)
- `original_price` - Price before discount (or same as `total_price` if no promo)
- `discount_amount` - Amount discounted (0 if no promo code)

---

## UI Implementation Suggestions

### 1. Promo Code Management Page

Create a new page or section in your admin panel for managing promo codes.

**Recommended Layout**:

```
┌─────────────────────────────────────────────┐
│  Promo Codes Management                     │
├─────────────────────────────────────────────┤
│                                             │
│  [Create New Promo Code]                    │
│  ┌─────────────────────┬─────────┐         │
│  │ Enter Code          │ CREATE  │         │
│  └─────────────────────┴─────────┘         │
│                                             │
│  Active Promo Codes (5% discount):          │
│  ┌───────────────────────────────────────┐ │
│  │ NEWYEAR2026      [Delete]             │ │
│  │ Created: 2025-11-16                   │ │
│  ├───────────────────────────────────────┤ │
│  │ SUMMER10         [Delete]             │ │
│  │ Created: 2025-11-15                   │ │
│  └───────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

**Features to Include**:
- List of all active promo codes with creation dates
- Input field to create new promo code
- Delete button for each promo code (with confirmation dialog)
- Validation feedback (show errors from API)
- Loading states for API calls
- Success/error notifications

---

### 2. Example React Component

```jsx
import React, { useState, useEffect } from 'react';

const PromoCodeManager = ({ credentials }) => {
  const [promoCodes, setPromoCodes] = useState([]);
  const [newCode, setNewCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load promo codes on mount
  useEffect(() => {
    loadPromoCodes();
  }, []);

  const loadPromoCodes = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        'https://foodikal-ny-backend.x-gs-x.workers.dev/api/admin/promo_codes',
        {
          headers: {
            'Authorization': `Basic ${credentials}`
          }
        }
      );
      const data = await response.json();
      if (data.success) {
        setPromoCodes(data.promo_codes);
      }
    } catch (err) {
      setError('Failed to load promo codes');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setError(null);

    // Validate input
    const code = newCode.trim().toUpperCase();
    if (code.length < 3 || code.length > 20) {
      setError('Code must be 3-20 characters');
      return;
    }
    if (!/^[A-Z0-9]+$/.test(code)) {
      setError('Code must be alphanumeric only');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        'https://foodikal-ny-backend.x-gs-x.workers.dev/api/admin/promo_codes',
        {
          method: 'POST',
          headers: {
            'Authorization': `Basic ${credentials}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ code })
        }
      );

      const data = await response.json();

      if (data.success) {
        setNewCode('');
        loadPromoCodes(); // Reload list
        alert('Promo code created successfully!');
      } else {
        setError(data.error || 'Failed to create promo code');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (code) => {
    if (!confirm(`Delete promo code "${code}"?`)) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        `https://foodikal-ny-backend.x-gs-x.workers.dev/api/admin/promo_codes/${code}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Basic ${credentials}`
          }
        }
      );

      const data = await response.json();

      if (data.success) {
        loadPromoCodes(); // Reload list
        alert('Promo code deleted successfully!');
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="promo-code-manager">
      <h2>Promo Code Management</h2>

      {/* Create Form */}
      <form onSubmit={handleCreate}>
        <input
          type="text"
          value={newCode}
          onChange={(e) => setNewCode(e.target.value.toUpperCase())}
          placeholder="Enter promo code (e.g., NEWYEAR2026)"
          disabled={loading}
          maxLength={20}
        />
        <button type="submit" disabled={loading || !newCode.trim()}>
          {loading ? 'Creating...' : 'Create Promo Code'}
        </button>
      </form>

      {/* Error Message */}
      {error && <div className="error">{error}</div>}

      {/* Promo Code List */}
      <div className="promo-list">
        <h3>Active Promo Codes (5% discount)</h3>
        {promoCodes.length === 0 ? (
          <p>No promo codes yet</p>
        ) : (
          <ul>
            {promoCodes.map((promo) => (
              <li key={promo.code}>
                <div>
                  <strong>{promo.code}</strong>
                  <span>Created: {new Date(promo.created_at).toLocaleDateString()}</span>
                </div>
                <button
                  onClick={() => handleDelete(promo.code)}
                  disabled={loading}
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default PromoCodeManager;
```

---

### 3. Order List Display Updates

Update your order list display to show promo code information when available:

```jsx
const OrderItem = ({ order }) => {
  const hasPromo = order.promo_code && order.discount_amount > 0;

  return (
    <div className="order-item">
      <h3>Order #{order.id}</h3>
      <p>Customer: {order.customer_name}</p>

      {/* Show promo code info if used */}
      {hasPromo && (
        <div className="promo-info">
          <span className="promo-badge">🎟 Promo: {order.promo_code}</span>
          <div className="price-breakdown">
            <p>Original Price: {order.original_price} RSD</p>
            <p className="discount">Discount: -{order.discount_amount} RSD</p>
          </div>
        </div>
      )}

      <p className="total">Total: {order.total_price} RSD</p>
    </div>
  );
};
```

---

## Validation Rules & Best Practices

### Promo Code Format:
- ✅ Latin letters (A-Z, a-z)
- ✅ Cyrillic letters (А-Я, а-я, Ё, ё)
- ✅ Numbers (0-9)
- ✅ 3-20 characters
- ✅ Case-sensitive (recommend UPPERCASE for consistency)
- ❌ No spaces or special characters (no hyphens, underscores, etc.)

### Valid Examples (Latin):
- `NEWYEAR2026` ✅
- `SUMMER10` ✅
- `FLASH50` ✅
- `TEST123` ✅

### Valid Examples (Cyrillic):
- `НОВЫЙГОД2026` ✅ (New Year 2026)
- `СКИДКА10` ✅ (Discount 10)
- `ЗИМА2026` ✅ (Winter 2026)
- `ПОДАРОК` ✅ (Gift)

### Valid Examples (Mixed):
- `НОВЫЙ2026` ✅ (Latin numbers + Cyrillic)
- `SALE10РУБ` ✅ (Latin + Cyrillic)

### Invalid Examples:
- `НГ` ❌ (too short - only 2 characters)
- `NY 2026` ❌ (contains space)
- `SALE-10` ❌ (contains hyphen)
- `НОВЫЙ-ГОД` ❌ (contains hyphen)
- `VERYLONGPROMOCODETHATEXCEEDS20CHARS` ❌ (too long)

### Recommendations:
1. **Always convert to uppercase** in the UI for consistency
2. **Show validation errors** immediately as user types
3. **Confirm before deleting** a promo code
4. **Show creation date** so you can track when codes were created
5. **Consider adding notes** (future feature) to track why codes were created

---

## Testing Your Implementation

### Test Case 1: Create Promo Code
1. Open the promo code management page
2. Enter code: `TEST2026`
3. Click "Create"
4. ✅ Should see success message
5. ✅ Code should appear in the list

### Test Case 2: Create Duplicate
1. Try to create `TEST2026` again
2. ✅ Should see error: "Promo code already exists"

### Test Case 3: Invalid Format
1. Try to create `AB` (too short)
2. ✅ Should see validation error
3. Try to create `TEST-CODE` (special char)
4. ✅ Should see validation error

### Test Case 4: Delete Promo Code
1. Click delete on a promo code
2. Confirm the dialog
3. ✅ Code should be removed from list

### Test Case 5: View Order with Promo
1. Create a test order with promo code from the public site
2. View order in admin panel
3. ✅ Should see promo code, original price, discount, and final price

---

## Security Notes

1. **Authentication Required**: All promo code endpoints require admin authentication
2. **Same Credentials**: Use the same admin credentials as other admin endpoints
3. **HTTPS Only**: Always use HTTPS in production
4. **Input Validation**: Backend validates all inputs, but frontend should also validate for better UX

---

## Example API Integration Class

```javascript
class PromoCodeAPI {
  constructor(baseURL, credentials) {
    this.baseURL = baseURL;
    this.credentials = credentials;
  }

  getHeaders(includeContentType = false) {
    const headers = {
      'Authorization': `Basic ${this.credentials}`
    };
    if (includeContentType) {
      headers['Content-Type'] = 'application/json';
    }
    return headers;
  }

  async getAll() {
    const response = await fetch(`${this.baseURL}/api/admin/promo_codes`, {
      headers: this.getHeaders()
    });
    return await response.json();
  }

  async create(code) {
    const response = await fetch(`${this.baseURL}/api/admin/promo_codes`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify({ code })
    });
    return await response.json();
  }

  async delete(code) {
    const response = await fetch(
      `${this.baseURL}/api/admin/promo_codes/${code}`,
      {
        method: 'DELETE',
        headers: this.getHeaders()
      }
    );
    return await response.json();
  }
}

// Usage:
const api = new PromoCodeAPI(
  'https://foodikal-ny-backend.x-gs-x.workers.dev',
  btoa('admin:your_password')
);

// Get all promo codes
const codes = await api.getAll();

// Create new promo code
await api.create('NEWYEAR2026');

// Delete promo code
await api.delete('NEWYEAR2026');
```

---

## Important Notes

1. **Discount is Fixed**: All promo codes give exactly 5% discount. This is not configurable per code.
2. **No Expiration**: Promo codes don't expire automatically. You must manually delete them.
3. **Unlimited Uses**: Promo codes can be used unlimited times by different customers.
4. **No Minimum Order**: Promo codes work on any order amount.
5. **Case Sensitive**: Promo codes are case-sensitive in the database.

---

## Questions?

If you encounter any issues or need additional features:
- Check the backend logs for detailed error messages
- Verify admin credentials are correct
- Ensure CORS is properly configured for your admin domain
- Test endpoints with curl or Postman first to isolate frontend issues
