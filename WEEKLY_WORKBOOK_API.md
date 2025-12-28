# Weekly Workbook API Documentation

## Overview
The Weekly Workbook API generates comprehensive Excel reports for order data during the period December 25-31, 2025. The system uses a hybrid Python + JavaScript architecture for optimal performance.

## Architecture

### Components
1. **Python Backend** (`foodikal-ny-backend`):
   - Aggregates order data from D1 database
   - Processes and structures data
   - Provides JSON API endpoint

2. **JavaScript Excel Generator** (`foodikal-ny-excel-generator`):
   - Generates multi-sheet .xlsx files using ExcelJS
   - Handles complex formulas and formatting
   - Returns binary Excel file

3. **Service Binding**:
   - Python backend calls Excel generator via service binding
   - No external HTTP requests needed
   - Fast and secure communication

## API Endpoints

### 1. Get Weekly Workbook Data (JSON)
**Endpoint:** `GET /api/admin/weekly_workbook_data`
**Authentication:** Required (Bearer token)
**Purpose:** Returns aggregated order data as JSON

**Response:**
```json
{
  "success": true,
  "date_range": {
    "start": "2025-12-25",
    "end": "2025-12-31"
  },
  "customers": ["Company A", "Company B", ...],
  "menu_items": [
    {
      "id": 1,
      "name": "Брускетта с вяленой свининой",
      "category": "Брускетты",
      "price": 300,
      ...
    }
  ],
  "orders": [...],
  "aggregated_data": {
    "Company A": {
      "2025-12-25": {
        "1": 5,  // item_id: quantity
        "2": 3
      }
    }
  }
}
```

### 2. Generate Weekly Workbook (Excel File)
**Endpoint:** `GET /api/admin/generate_weekly_workbook`
**Authentication:** Required (Bearer token)
**Purpose:** Generates and downloads Excel workbook file

**Response:**
- **Content-Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Filename:** Dynamic based on range parameter:
  - `first_half` → `Заказы_нг_фуршет_25-28.xlsx`
  - `second_half` → `Заказы_нг_фуршет_29-31.xlsx`
  - `full_week` (or omitted) → `Заказы_фуршет_нг.xlsx`
- **Binary Excel file download**

**Example Usage:**
```javascript
// From admin frontend
const response = await fetch(
  'https://foodikal-ny-backend.x-gs-x.workers.dev/api/admin/generate_weekly_workbook',
  {
    headers: {
      'Authorization': `Bearer ${adminPassword}`
    }
  }
);

if (response.ok) {
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'Заказы_фуршет_нг.xlsx';
  a.click();
}
```

**cURL Example:**
```bash
curl -X GET \
  "https://foodikal-ny-backend.x-gs-x.workers.dev/api/admin/generate_weekly_workbook" \
  -H "Authorization: Bearer YOUR_PASSWORD" \
  -o "Заказы_фуршет_нг.xlsx"
```

## Query Parameters

Both endpoints support an optional `range` query parameter to filter orders by date:

**Parameter:** `range`
**Type:** String (optional)
**Values:**
- `first_half` - December 25-28, 2025 (Thursday-Sunday)
- `second_half` - December 29-31, 2025 (Monday-Wednesday)
- (omitted) - Full week, December 25-31, 2025 (default)

### Examples

**Get first half data (Dec 25-28):**
```bash
# JSON endpoint
curl -X GET \
  "https://foodikal-ny-backend.x-gs-x.workers.dev/api/admin/weekly_workbook_data?range=first_half" \
  -H "Authorization: Bearer YOUR_PASSWORD"

# Excel file (automatically named Заказы_нг_фуршет_25-28.xlsx)
curl -X GET \
  "https://foodikal-ny-backend.x-gs-x.workers.dev/api/admin/generate_weekly_workbook?range=first_half" \
  -H "Authorization: Bearer YOUR_PASSWORD" \
  -O
```

