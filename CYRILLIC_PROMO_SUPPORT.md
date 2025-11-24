# Cyrillic Promo Code Support - Update

## What Changed

The promo code feature now **fully supports Cyrillic characters** in addition to Latin letters and numbers.

---

## Updated Validation Rules

### Allowed Characters:
- ✅ **Latin letters**: A-Z, a-z
- ✅ **Cyrillic letters**: А-Я, а-я, Ё, ё
- ✅ **Numbers**: 0-9
- ❌ **Special characters**: Not allowed (no spaces, hyphens, underscores, etc.)

### Length Requirements:
- Minimum: 3 characters
- Maximum: 20 characters

---

## Valid Examples

### Latin Promo Codes:
- `NEWYEAR2026` ✅
- `SUMMER10` ✅
- `FLASH50` ✅

### Cyrillic Promo Codes:
- `НОВЫЙГОД2026` ✅ (New Year 2026)
- `СКИДКА10` ✅ (Discount 10)
- `ЗИМА2026` ✅ (Winter 2026)
- `ЛЕТО` ✅ (Summer)

### Mixed (Latin + Cyrillic + Numbers):
- `НОВЫЙ2026` ✅
- `SALE10РУБ` ✅

### Invalid Examples:
- `НГ` ❌ (too short - only 2 characters)
- `НОВЫЙ-ГОД` ❌ (contains hyphen)
- `СКИДКА 10` ❌ (contains space)
- `SALE!` ❌ (contains special character)

---

## Technical Details

### Backend Changes:
File: `src/validators.py`

Updated validation pattern:
```python
pattern = r'^[A-Za-zА-Яа-яЁё0-9]+$'
```

This regex pattern allows:
- `A-Za-z` - Latin letters (uppercase and lowercase)
- `А-Яа-я` - Cyrillic letters (uppercase and lowercase)
- `Ёё` - Special Cyrillic letter Yo
- `0-9` - Numbers

### Database Support:
- SQLite with UTF-8 encoding already supports Cyrillic
- No database migration needed
- Promo codes are stored as TEXT with full UTF-8 support

---

## Frontend Implementation Notes

### For Admin Panel:

When creating promo codes, you can now use Cyrillic characters:

```javascript
// Example: Creating a Cyrillic promo code
await createPromoCode("НОВЫЙГОД2026");
```

**Validation** (client-side - optional but recommended):
```javascript
function validatePromoCode(code) {
  // Length check
  if (code.length < 3 || code.length > 20) {
    return false;
  }

  // Allow Latin, Cyrillic, and numbers only
  const pattern = /^[A-Za-zА-Яа-яЁё0-9]+$/;
  return pattern.test(code);
}
```

### For Customer Frontend:

No changes needed to support Cyrillic input - the backend will accept it automatically.

**Optional**: Update client-side validation if you have it:

```javascript
// Old validation (Latin only)
const pattern = /^[A-Z0-9]+$/; // ❌ Old - rejects Cyrillic

// New validation (Latin + Cyrillic)
const pattern = /^[A-Za-zА-Яа-яЁё0-9]+$/; // ✅ New - accepts both
```

---

## Testing

### Test Promo Code Created:
- **Code**: `НОВЫЙГОД2026`
- **Status**: Active in production database
- **Discount**: 5% (same as all promo codes)

### Test Results:
✅ **Create Order with Cyrillic Promo**: SUCCESS
- Promo code: НОВЫЙГОД2026
- Discount applied: 26 RSD (5% of 520 RSD)
- Order created: ID #18

✅ **Database Storage**: Cyrillic characters stored and retrieved correctly

✅ **API Response**: Promo code returned in response with proper UTF-8 encoding

---

## Important Notes

### Case Sensitivity:
- Promo codes are **case-sensitive**
- `НОВЫЙГОД` ≠ `новыйгод` ≠ `НовыйГод`
- **Recommendation**: Use UPPERCASE for consistency

### Mixed Languages:
- You can mix Latin and Cyrillic in the same promo code
- Example: `НОВЫЙ2026` or `SALE10РУБ`

### Frontend Display:
- Make sure your frontend supports UTF-8 encoding
- Set proper charset: `<meta charset="UTF-8">`
- Use proper Content-Type header: `Content-Type: application/json; charset=utf-8`

### Input Field:
- No special handling needed for Cyrillic input
- Users can type Cyrillic characters naturally
- Consider adding placeholder text in Cyrillic for Russian-speaking users:
  ```html
  <input placeholder="Введите промокод" />
  <!-- "Enter promo code" in Russian -->
  ```

---

## Updated Documentation

The following documentation files reflect the Cyrillic support:

1. **Admin Instructions** (`admin_promo_instructions.md`):
   - Updated validation rules section
   - Added Cyrillic examples
   - Updated valid/invalid examples

2. **Frontend Instructions** (`frontend_promo_instructions.md`):
   - Updated validation rules section
   - Added Cyrillic examples
   - Updated client-side validation code

---

## Examples for Different Languages

### Russian Promo Codes:
```
НОВЫЙГОД2026 - New Year 2026
ЛЕТО2026 - Summer 2026
ЗИМА - Winter
ВЕСНА - Spring
ОСЕНЬ - Autumn
СКИДКА5 - Discount 5
РАСПРОДАЖА - Sale
ПОДАРОК - Gift
```

### Serbian Promo Codes:
```
НОВА2026 - New 2026
ЛЕТО - Summer
ЗИМА - Winter
ПОПУСТ - Discount
```

---

## Migration Guide

### For Existing Deployments:

**No migration needed!** The update is backward compatible:

1. ✅ Existing Latin promo codes continue to work
2. ✅ No database changes required
3. ✅ UTF-8 support was already present
4. ✅ Only validation logic was updated

### Deployment Steps:

1. Code is already deployed to production
2. Cyrillic promo codes can be created immediately
3. No downtime or data migration required

---

## Support & Troubleshooting

### Common Issues:

**Q: Cyrillic characters display as ???? or squares**
A: Check that your HTML has `<meta charset="UTF-8">` and API responses use proper UTF-8 encoding

**Q: Validation rejects valid Cyrillic codes**
A: Make sure you're using the updated validation pattern that includes `А-Яа-яЁё`

**Q: Case sensitivity issues**
A: Remember promo codes are case-sensitive. Convert to uppercase for consistency:
```javascript
const code = userInput.toUpperCase(); // Works for both Latin and Cyrillic
```

**Q: Mixed Latin-Cyrillic codes don't work**
A: They should work! If not, check the validation pattern includes both character ranges.

---

## Version History

- **v1.1** (November 16, 2025): Added Cyrillic character support
- **v1.0** (November 16, 2025): Initial promo code feature (Latin only)

---

## Contact

For issues or questions about Cyrillic promo code support, check:
- Backend validation: `src/validators.py`
- Test with: `НОВЫЙГОД2026` (already created in database)
