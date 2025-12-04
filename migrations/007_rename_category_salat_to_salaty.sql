-- Migration: Rename category from Салат to Салаты
-- Date: 2025-11-30
-- Description: Update category name from singular to plural

UPDATE menu_items
SET category = 'Салаты'
WHERE category = 'Салат';
