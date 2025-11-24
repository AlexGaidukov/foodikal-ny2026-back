-- Migration: Replace all menu data with actual Foodikal NY menu
-- WARNING: This will delete ALL existing orders and menu items

-- Clear existing data
DELETE FROM orders;
DELETE FROM menu_items;

-- Insert Брускетты (11 items)
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Брускетта с вяленой свининой', 'Брускетты', 'Хрустящий хлеб с вяленой свининой (60г)', 300, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Брускетта с гравлаксом', 'Брускетты', 'Слабосоленый лосось на поджаренном хлебе (60г)', 220, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Брускетта с грибной икрой', 'Брускетты', 'Ароматная грибная икра на хрустящей основе (60г)', 120, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Брускетта с грушей и горгонзоллой', 'Брускетты', 'Сочетание сладкой груши и пикантного сыра горгонзолла (60г)', 350, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Брускетта с гуакамоле', 'Брускетты', 'Нежное пюре из авокадо с приправами (60г)', 200, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Брускетта с паштетом из куриной печени', 'Брускетты', 'Домашний паштет из куриной печени (60г)', 90, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Брускетта с пршутом и персиком', 'Брускетты', 'Итальянская ветчина пршут со сладким персиком (60г)', 270, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Брускетта с рикоттой', 'Брускетты', 'Нежный сыр рикотта на хрустящем хлебе (60г)', 90, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Брускетта с творожным сыром и сладким перцем', 'Брускетты', 'Мягкий творожный сыр с кусочками сладкого перца (60г)', 120, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Брускетта с хумусом и свежими овощами', 'Брускетты', 'Паста из нута с ассорти свежих овощей (60г)', 100, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Брускетта с шампиньонами', 'Брускетты', 'Обжаренные шампиньоны с зеленью (60г)', 140, '');

-- Insert Горячее (7 items)
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Баранья нога', 'Горячее', 'Запеченная баранья нога с пряными травами (1780г)', 15500, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Куриный шашлычок с картофелем фри', 'Горячее', 'Нежные кусочки курицы на шпажках с золотистым картофелем фри (200г)', 550, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Овощи гриль', 'Горячее', 'Ассорти овощей, приготовленных на гриле (550г)', 650, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Рулетики из ветчины с сыром', 'Горячее', 'Ветчина, завернутая с плавленым сыром (2шт, 120г)', 450, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Свиная рулька', 'Горячее', 'Запеченная свиная рулька с хрустящей корочкой (1100г)', 3100, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Свиной шашлычок', 'Горячее', 'Маринованная свинина на шпажках (100г)', 310, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Тушеная капуста', 'Горячее', 'Классическая тушеная капуста (650-700г)', 870, '');

-- Insert Другие закуски (2 items)
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Ассорти сыров и мясных деликатесов', 'Другие закуски', 'Подборка элитных сыров и мясных деликатесов (300г)', 2000, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Хумус с баклажаном', 'Другие закуски', 'Закуска из нута с печеным баклажаном (1шт 50г)', 120, '');

-- Insert Канапе (8 items)
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Канапе овощное', 'Канапе', 'Ассорти свежих овощей на шпажке (45г)', 75, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Канапе с ветчиной', 'Канапе', 'Мини-бутерброд с ветчиной (40г)', 90, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Канапе с грушей и пршутом', 'Канапе', 'Сочетание сладкой груши и итальянской ветчины (25г)', 140, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Канапе с креветкой и авокадо', 'Канапе', 'Нежная креветка с кремовым авокадо (25г)', 240, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Канапе с салями и вяленым томатом', 'Канапе', 'Пикантная салями с вялеными томатами (55г)', 180, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Канапе с салями и черным хлебом', 'Канапе', 'Салями на ароматном черном хлебе (20г)', 90, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Канапе с сыром и виноградом', 'Канапе', 'Сыр с сочным виноградом (30г)', 130, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Канапе фруктовое', 'Канапе', 'Ассорти свежих фруктов (60г)', 115, '');

-- Insert Салат (6 items)
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Винегрет', 'Салат', 'Классический салат из отварных овощей (мини-порция, 120г)', 175, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Крабовый салат', 'Салат', 'Салат с крабовыми палочками без огурца (1кг)', 1800, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Селёдка под Шубой', 'Салат', 'Традиционный слоеный салат с сельдью (1кг)', 2100, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Крабовый салат', 'Салат', 'Салат с крабовыми палочками (мини-порция, 120г)', 450, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Оливье с говядиной', 'Салат', 'Классический оливье с нежной говядиной (1кг)', 2200, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Оливье с говядиной', 'Салат', 'Классический оливье с говядиной (мини-порция, 120г)', 250, '');

-- Insert Тарталетки (5 items)
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Тарталетка с икрой', 'Тарталетки', 'Хрустящая корзиночка с имитацией икры (35г)', 150, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Тарталетка с крабовым салатом', 'Тарталетки', 'Корзиночка с нежным крабовым салатом (30г)', 150, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Тарталетка с креветкой', 'Тарталетки', 'Тарталетка с морской креветкой (30г)', 180, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Тарталетка со свекольным муссом и сельдью', 'Тарталетки', 'Оригинальное сочетание свекольного мусса с селедкой (35г)', 170, '');
INSERT INTO menu_items (name, category, description, price, image) VALUES ('Тарталетка со слабосоленым лососем', 'Тарталетки', 'Корзиночка с нежным слабосоленым лососем (35г)', 160, '');
