# Admin Panel: Fractional Quantity Configuration

## Overview

Admins can configure which menu items support fractional quantities (e.g., salads sold by kg). This allows customers to order items like "1.5 kg" instead of whole units only.

---

## API Endpoints

### Get Menu Items

`GET /api/admin/menu_list` or `GET /api/menu`

Response includes fractional fields:

```json
{
  "id": 41,
  "name": "Оливье с говядиной (1 кг)",
  "price": 2200,
  "allow_fractional": 1,
  "quantity_step": 0.5,
  "min_quantity": 1,
  "unit": "кг"
}
```

### Update Menu Item

`PUT /api/admin/menu_update/:id`

```bash
curl -X PUT https://api.example.com/api/admin/menu_update/41 \
  -H "Authorization: Bearer YOUR_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{
    "allow_fractional": true,
    "quantity_step": 0.5,
    "min_quantity": 1,
    "unit": "кг"
  }'
```

### Create Menu Item

`POST /api/admin/menu_add`

```bash
curl -X POST https://api.example.com/api/admin/menu_add \
  -H "Authorization: Bearer YOUR_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Новый салат (1 кг)",
    "category": "Салаты",
    "price": 1800,
    "description": "Описание",
    "allow_fractional": true,
    "quantity_step": 0.5,
    "min_quantity": 1,
    "unit": "кг"
  }'
```

---

## Field Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `allow_fractional` | `boolean` | `false` | Enable decimal quantities |
| `quantity_step` | `number` | `1.0` | Increment size (0.5, 0.25, 1.0) |
| `min_quantity` | `number` | `1.0` | Minimum order quantity |
| `unit` | `string` | `"шт"` | Display unit (кг, г, шт, порция) |

---

## UI Implementation

### Menu Item Edit Form

Add a "Fractional Quantity" section to the menu item edit form:

```
┌─────────────────────────────────────────────────────────┐
│ Edit Menu Item                                          │
├─────────────────────────────────────────────────────────┤
│ Name:        [Оливье с говядиной (1 кг)              ]  │
│ Category:    [Салаты                              ▼  ]  │
│ Price:       [2200                                   ]  │
│ Description: [________________________              ]   │
│ Image URL:   [________________________              ]   │
│                                                         │
│ ─── Quantity Settings ─────────────────────────────     │
│                                                         │
│ [✓] Allow fractional quantities                         │
│                                                         │
│ Step size:       [0.5    ]  (e.g., 0.5, 0.25, 1)       │
│ Minimum:         [1      ]  (cannot order less)        │
│ Unit:            [кг   ▼ ]  (кг, г, шт, порция)        │
│                                                         │
│              [Cancel]  [Save]                           │
└─────────────────────────────────────────────────────────┘
```

### Conditional Display

Only show step/min/unit fields when "Allow fractional" is checked:

```typescript
const [allowFractional, setAllowFractional] = useState(false);

return (
  <div>
    <label>
      <input
        type="checkbox"
        checked={allowFractional}
        onChange={(e) => setAllowFractional(e.target.checked)}
      />
      Allow fractional quantities
    </label>

    {allowFractional && (
      <div className="fractional-settings">
        <label>
          Step size:
          <input type="number" step="0.1" min="0.1" value={quantityStep} />
        </label>
        <label>
          Minimum:
          <input type="number" step="0.1" min="0.1" value={minQuantity} />
        </label>
        <label>
          Unit:
          <select value={unit}>
            <option value="кг">кг</option>
            <option value="г">г</option>
            <option value="шт">шт</option>
            <option value="порция">порция</option>
          </select>
        </label>
      </div>
    )}
  </div>
);
```

### Menu List Table

Add a column or indicator for fractional items:

```
┌────┬─────────────────────────────┬──────────┬───────┬──────────┐
│ ID │ Name                        │ Category │ Price │ Quantity │
├────┼─────────────────────────────┼──────────┼───────┼──────────┤
│ 37 │ Винегрет (120 г)           │ Салаты   │ 400   │ шт       │
│ 38 │ Крабовый салат (1 кг)      │ Салаты   │ 2000  │ 0.5 кг   │  ← fractional
│ 41 │ Оливье с говядиной (1 кг)  │ Салаты   │ 2200  │ 0.5 кг   │  ← fractional
│ 42 │ Оливье с говядиной (120 г) │ Салаты   │ 400   │ шт       │
└────┴─────────────────────────────┴──────────┴───────┴──────────┘
```

---

## Common Configurations

### By Weight (kg)
For items sold by kilogram:
```json
{
  "allow_fractional": true,
  "quantity_step": 0.5,
  "min_quantity": 1,
  "unit": "кг"
}
```
Valid: 1, 1.5, 2, 2.5, 3...

### By Weight (smaller step)
For items needing finer control:
```json
{
  "allow_fractional": true,
  "quantity_step": 0.25,
  "min_quantity": 0.5,
  "unit": "кг"
}
```
Valid: 0.5, 0.75, 1, 1.25, 1.5...

### Standard (pieces)
Default for most items:
```json
{
  "allow_fractional": false,
  "quantity_step": 1,
  "min_quantity": 1,
  "unit": "шт"
}
```
Valid: 1, 2, 3, 4...

---

## Validation Rules

The backend enforces:

1. **Step validation**: Quantity must follow step increments from min_quantity
   - If step=0.5, min=1: valid values are 1, 1.5, 2, 2.5...
   - 1.3 or 1.7 would be rejected

2. **Minimum validation**: Cannot order less than min_quantity

3. **Non-fractional protection**: Items with `allow_fractional=false` reject decimal quantities

---

## Currently Configured Items

| ID | Name | Step | Min | Unit |
|----|------|------|-----|------|
| 38 | Крабовый салат (1 кг) | 0.5 | 1 | кг |
| 39 | Селёдка под Шубой (1 кг) | 0.5 | 1 | кг |
| 41 | Оливье с говядиной (1 кг) | 0.5 | 1 | кг |

All other items: `allow_fractional=0`, `quantity_step=1`, `min_quantity=1`, `unit="шт"`

---

## Quick Enable via API

To enable fractional quantities for an existing item:

```bash
# Enable fractional for item ID 50
curl -X PUT https://api.example.com/api/admin/menu_update/50 \
  -H "Authorization: Bearer PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{"allow_fractional": true, "quantity_step": 0.5, "min_quantity": 1, "unit": "кг"}'
```

To disable fractional:

```bash
curl -X PUT https://api.example.com/api/admin/menu_update/50 \
  -H "Authorization: Bearer PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{"allow_fractional": false, "unit": "шт"}'
```

---

## TypeScript Interface

```typescript
interface MenuItem {
  id: number;
  name: string;
  category: string;
  description: string;
  price: number;
  image: string;
  allow_fractional: boolean;
  quantity_step: number;
  min_quantity: number;
  unit: string;
}

interface MenuItemUpdate {
  name?: string;
  category?: string;
  description?: string;
  price?: number;
  image?: string;
  allow_fractional?: boolean;
  quantity_step?: number;
  min_quantity?: number;
  unit?: string;
}
```

---

## Testing Checklist

- [ ] Can enable fractional for an item via edit form
- [ ] Can disable fractional for an item
- [ ] Step size field validates (positive number)
- [ ] Minimum field validates (positive number)
- [ ] Unit dropdown works correctly
- [ ] Changes persist after save
- [ ] Menu list shows fractional indicator
- [ ] Can create new item with fractional enabled
