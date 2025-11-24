# Customer Frontend - Promo Code Feature Implementation Guide

## Overview

The backend now supports promo codes that give customers a **5% discount** on their orders. This guide will help you add the promo code functionality to the customer order form.

### Promo Code Format Support

Promo codes now support:
- ✅ **Latin letters**: A-Z, a-z
- ✅ **Cyrillic letters**: А-Я, а-я, Ё, ё
- ✅ **Numbers**: 0-9
- ✅ **Length**: 3-20 characters
- ❌ **No special characters** (no spaces, hyphens, underscores, etc.)

**Valid Examples:**
- Latin: `NEWYEAR2026`, `SUMMER10`, `FLASH50`
- Cyrillic: `НОВЫЙГОД2026`, `СКИДКА10`, `ЗИМА2026`
- Mixed: `НОВЫЙ2026`, `SALE10РУБ`

**Invalid Examples:**
- `НГ` ❌ (too short)
- `НОВЫЙ-ГОД` ❌ (contains hyphen)
- `SALE 10` ❌ (contains space)

---

## What Changed in the API

### Order Creation Endpoint

**Endpoint**: `POST /api/create_order`

The order creation endpoint now accepts an optional `promo_code` field.

**Updated Request Body**:
```json
{
  "customer_name": "Иван Иванов",
  "customer_contact": "+1234567890",
  "delivery_address": "Нью-Йорк, улица Тест, 123",
  "delivery_date": "2025-12-25",
  "comments": "Позвонить за 30 минут",
  "promo_code": "NEWYEAR2026",
  "order_items": [
    {
      "item_id": 1,
      "quantity": 2
    }
  ]
}
```

**New Field**:
- `promo_code` (optional, string): The promo code to apply for 5% discount
  - Accepts Latin letters (A-Z), Cyrillic letters (А-Я, Ё), and numbers (0-9)
  - Must be 3-20 characters
  - Case-sensitive (recommend using UPPERCASE)
  - Examples: `NEWYEAR2026`, `НОВЫЙГОД2026`, `СКИДКА10`

---

## API Response Changes

### Success Response (with promo code)

When a valid promo code is used, the response includes additional discount information:

```json
{
  "success": true,
  "order_id": 16,
  "total_price": 494,
  "message": "Order created successfully",
  "original_price": 520,
  "discount_amount": 26,
  "promo_code": "NEWYEAR2026"
}
```

**New Fields** (only present when promo code is applied):
- `original_price`: Price before discount
- `discount_amount`: Amount discounted (5% of original price)
- `promo_code`: The promo code that was applied

### Success Response (without promo code)

When no promo code is used, the response remains the same as before:

```json
{
  "success": true,
  "order_id": 17,
  "total_price": 600,
  "message": "Order created successfully"
}
```

### Error Responses

**Invalid Promo Code Format** (400 Bad Request):
```json
{
  "success": false,
  "error": "Invalid promo code format"
}
```

**Promo Code Not Found** (400 Bad Request):
```json
{
  "success": false,
  "error": "Promo code not found",
  "details": {
    "promo_code": "Invalid promo code"
  }
}
```

---

## UI Implementation

### 1. Add Promo Code Input to Order Form

Add an optional promo code input field to your order form. Recommended placement: **after order items, before or near the total price**.

**Recommended Layout**:

```
┌─────────────────────────────────────────────┐
│  Your Order                                 │
├─────────────────────────────────────────────┤
│  [Order items list...]                      │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │ 💬 Have a promo code?                │  │
│  │ ┌─────────────────┬────────────┐     │  │
│  │ │ Enter code      │ [Apply]    │     │  │
│  │ └─────────────────┴────────────┘     │  │
│  │ ✅ Promo code applied: -26 RSD       │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  Subtotal:        520 RSD                   │
│  Discount (5%):   -26 RSD                   │
│  ────────────────────────                   │
│  Total:           494 RSD                   │
│                                             │
│  [Place Order]                              │
└─────────────────────────────────────────────┘
```

---

### 2. Example React Component

