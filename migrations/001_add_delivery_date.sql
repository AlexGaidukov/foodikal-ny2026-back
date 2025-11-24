-- Migration: Add delivery_date column to orders table
-- Date: 2025-11-13

-- Add delivery_date column
ALTER TABLE orders ADD COLUMN delivery_date TEXT NOT NULL DEFAULT '2025-12-31';

-- Remove default after adding (to make it required for new orders)
-- Note: SQLite doesn't support removing DEFAULT, so we leave it for now
-- New orders will be validated by the application layer