**Get second half data (Dec 29-31):**
```bash
# JSON endpoint
curl -X GET \
  "https://foodikal-ny-backend.x-gs-x.workers.dev/api/admin/weekly_workbook_data?range=second_half" \
  -H "Authorization: Bearer YOUR_PASSWORD"

# Excel file (automatically named Заказы_нг_фуршет_29-31.xlsx)
curl -X GET \
  "https://foodikal-ny-backend.x-gs-x.workers.dev/api/admin/generate_weekly_workbook?range=second_half" \
  -H "Authorization: Bearer YOUR_PASSWORD" \
  -O
```

**Get full week (same as no parameter):**
```bash
# Both of these return the full week
curl "https://foodikal-ny-backend.x-gs-x.workers.dev/api/admin/weekly_workbook_data" \
  -H "Authorization: Bearer YOUR_PASSWORD"

curl "https://foodikal-ny-backend.x-gs-x.workers.dev/api/admin/weekly_workbook_data?range=full_week" \
  -H "Authorization: Bearer YOUR_PASSWORD"
```

### Client Filtering

**Important:** The `range` parameter filters both dates AND customers:

- **Only customers with orders in the selected date range are included**
- If a customer has orders in both ranges, they appear separately in each range's output
- Excel files always show all 7 weekday columns; excluded dates display 0 or blank

**Example:**

John places two orders:
- Order 1: Dec 25 (Thursday) - 5 items
- Order 2: Dec 29 (Monday) - 3 items

**Result:**
- `?range=first_half`: John appears with only Dec 25-28 orders (5 items on Thu, 0 on Mon-Wed)
- `?range=second_half`: John appears with only Dec 29-31 orders (0 on Thu-Sun, 3 items on Mon)
- No parameter: John appears with all orders (5 items on Thu, 3 items on Mon)

### Response Changes

The `date_range` object now includes a `preset` field:

```json
{
  "success": true,
  "date_range": {
    "start": "2025-12-25",
    "end": "2025-12-28",
    "preset": "first_half"
  },
  "customers": ["Company A", "Company B"],
  "aggregated_data": { ... }
}
```

### Error Handling

**Invalid range values return 400 Bad Request:**

```bash
curl "https://foodikal-ny-backend.x-gs-x.workers.dev/api/admin/weekly_workbook_data?range=invalid" \
  -H "Authorization: Bearer YOUR_PASSWORD"
```

**Response:**
```json
{
  "success": false,
  "error": "Invalid range parameter: 'invalid'. Valid values: full_week, first_half, second_half"
}
```

## Excel Workbook Structure

The generated workbook contains 14 sheets:

### Sheet 1: "ЗАКАЗ" (Main Order Sheet)
- **Size:** ~205 rows × (3 + customers × 15) columns
- **Structure:**
  - Column A: Menu item names (multi-language format)
  - Column B: Row numbers
  - Columns C+: Customer data (15 columns per customer)
    - 7 columns for days (Thu-Wed)
    - 7 columns for customizations
    - 1 column for total

### Sheets 2-7: Daily Sheets
- **Names:** "ЗН ЧТ", "ЗН ПТ", "ЗН СБ", "ЗН ВС", "ЗН ПН", "ЗН ВТ", "ЗН СР"
- **Mapping:**
  - ЗН ЧТ = Thursday, Dec 25
  - ЗН ПТ = Friday, Dec 26
  - ЗН СБ = Saturday, Dec 27
  - ЗН ВС = Sunday, Dec 28
  - ЗН ПН = Monday, Dec 29
  - ЗН ВТ = Tuesday, Dec 30
  - ЗН СР = Wednesday, Dec 31

- **Structure:**
  - Row 1: Header with date ("Готовим DD.MM")
  - Row 2: Column headers
  - Column A: Menu item names
  - Column B: Total quantities (SUM formula)
  - Column C: Customization column (empty)
  - Even columns (D,F,H...): Customer quantities
  - Odd columns (E,G,I...): Customization placeholders

### Sheet 8: "ЗН НЕДЕЛЬНЫЙ" (Weekly Summary)
- Consolidates all daily totals
- Formulas reference daily sheets
- Shows totals for each day and week