```jsx
import React, { useState, useEffect } from 'react';

const OrderForm = () => {
  // Order form state
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_contact: '',
    delivery_address: '',
    delivery_date: '',
    comments: '',
    order_items: []
  });

  // Promo code state
  const [promoCode, setPromoCode] = useState('');
  const [promoApplied, setPromoApplied] = useState(false);
  const [promoError, setPromoError] = useState('');
  const [appliedPromo, setAppliedPromo] = useState(null);

  // Calculate prices
  const calculateSubtotal = () => {
    return formData.order_items.reduce((total, item) => {
      return total + (item.price * item.quantity);
    }, 0);
  };

  const subtotal = calculateSubtotal();
  const discount = appliedPromo ? Math.floor(subtotal * 0.05) : 0;
  const total = subtotal - discount;

  // Handle promo code input
  const handlePromoChange = (e) => {
    const value = e.target.value.toUpperCase();
    setPromoCode(value);
    setPromoError('');

    // Clear applied promo if user modifies the code
    if (promoApplied && value !== appliedPromo) {
      setPromoApplied(false);
      setAppliedPromo(null);
    }
  };

  // Apply promo code (optional: validate before submitting order)
  const handleApplyPromo = () => {
    const trimmedCode = promoCode.trim();

    if (!trimmedCode) {
      setPromoError('Please enter a promo code');
      return;
    }

    // Validate format (optional client-side validation)
    if (trimmedCode.length < 3 || trimmedCode.length > 20) {
      setPromoError('Promo code must be 3-20 characters');
      return;
    }

    if (!/^[A-Za-zА-Яа-яЁё0-9]+$/.test(trimmedCode)) {
      setPromoError('Promo code must be alphanumeric (Latin/Cyrillic letters and numbers)');
      return;
    }

    // Mark as applied (will be validated on server)
    setPromoApplied(true);
    setAppliedPromo(trimmedCode);
    setPromoError('');
  };

  // Submit order
  const handleSubmit = async (e) => {
    e.preventDefault();

    const orderData = {
      ...formData,
      ...(appliedPromo && { promo_code: appliedPromo })
    };

    try {
      const response = await fetch(
        'https://foodikal-ny-cors-wrapper.x-gs-x.workers.dev/api/create_order',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(orderData)
        }
      );

      const data = await response.json();

      if (data.success) {
        // Show success message
        if (data.promo_code) {
          alert(
            `Order placed successfully!\n` +
            `Original price: ${data.original_price} RSD\n` +
            `Discount: -${data.discount_amount} RSD\n` +
            `Total: ${data.total_price} RSD\n` +
            `Promo code: ${data.promo_code}`
          );
        } else {
          alert(`Order placed successfully! Total: ${data.total_price} RSD`);
        }

        // Reset form...
      } else {
        // Handle error
        if (data.error === 'Promo code not found') {
          setPromoError('Invalid promo code');
          setPromoApplied(false);
          setAppliedPromo(null);
        } else {
          alert(`Error: ${data.error}`);
        }
      }
    } catch (error) {
      alert('Network error. Please try again.');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Customer info fields */}
      <input
        type="text"
        placeholder="Your name"
        value={formData.customer_name}
        onChange={(e) => setFormData({...formData, customer_name: e.target.value})}
        required
      />

      <input
        type="tel"
        placeholder="Contact number"
        value={formData.customer_contact}
        onChange={(e) => setFormData({...formData, customer_contact: e.target.value})}
        required
      />

      <input
        type="text"
        placeholder="Delivery address"
        value={formData.delivery_address}
        onChange={(e) => setFormData({...formData, delivery_address: e.target.value})}
        required
      />

      <input
        type="date"
        value={formData.delivery_date}
        onChange={(e) => setFormData({...formData, delivery_date: e.target.value})}
        required
      />

      <textarea
        placeholder="Comments (optional)"
        value={formData.comments}
        onChange={(e) => setFormData({...formData, comments: e.target.value})}
      />

      {/* Order items would be displayed here */}

      {/* PROMO CODE SECTION */}
      <div className="promo-section">
        <h3>💬 Have a promo code?</h3>
        <div className="promo-input-group">
          <input
            type="text"
            placeholder="Enter promo code"
            value={promoCode}
            onChange={handlePromoChange}
            maxLength={20}
            style={{
              textTransform: 'uppercase'
            }}
          />
          <button
            type="button"
            onClick={handleApplyPromo}
            disabled={!promoCode.trim() || promoApplied}
          >
            {promoApplied ? '✓ Applied' : 'Apply'}
          </button>
        </div>

        {/* Error message */}
        {promoError && (
          <div className="promo-error" style={{ color: 'red' }}>
            {promoError}
          </div>
        )}

        {/* Success message */}
        {promoApplied && !promoError && (
          <div className="promo-success" style={{ color: 'green' }}>
            ✅ Promo code "{appliedPromo}" applied! You save {discount} RSD
          </div>
        )}
      </div>

      {/* PRICE BREAKDOWN */}
      <div className="price-summary">
        <div className="price-row">
          <span>Subtotal:</span>
          <span>{subtotal} RSD</span>
        </div>

        {promoApplied && discount > 0 && (
          <div className="price-row discount">
            <span>Discount (5%):</span>
            <span>-{discount} RSD</span>
          </div>
        )}

        <div className="price-row total">
          <strong>Total:</strong>
          <strong>{total} RSD</strong>
        </div>
      </div>

      <button type="submit">Place Order</button>
    </form>
  );
};

export default OrderForm;
```

