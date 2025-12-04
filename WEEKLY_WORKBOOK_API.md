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
- **Filename:** `Заказы_фуршет_нг.xlsx`
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

- **Fixed Date Range:** December 25-31, 2025 (hardcoded)
- **No Pagination:** All data loaded at once
- **Memory:** Large customer counts may approach worker memory limits
- **File Size:** Workbooks with 50+ customers may be 5-10 MB

## Future Enhancements

Possible improvements:
1. Configurable date ranges
2. Customer filtering options
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