### Sheet 9: "АКТЫ" (Order Confirmations)
- Document header in 3 languages (Russian/English/Serbian)
- List of all customers
- Total quantities per customer

### Sheets 10-14: "ЛС ПН" through "ЛС ПТ" (Packing Lists)
- Simplified packing list templates
- Customer names listed

## Data Aggregation

### Database Query
Orders are fetched for the date range December 25-31, 2025:

```sql
SELECT * FROM orders
WHERE delivery_date BETWEEN '2025-12-25' AND '2025-12-31'
ORDER BY delivery_date, customer_name
```

### Aggregation Logic
For each order:
1. Parse `order_items` JSON field
2. Group by customer → date → menu item
3. Sum quantities for duplicate items

Example:
```
Customer A orders:
- Order 1 (Dec 25): Item #9 × 2
- Order 2 (Dec 25): Item #9 × 3

Aggregated: Customer A, Dec 25, Item #9 = 5
```

## Formulas in Excel

### Daily Sheets
- **Column B (Total):** `=SUM(D[row]:BK[row])`
  - Sums all customer quantities for that item

### Main ЗАКАЗ Sheet
- **Day columns:** `='ЗН ПН'!D3`
  - References daily sheet cell
- **Total column:** `=SUM(C[row]:P[row])`
  - Sums 7 day columns + 7 custom columns

### Weekly Summary
- **Day columns:** `='ЗН ПН'!B3`
  - References daily total column
- **Week total:** `=SUM(B[row]:H[row])`

## Error Handling

### No Orders Found
- Generates empty template with structure
- All quantity fields show 0 or empty

### Database Errors
- Returns 500 with error message
- Logs error event for debugging

### Excel Generator Errors
- Returns 500 if service binding fails
- Returns error message from Excel worker

## Performance

- **Database query:** ~100-500ms (depends on order count)
- **Data aggregation:** ~50-200ms (Python processing)
- **Excel generation:** ~1-3 seconds (JavaScript ExcelJS)
- **Total time:** ~2-4 seconds for complete workbook

## Deployment

### Python Backend
```bash
wrangler deploy
```

### Excel Generator
```bash
wrangler deploy -c wrangler-excel.toml
```

### Service Binding
Configured in `wrangler.toml`:
```toml
[[services]]
binding = "EXCEL_GENERATOR"
service = "foodikal-ny-excel-generator"
```

## URLs

- **Python Backend:** `https://foodikal-ny-backend.x-gs-x.workers.dev`
- **Excel Generator:** `https://foodikal-ny-excel-generator.x-gs-x.workers.dev`
- **CORS Wrapper:** `https://foodikal-ny-cors-wrapper.x-gs-x.workers.dev`

## Security

- **Authentication:** Admin password required (Bearer token)
- **Rate Limiting:** Admin endpoints protected by auth rate limiting
- **Service Binding:** Internal communication (no public Excel generator access)

## Limitations

- **Preset Date Ranges:** Only supports three presets (full week, first half, second half) for December 25-31, 2025
- **No Custom Dates:** Cannot specify arbitrary date ranges
- **No Pagination:** All data loaded at once
- **Memory:** Large customer counts may approach worker memory limits
- **File Size:** Workbooks with 50+ customers may be 5-10 MB

## Future Enhancements

Possible improvements:
1. Custom date ranges (arbitrary start/end dates)
2. Customer filtering options  (include/exclude specific customers)
3. Additional sheet types
4. Custom formatting options
5. Email delivery of workbooks

## Troubleshooting

### Excel file won't download
- Check authentication token
- Verify date range has orders
- Check browser console for errors

### Empty Excel file
- No orders in date range
- Database query returned empty results

### Service binding error
- Ensure Excel generator worker is deployed
- Check wrangler.toml service binding configuration
- Redeploy Python backend

## Support

For issues or questions:
- Check worker logs: `wrangler tail`
- View deployments: `wrangler deployments list`
- GitHub issues: [Your repository URL]
