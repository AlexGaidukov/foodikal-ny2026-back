-- Foodikal NY Database Schema
-- Database: foodikal_ny_db (D1 SQLite)

-- Table 1: Menu Items
CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    price INTEGER NOT NULL,
    image TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: Orders
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    customer_contact TEXT NOT NULL,
    delivery_address TEXT NOT NULL,
    delivery_date TEXT NOT NULL,
    comments TEXT,
    order_items TEXT NOT NULL,
    items_subtotal INTEGER DEFAULT 0,
    delivery_fee INTEGER DEFAULT 0,
    total_price INTEGER NOT NULL,
    promo_code TEXT,
    original_price INTEGER,
    discount_amount INTEGER DEFAULT 0,
    confirmed_after_creation BOOLEAN DEFAULT 0,
    confirmed_before_delivery BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table 3: Promo Codes
CREATE TABLE IF NOT EXISTS promo_codes (
    code TEXT PRIMARY KEY,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table 4: Banners
CREATE TABLE IF NOT EXISTS banners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    item_link TEXT NOT NULL,
    image_url TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_menu_category ON menu_items(category);
CREATE INDEX IF NOT EXISTS idx_orders_confirmations ON orders(confirmed_after_creation, confirmed_before_delivery);
CREATE INDEX IF NOT EXISTS idx_banners_display_order ON banners(display_order ASC);

-- Sample menu items (for testing)
INSERT INTO menu_items (name, category, description, price, image) VALUES
('Брускетта с вяленой свининой (60г)', 'Брускетты', 'Хлеб, вяленая свинина, оливковое масло, специи', 300, 'images/bruschetta-pork.jpg'),
('Брускетта с томатами (60г)', 'Брускетты', 'Хлеб, свежие томаты, базилик, чеснок, оливковое масло', 280, 'images/bruschetta-tomato.jpg'),
('Свиная рулька запеченная (1200г)', 'Горячее', 'Свиная рулька, запеченная с травами и специями', 3100, 'images/pork-knuckle.jpg'),
('Баранья нога запеченная (1780г)', 'Горячее', 'Баранья нога с розмарином и чесноком', 15500, 'images/lamb-leg.jpg'),
('Тартар из лосося (120г)', 'Закуски', 'Свежий лосось, авокадо, лимон, каперсы', 1200, 'images/salmon-tartar.jpg'),
('Канапе с икрой (5 шт)', 'Канапе', 'Хлеб, сливочное масло, красная икра', 450, 'images/canape-caviar.jpg'),
('Салат Цезарь (250г)', 'Салат', 'Листья салата, курица, пармезан, сухарики, соус цезарь', 950, 'images/caesar.jpg'),
('Тарталетка с креветками (1 шт)', 'Тарталетки', 'Тарталетка, креветки, соус тартар', 380, 'images/tartlet-shrimp.jpg');
