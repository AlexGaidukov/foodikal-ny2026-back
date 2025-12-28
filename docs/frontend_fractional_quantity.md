# Frontend: Fractional Quantity Support

## Overview

Some menu items (large salads sold by kg) now support fractional quantities in 0.5 kg increments. The frontend needs to detect these items and provide an appropriate UI for quantity selection.

---

## API Changes

### Menu Response

Each menu item now includes 4 new fields:

```json
{
  "id": 41,
  "name": "Оливье с говядиной (1 кг)",
  "category": "Салаты",
  "price": 2200,
  "description": "...",
  "image": "...",
  "allow_fractional": 1,
  "quantity_step": 0.5,
  "min_quantity": 1,
  "unit": "кг"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `allow_fractional` | `0` or `1` | Whether item supports decimal quantities |
| `quantity_step` | `number` | Increment size (e.g., `0.5` means 1, 1.5, 2, 2.5...) |
| `min_quantity` | `number` | Minimum allowed quantity (e.g., `1`) |
| `unit` | `string` | Display unit (`"кг"` or `"шт"`) |

### Order Request

Quantity can now be a decimal for fractional items:

```json
{
  "order_items": [
    {"item_id": 41, "quantity": 1.5},
    {"item_id": 37, "quantity": 2}
  ]
}
```

---

## Currently Enabled Items

| ID | Name | Step | Min | Unit |
|----|------|------|-----|------|
| 38 | Крабовый салат (1 кг) | 0.5 | 1 | кг |
| 39 | Селёдка под Шубой (1 кг) | 0.5 | 1 | кг |
| 41 | Оливье с говядиной (1 кг) | 0.5 | 1 | кг |

---

## UI Implementation

### 1. Detect Fractional Items

```typescript
const isFractional = (item: MenuItem): boolean => {
  return item.allow_fractional === 1;
};
```

### 2. Quantity Selector Logic

**For regular items** (`allow_fractional === 0`):
- Standard +/- buttons with integer steps
- Min: 1, Step: 1

**For fractional items** (`allow_fractional === 1`):
- +/- buttons with `quantity_step` increments
- Min: `min_quantity` (typically 1)
- Display with one decimal place

```typescript
// Increment/decrement handlers
const increment = (item: MenuItem, currentQty: number): number => {
  const step = item.allow_fractional ? item.quantity_step : 1;
  const newQty = currentQty + step;
  return Math.min(newQty, 50); // Max 50
};

const decrement = (item: MenuItem, currentQty: number): number => {
  const step = item.allow_fractional ? item.quantity_step : 1;
  const minQty = item.allow_fractional ? item.min_quantity : 1;
  const newQty = currentQty - step;
  return Math.max(newQty, minQty);
};
```

### 3. Display Formatting

```typescript
const formatQuantity = (item: MenuItem, qty: number): string => {
  if (item.allow_fractional) {
    // Show decimal for fractional items: "1.5 кг"
    return `${qty.toFixed(1)} ${item.unit}`;
  }
  // Integer for regular items: "2 шт"
  return `${qty} ${item.unit}`;
};

const formatPrice = (item: MenuItem, qty: number): string => {
  const total = item.price * qty;
  return `${Math.round(total)} RSD`;
};
```

### 4. Suggested UI Designs

**Option A: Smart +/- Buttons**
```
┌─────────────────────────────────────────┐
│ Оливье с говядиной (1 кг)               │
│ 2200 RSD/кг                             │
│                                         │
│    [ - ]    1.5 кг    [ + ]             │
│                                         │
│            = 3300 RSD                   │
└─────────────────────────────────────────┘
```

**Option B: Dropdown/Slider for Fractional**
```
┌─────────────────────────────────────────┐
│ Оливье с говядиной (1 кг)               │
│ 2200 RSD/кг                             │
│                                         │
│  Количество: [ 1.5 кг ▼ ]               │
│              ├─ 1 кг                    │
│              ├─ 1.5 кг                  │
│              ├─ 2 кг                    │
│              └─ 2.5 кг                  │
│                                         │
│            = 3300 RSD                   │
└─────────────────────────────────────────┘
```

---

## Validation

The backend validates:
1. Quantity >= `min_quantity`
2. Quantity follows `quantity_step` increments
3. Non-fractional items reject decimal quantities

### Error Responses

```json
// Below minimum
{"success": false, "error": "Minimum quantity for 'Оливье с говядиной (1 кг)' is 1"}

// Wrong step
{"success": false, "error": "Quantity for 'Оливье с говядиной (1 кг)' must be in increments of 0.5"}

// Fractional on non-fractional item
{"success": false, "error": "'Винегрет (120 г)' does not allow fractional quantities"}
```

---

## Cart Display

When showing cart items, include unit for fractional items:

```typescript
const cartItemDisplay = (item: CartItem, menuItem: MenuItem): string => {
  if (menuItem.allow_fractional) {
    return `${item.name} × ${item.quantity.toFixed(1)} ${menuItem.unit}`;
  }
  return `${item.name} × ${item.quantity}`;
};

// Examples:
// "Оливье с говядиной (1 кг) × 1.5 кг"
// "Винегрет (120 г) × 2"
```

---

## Testing Checklist

- [ ] Fractional items show correct +/- step (0.5)
- [ ] Cannot go below minimum (1 kg)
- [ ] Cannot enter invalid quantities (1.3, 0.7)
- [ ] Price calculates correctly (2200 × 1.5 = 3300)
- [ ] Cart displays quantity with unit
- [ ] Order submission works with decimal quantities
- [ ] Non-fractional items still work with integer quantities
- [ ] Validation errors display correctly

---

## TypeScript Interface Update

```typescript
interface MenuItem {
  id: number;
  name: string;
  category: string;
  description: string;
  price: number;
  image: string;
  // New fields
  allow_fractional: 0 | 1;
  quantity_step: number;
  min_quantity: number;
  unit: string;
}

interface OrderItem {
  item_id: number;
  quantity: number; // Can be float for fractional items
}
```