---

### 3. Simpler Implementation (No Client-Side Validation)

If you prefer a simpler approach without pre-validation:

```jsx
const SimplePromoCode = ({ onPromoChange }) => {
  const [code, setCode] = useState('');

  const handleChange = (e) => {
    const value = e.target.value.toUpperCase();
    setCode(value);
    onPromoChange(value);
  };

  return (
    <div className="promo-code-input">
      <label>Promo Code (optional)</label>
      <input
        type="text"
        value={code}
        onChange={handleChange}
        placeholder="Enter promo code"
        maxLength={20}
        style={{ textTransform: 'uppercase' }}
      />
      <small>Enter your promo code to get 5% discount</small>
    </div>
  );
};

// Usage in order form:
<SimplePromoCode
  onPromoChange={(code) => setFormData({...formData, promo_code: code})}
/>

// Optional: Add Cyrillic placeholder
<input
  type="text"
  value={code}
  onChange={handleChange}
  placeholder="Enter code / Введите промокод"
  maxLength={20}
  style={{ textTransform: 'uppercase' }}
/>
```

---

### 4. Vanilla JavaScript Example

```javascript
// HTML
<div class="promo-section">
  <label for="promo-code">Promo Code (optional)</label>
  <input
    type="text"
    id="promo-code"
    maxlength="20"
    placeholder="Enter promo code"
    style="text-transform: uppercase;"
  />
  <span class="promo-feedback"></span>
</div>

<div class="price-summary">
  <div>Subtotal: <span id="subtotal">0</span> RSD</div>
  <div id="discount-row" style="display: none;">
    Discount (5%): -<span id="discount">0</span> RSD
  </div>
  <div><strong>Total: <span id="total">0</span> RSD</strong></div>
</div>

// JavaScript
const promoInput = document.getElementById('promo-code');
const promoFeedback = document.querySelector('.promo-feedback');
const discountRow = document.getElementById('discount-row');

// Auto-uppercase
promoInput.addEventListener('input', (e) => {
  e.target.value = e.target.value.toUpperCase();
});

// Calculate and display prices
function updatePrices(subtotal, hasPromo, promoCode) {
  const discount = hasPromo ? Math.floor(subtotal * 0.05) : 0;
  const total = subtotal - discount;

  document.getElementById('subtotal').textContent = subtotal;
  document.getElementById('discount').textContent = discount;
  document.getElementById('total').textContent = total;

  if (discount > 0) {
    discountRow.style.display = 'block';
  } else {
    discountRow.style.display = 'none';
  }
}

// Submit order
async function submitOrder(formData) {
  const promoCode = promoInput.value.trim();

  if (promoCode) {
    formData.promo_code = promoCode;
  }

  const response = await fetch(
    'https://foodikal-ny-cors-wrapper.x-gs-x.workers.dev/api/create_order',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    }
  );

  const data = await response.json();

  if (data.success) {
    if (data.promo_code) {
      promoFeedback.textContent = `✓ ${data.discount_amount} RSD saved!`;
      promoFeedback.style.color = 'green';
    }
    alert(`Order placed! Total: ${data.total_price} RSD`);
  } else if (data.error === 'Promo code not found') {
    promoFeedback.textContent = '✗ Invalid promo code';
    promoFeedback.style.color = 'red';
  } else {
    alert(`Error: ${data.error}`);
  }
}
```

---

## UI/UX Best Practices

### 1. Input Field Design

