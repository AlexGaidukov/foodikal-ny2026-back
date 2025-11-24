-- Migration: Add promo codes feature
-- 1. Create promo_codes table
-- 2. Add promo_code, original_price, discount_amount columns to orders table

-- Create promo_codes table
CREATE TABLE IF NOT EXISTS promo_codes (
    code TEXT PRIMARY KEY,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create new orders table with promo code columns
CREATE TABLE orders_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    customer_contact TEXT NOT NULL,
    delivery_address TEXT NOT NULL,
    delivery_date TEXT NOT NULL,
    comments TEXT,
    order_items TEXT NOT NULL,
    total_price INTEGER NOT NULL,
    promo_code TEXT,
    original_price INTEGER,
    discount_amount INTEGER DEFAULT 0,
    confirmed_after_creation BOOLEAN DEFAULT 0,
    confirmed_before_delivery BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Copy data from old table
INSERT INTO orders_new (
    id, customer_name, customer_contact, delivery_address, delivery_date,
    comments, order_items, total_price,
    confirmed_after_creation, confirmed_before_delivery,
    created_at, updated_at
)
SELECT
    id, customer_name, customer_contact, delivery_address, delivery_date,
    comments, order_items, total_price,
    confirmed_after_creation, confirmed_before_delivery,
    created_at, updated_at
FROM orders;

-- Drop old table
DROP TABLE orders;

-- Rename new table to orders
ALTER TABLE orders_new RENAME TO orders;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_confirmations ON orders(confirmed_after_creation, confirmed_before_delivery);
