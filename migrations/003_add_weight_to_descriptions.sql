-- Migration: Add weight information to menu item descriptions
-- This migration prepends weight to existing descriptions

-- Брускетты (11 items) - 60г each
UPDATE menu_items SET description = '60г | ' || description WHERE name = 'Брускетта с вяленой свининой (шт)';
UPDATE menu_items SET description = '60г | ' || description WHERE name = 'Брускетта с гравлаксом (шт)';
UPDATE menu_items SET description = '60г | ' || description WHERE name = 'Брускетта с грибной икрой (шт)';
UPDATE menu_items SET description = '60г | ' || description WHERE name = 'Брускетта с грушей и горгонзоллой (шт)';
UPDATE menu_items SET description = '60г | ' || description WHERE name = 'Брускетта с гуакамоле (шт)';
UPDATE menu_items SET description = '60г | ' || description WHERE name = 'Брускетта с паштетом из куриной печени (шт)';
UPDATE menu_items SET description = '60г | ' || description WHERE name = 'Брускетта с пршутом и персиком (шт)';
UPDATE menu_items SET description = '60г | ' || description WHERE name = 'Брускетта с рикоттой (шт)';
UPDATE menu_items SET description = '60г | ' || description WHERE name = 'Брускетта с творожным сыром и сладким перцем (шт)';
UPDATE menu_items SET description = '60г | ' || description WHERE name = 'Брускетта с хумусом и свежими овощами (шт)';
UPDATE menu_items SET description = '60г | ' || description WHERE name = 'Брускетта с шампиньонами (шт)';

-- Горячее (6 items, skipping Баранья нога as it's already done)
UPDATE menu_items SET description = '200г | ' || description WHERE name = 'Куриный шашлычок с картофелем фри';
UPDATE menu_items SET description = '550г | ' || description WHERE name = 'Овощи гриль';
UPDATE menu_items SET description = '120г | ' || description WHERE name = 'Рулетики из ветчины с сыром (2 шт)';
UPDATE menu_items SET description = '1100г | ' || description WHERE name = 'Свиная рулька';
UPDATE menu_items SET description = '100г | ' || description WHERE name = 'Свиной шашлычок';
UPDATE menu_items SET description = '650г | ' || description WHERE name = 'Тушеная капуста';

-- Другие закуски (2 items)
UPDATE menu_items SET description = '300г | ' || description WHERE name = 'Ассорти сыров и мясных деликатесов';
UPDATE menu_items SET description = '50г | ' || description WHERE name = 'Хумус с баклажаном';

-- Канапе (8 items)
UPDATE menu_items SET description = '45г | ' || description WHERE name = 'Канапе овощное (шт)';
UPDATE menu_items SET description = '40г | ' || description WHERE name = 'Канапе с ветчиной (шт)';
UPDATE menu_items SET description = '25г | ' || description WHERE name = 'Канапе с грушей и пршутом (шт)';
UPDATE menu_items SET description = '25г | ' || description WHERE name = 'Канапе с креветкой и авокадо (шт)';
UPDATE menu_items SET description = '55г | ' || description WHERE name = 'Канапе с салями и вяленым томатом (шт)';
UPDATE menu_items SET description = '20г | ' || description WHERE name = 'Канапе с салями и черным хлебом (шт)';
UPDATE menu_items SET description = '30г | ' || description WHERE name = 'Канапе с сыром и виноградом (шт)';
UPDATE menu_items SET description = '60г | ' || description WHERE name = 'Канапе фруктовое (шт)';

-- Салат (3 items - 120g versions only, skipping 1kg versions)
UPDATE menu_items SET description = '120г | ' || description WHERE name = 'Винегрет (120 г)';
UPDATE menu_items SET description = '120г | ' || description WHERE name = 'Крабовый салат (120 г)';
UPDATE menu_items SET description = '120г | ' || description WHERE name = 'Оливье с говядиной (120 г)';

-- Тарталетки (5 items)
UPDATE menu_items SET description = '35г | ' || description WHERE name = 'Тарталетка с икрой (шт)';
UPDATE menu_items SET description = '30г | ' || description WHERE name = 'Тарталетка с крабовым салатом (шт)';
UPDATE menu_items SET description = '30г | ' || description WHERE name = 'Тарталетка с креветкой (шт)';
UPDATE menu_items SET description = '35г | ' || description WHERE name = 'Тарталетка со свекольным муссом и сельдью (шт)';
UPDATE menu_items SET description = '35г | ' || description WHERE name = 'Тарталетка со слабосоленым лососем (шт)';