**Do:**
- ✅ Auto-convert to uppercase for consistency
- ✅ Show character limit (max 20 characters)
- ✅ Optional field - don't make it required
- ✅ Provide clear label: "Promo Code" or "Discount Code"
- ✅ Use placeholder: "Enter promo code"

**Don't:**
- ❌ Don't show promo input if cart is empty
- ❌ Don't hide the field - keep it visible but optional
- ❌ Don't use confusing labels like "Coupon" if backend calls it "Promo Code"

### 2. Visual Feedback

**Success State:**
```
✅ Promo code "NEWYEAR2026" applied! You save 26 RSD
```

**Error State:**
```
✗ Invalid promo code. Please check and try again.
```

**Empty State:**
```
💬 Have a promo code? Enter it here to save 5%
```

### 3. Price Display

Always show the breakdown when promo is applied:

```
Subtotal:        520 RSD
Discount (5%):   -26 RSD
─────────────────────
Total:           494 RSD
```

### 4. Mobile Considerations

- Use larger tap targets for "Apply" button
- Consider placing promo code input in an expandable section
- Keep the promo input above the "Place Order" button

---

## Client-Side Validation (Optional)

You can add client-side validation for better UX, but remember the backend will validate anyway.

```javascript
function validatePromoCode(code) {
  const trimmed = code.trim();

  // Empty is OK (optional field)
  if (!trimmed) {
    return { valid: true, error: null };
  }

  // Length check
  if (trimmed.length < 3) {
    return { valid: false, error: 'Promo code too short (minimum 3 characters)' };
  }

  if (trimmed.length > 20) {
    return { valid: false, error: 'Promo code too long (maximum 20 characters)' };
  }

  // Format check (supports Latin, Cyrillic, and numbers)
  if (!/^[A-Za-zА-Яа-яЁё0-9]+$/.test(trimmed)) {
    return { valid: false, error: 'Promo code must contain only letters (Latin/Cyrillic) and numbers' };
  }

  return { valid: true, error: null };
}

// Usage
const validation = validatePromoCode(promoInput.value);
if (!validation.valid) {
  showError(validation.error);
}
```

---

## Styling Examples

### CSS for Promo Section

```css
.promo-section {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin: 20px 0;
}

.promo-section h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #6c757d;
}

.promo-input-group {
  display: flex;
  gap: 8px;
}

.promo-input-group input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  text-transform: uppercase;
  font-family: monospace;
}

.promo-input-group button {
  padding: 10px 20px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.promo-input-group button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.promo-success {
  margin-top: 8px;
  color: #28a745;
  font-size: 14px;
}

.promo-error {
  margin-top: 8px;
  color: #dc3545;
  font-size: 14px;
}

/* Price breakdown */
.price-summary {
  margin: 20px 0;
  padding: 16px;
  background: #fff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
}

.price-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
}

.price-row.discount {
  color: #28a745;
}

.price-row.total {
  border-top: 2px solid #000;
  padding-top: 12px;
  margin-top: 8px;
  font-size: 18px;
}
```

---

## Testing Your Implementation

### Test Case 1: Valid Promo Code (Latin)
1. Fill out the order form
2. Enter promo code: `NEWYEAR2026`
3. Click "Apply" (if you have Apply button)
4. ✅ Should show discount amount
5. Submit order
6. ✅ Should receive confirmation with discount details

### Test Case 1b: Valid Promo Code (Cyrillic)
1. Fill out the order form
2. Enter promo code: `НОВЫЙГОД2026`
3. Click "Apply" (if you have Apply button)
4. ✅ Should show discount amount
5. Submit order
6. ✅ Should receive confirmation with discount details

### Test Case 2: Invalid Promo Code
1. Fill out the order form
2. Enter promo code: `INVALID123`
3. Submit order
4. ✅ Should show error: "Promo code not found"

### Test Case 3: No Promo Code
1. Fill out the order form
2. Leave promo code field empty
3. Submit order
4. ✅ Should work normally without discount

### Test Case 4: Invalid Format
1. Enter: `AB` (too short)
2. ✅ Should show validation error (if client-side validation)
3. Enter: `TEST-CODE` (special character)
4. ✅ Should show validation error
5. Enter: `НОВЫЙ-ГОД` (Cyrillic with hyphen)
6. ✅ Should show validation error

