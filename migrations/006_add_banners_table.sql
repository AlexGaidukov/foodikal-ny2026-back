-- Migration: Add banners table
-- Date: 2025-11-30
-- Description: Add table for homepage carousel banners

-- Create banners table
CREATE TABLE IF NOT EXISTS banners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    item_link TEXT NOT NULL,
    image_url TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_banners_display_order ON banners(display_order ASC);

-- Sample banners for testing
INSERT INTO banners (name, item_link, image_url, display_order) VALUES
('Свиная рулька запеченная', 'https://ny2026.foodikal.rs/menu/gorachee', 'https://ny2026.foodikal.rs/images/banners/pork-knuckle-banner.jpg', 1),
('Брускетта с вяленой свининой', 'https://ny2026.foodikal.rs/menu/brusketty', 'https://ny2026.foodikal.rs/images/banners/bruschetta-banner.jpg', 2);
