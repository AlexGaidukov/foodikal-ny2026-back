-- Migration: Rename category from "Другие закуски" to "Закуски"

UPDATE menu_items SET category = 'Закуски' WHERE category = 'Другие закуски';
