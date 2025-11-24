-- Migration: Remove customer_email column from orders table
-- SQLite does not support DROP COLUMN directly, so we need to recreate the table

-- Create new table without email
CREATE TABLE orders_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    customer_contact TEXT NOT NULL,
    delivery_address TEXT NOT NULL,
    delivery_date TEXT NOT NULL,
    comments TEXT,
    order_items TEXT NOT NULL,
    total_price INTEGER NOT NULL,
    confirmed_after_creation BOOLEAN DEFAULT 0,
    confirmed_before_delivery BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Copy data from old table (excluding customer_email)
INSERT INTO orders_new (
    id, customer_name, customer_contact, delivery_address, delivery_date,
    comments, order_items, total_price, confirmed_after_creation,
    confirmed_before_delivery, created_at, updated_at
)
SELECT
    id, customer_name, customer_contact, delivery_address, delivery_date,
    comments, order_items, total_price, confirmed_after_creation,
    confirmed_before_delivery, created_at, updated_at
FROM orders;

-- Drop old table
DROP TABLE orders;

-- Rename new table to orders
ALTER TABLE orders_new RENAME TO orders;
