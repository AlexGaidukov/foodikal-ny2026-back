-- Add delivery fee support
-- Migration: 008_add_delivery_fee.sql
-- Purpose: Add items_subtotal and delivery_fee columns to orders table

-- Add new columns
ALTER TABLE orders ADD COLUMN items_subtotal INTEGER DEFAULT 0;
ALTER TABLE orders ADD COLUMN delivery_fee INTEGER DEFAULT 0;

-- Backfill existing orders
-- For old orders: items_subtotal = total_price - discount (delivery was not tracked)
UPDATE orders
SET items_subtotal = total_price - COALESCE(discount_amount, 0),
    delivery_fee = 0
WHERE items_subtotal = 0;