### Test Case 5: Empty Cart
1. Try to apply promo code with no items
2. ✅ Discount should be 0 RSD (5% of 0 is 0)

---

## Important Notes

### Discount Calculation
- Discount is **always 5%** of the subtotal
- Calculation: `discount = floor(subtotal * 0.05)`
- Uses integer math (no decimal places)
- Example: 520 RSD → 26 RSD discount (5%)

### Cyrillic Character Support
- Promo codes fully support **Cyrillic characters** (Russian/Serbian letters)
- No special handling needed - users can type Cyrillic naturally
- The backend validates and stores Cyrillic correctly with UTF-8 encoding
- Make sure your HTML has `<meta charset="UTF-8">` for proper display
- Client-side validation pattern: `/^[A-Za-zА-Яа-яЁё0-9]+$/`
- Consider adding Cyrillic placeholder text for Russian-speaking users:
  ```html
  <input placeholder="Enter code / Введите промокод" />
  ```
- Both Latin and Cyrillic codes work: `NEWYEAR2026` or `НОВЫЙГОД2026`

### Backend Behavior
- Promo code validation happens on the server
- Backend calculates the actual prices (don't trust client-side calculations)
- Invalid promo codes return 400 error
- Empty/missing promo code is perfectly fine (optional field)

### CORS Configuration
- Remember to use the CORS wrapper URL: `https://foodikal-ny-cors-wrapper.x-gs-x.workers.dev`
- Your frontend domain must be in the allowed origins list

### Security
- Never expose promo code creation to customers
- All promo codes are managed by admins only
- Promo codes are case-sensitive

---

## Complete API Integration Example

```javascript
class OrderAPI {
  constructor() {
    this.baseURL = 'https://foodikal-ny-cors-wrapper.x-gs-x.workers.dev';
  }

  async createOrder(orderData) {
    try {
      const response = await fetch(`${this.baseURL}/api/create_order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(orderData)
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to create order');
      }

      return {
        orderId: data.order_id,
        totalPrice: data.total_price,
        originalPrice: data.original_price,
        discountAmount: data.discount_amount,
        promoCode: data.promo_code,
        hasDiscount: !!data.promo_code
      };
    } catch (error) {
      console.error('Order creation failed:', error);
      throw error;
    }
  }

  calculateDiscount(subtotal, hasPromo) {
    return hasPromo ? Math.floor(subtotal * 0.05) : 0;
  }
}

// Usage
const api = new OrderAPI();

// Create order with promo code
const result = await api.createOrder({
  customer_name: "Test User",
  customer_contact: "+1234567890",
  delivery_address: "123 Test St",
  delivery_date: "2025-12-25",
  promo_code: "NEWYEAR2026",
  order_items: [
    { item_id: 1, quantity: 2 }
  ]
});

if (result.hasDiscount) {
  console.log(`Saved ${result.discountAmount} RSD with promo code ${result.promoCode}!`);
}
```

---

## Frequently Asked Questions

**Q: Can customers create their own promo codes?**
A: No. Only admins can create promo codes through the admin panel.

**Q: Do promo codes expire?**
A: No automatic expiration. Admins must manually delete codes when they should no longer be valid.

**Q: Can a customer use multiple promo codes?**
A: No. Only one promo code per order.

**Q: What's the minimum order amount for promo codes?**
A: No minimum. Promo codes work on any order amount.

**Q: Is the discount percentage configurable?**
A: No. All promo codes give exactly 5% discount.

**Q: Are promo codes case-sensitive?**
A: Yes, but you should convert input to uppercase for consistency.

**Q: What happens if the backend rejects the promo code?**
A: You'll receive a 400 error with message "Promo code not found". Show this error to the user and let them correct it.

---

## Next Steps

1. Add the promo code input field to your order form
2. Update your price calculation to show discount
3. Include promo_code in the order submission payload
4. Handle the additional response fields (original_price, discount_amount)
5. Test with test promo codes: `NEWYEAR2026` (Latin) or `НОВЫЙГОД2026` (Cyrillic)
6. Update your order confirmation/success page to show discount details
7. Ensure your page has proper UTF-8 encoding (`<meta charset="UTF-8">`) for Cyrillic support

---

## Need Help?

- Check browser console for API errors
- Verify you're using the CORS wrapper URL
- Test the API directly with curl or Postman first
- Make sure promo codes exist in the database (ask admin to create test codes)
