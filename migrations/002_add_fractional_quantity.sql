-- Migration: Add fractional quantity support to menu_items
-- Date: 2025-12-16

-- Add new columns for fractional quantity support
ALTER TABLE menu_items ADD COLUMN allow_fractional BOOLEAN DEFAULT 0;
ALTER TABLE menu_items ADD COLUMN quantity_step REAL DEFAULT 1.0;
ALTER TABLE menu_items ADD COLUMN min_quantity REAL DEFAULT 1.0;
ALTER TABLE menu_items ADD COLUMN unit TEXT DEFAULT 'шт';

-- Enable fractional quantities for specific salad items (IDs 38, 39, 41)
-- Step: 0.5, Min: 1, Unit: кг
UPDATE menu_items
SET allow_fractional = 1,
    quantity_step = 0.5,
    min_quantity = 1.0,
    unit = 'кг'
WHERE id IN (38, 39, 41);
