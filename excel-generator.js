/**
 * Excel Generator Worker for Foodikal NY
 * Generates weekly order workbook from aggregated data
 * Uses ExcelJS library to create multi-sheet .xlsx files
 */

import ExcelJS from 'exceljs';

export default {
	async fetch(request, env, ctx) {
		if (request.method === 'OPTIONS') {
			return new Response(null, {
				headers: {
					'Access-Control-Allow-Origin': '*',
					'Access-Control-Allow-Methods': 'POST, OPTIONS',
					'Access-Control-Allow-Headers': 'Content-Type, Authorization',
				},
			});
		}

		if (request.method !== 'POST') {
			return new Response('Method not allowed', { status: 405 });
		}

		try {
			// Parse incoming data
			const data = await request.json();

			// Generate Excel workbook
			const workbook = await generateWeeklyWorkbook(data);

			// Write to buffer
			const buffer = await workbook.xlsx.writeBuffer();

			// Return Excel file
			return new Response(buffer, {
				headers: {
					'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
					'Content-Disposition': 'attachment; filename="Заказы_фуршет_нг.xlsx"',
					'Access-Control-Allow-Origin': '*',
				},
			});
		} catch (error) {
			console.error('Excel generation error:', error);
			return new Response(JSON.stringify({ error: error.message }), {
				status: 500,
				headers: {
					'Content-Type': 'application/json',
					'Access-Control-Allow-Origin': '*',
				},
			});
		}
	},
};

/**
 * Generate the complete weekly workbook
 */
async function generateWeeklyWorkbook(data) {
	const workbook = new ExcelJS.Workbook();

	// Set workbook properties
	workbook.creator = 'Foodikal NY Backend';
	workbook.created = new Date();

	const { customers, menu_items, aggregated_data, date_range } = data;

	// Date mapping: Thu (25) -> Wed (31)
	const dates = [
		'2025-12-25', // Thursday
		'2025-12-26', // Friday
		'2025-12-27', // Saturday
		'2025-12-28', // Sunday
		'2025-12-29', // Monday
		'2025-12-30', // Tuesday
		'2025-12-31', // Wednesday
	];

	const dayNames = ['ЗН ЧТ', 'ЗН ПТ', 'ЗН СБ', 'ЗН ВС', 'ЗН ПН', 'ЗН ВТ', 'ЗН СР'];
	const dayNamesShort = ['ЧТ', 'ПТ', 'СБ', 'ВС', 'ПН', 'ВТ', 'СР'];

	// Group menu items by category
	const categoryOrder = ['Брускетты', 'Горячее', 'Закуски', 'Канапе', 'Салаты', 'Тарталетки'];
	const menuByCategory = {};

	for (const item of menu_items) {
		const cat = item.category;
		if (!menuByCategory[cat]) {
			menuByCategory[cat] = [];
		}
		menuByCategory[cat].push(item);
	}

	// Create ordered menu items list
	const orderedMenuItems = [];
	for (const cat of categoryOrder) {
		if (menuByCategory[cat]) {
			orderedMenuItems.push(...menuByCategory[cat]);
		}
	}

	// Create daily sheets first (sheets 2-7 in spec, but we'll create them first)
	const dailySheets = [];
	for (let i = 0; i < 7; i++) {
		const sheet = createDailySheet(workbook, dayNames[i], dates[i], customers, orderedMenuItems, aggregated_data);
		dailySheets.push(sheet);
	}

	// Sheet 1: Main ЗАКАЗ sheet
	createMainOrderSheet(workbook, customers, orderedMenuItems, dates, dayNamesShort, dailySheets);

	// Sheet 8: Weekly summary
	createWeeklySummarySheet(workbook, orderedMenuItems, dailySheets, dayNamesShort);

	// Sheet 9: АКТЫ (Order confirmations)
	createActsSheet(workbook, customers, aggregated_data);

	// Sheets 10-14: Packing lists (simplified version)
	for (let i = 0; i < 5; i++) {
		const dayName = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ'][i];
		createPackingListSheet(workbook, `ЛС ${dayName}`, customers);
	}

	return workbook;
}

/**
 * Create daily sheet (ЗН ПН, ЗН ВТ, etc.)
 */
function createDailySheet(workbook, sheetName, date, customers, menuItems, aggregatedData) {
	const sheet = workbook.addWorksheet(sheetName);

	// Format date as DD.MM
	const dateObj = new Date(date);
	const dateStr = `${String(dateObj.getDate()).padStart(2, '0')}.${String(dateObj.getMonth() + 1).padStart(2, '0')}`;

	// Row 1: Header with date
	sheet.getCell('A1').value = `Готовим ${dateStr}`;
	sheet.getCell('B1').value = 'Сумма';
	sheet.mergeCells('B1:C1');

	// Add customer names starting from D1
	let col = 4; // Column D
	for (const customer of customers) {
		sheet.getCell(1, col).value = customer;
		col += 2; // Skip one column for customization
	}

	// Row 2: Column headers
	sheet.getCell('A2').value = 'Наименование позиции';
	sheet.getCell('B2').value = 'Всего';
	sheet.getCell('C2').value = 'Из всего кол-во кастомов';

	col = 4;
	for (let i = 0; i < customers.length; i++) {
		sheet.getCell(2, col).value = 'Всего';
		sheet.getCell(2, col + 1).value = 'Из всего кол-во кастомов';
		col += 2;
	}

	// Data rows: Add menu items
	let row = 3;
	for (const item of menuItems) {
		// Column A: Item name (multi-language format)
		const itemName = `${item.name}/${item.name}/${item.name}`; // TODO: Add actual translations if available
		sheet.getCell(row, 1).value = itemName;

		// Column B: Total quantity formula (sum of all customer quantities)
		const lastCustomerCol = 4 + (customers.length - 1) * 2;
		const formula = `=SUM(D${row}:${getColumnLetter(lastCustomerCol)}${row})`;
		sheet.getCell(row, 2).value = { formula };

		// Column C: Empty (customization)
		sheet.getCell(row, 3).value = '';

		// Customer columns
		col = 4;
		for (const customer of customers) {
			// Get quantity for this customer/date/item
			let quantity = 0;
			if (
				aggregatedData[customer] &&
				aggregatedData[customer][date] &&
				aggregatedData[customer][date][item.id]
			) {
				quantity = aggregatedData[customer][date][item.id];
			}

			// Even column: quantity
			sheet.getCell(row, col).value = quantity || '';

			// Odd column: empty (customization)
			sheet.getCell(row, col + 1).value = '';

			col += 2;
		}

		row++;
	}

	// Set column widths
	sheet.getColumn(1).width = 50; // Item name column
	sheet.getColumn(2).width = 12; // Total column
	sheet.getColumn(3).width = 12; // Customization column

	for (let i = 4; i <= 4 + customers.length * 2; i++) {
		sheet.getColumn(i).width = 10;
	}

	// Apply borders and formatting
	applyBorders(sheet, 1, 1, row - 1, 3 + customers.length * 2);

	return sheet;
}

/**
 * Create main ЗАКАЗ sheet
 */
function createMainOrderSheet(workbook, customers, menuItems, dates, dayNames, dailySheets) {
	const sheet = workbook.addWorksheet('ЗАКАЗ', { tabColor: { argb: 'FF00FF00' } });

	// This is a complex sheet - simplified implementation
	// Column A: Menu item names
	// Column B: Row numbers
	// Starting from Column C: Customer company pairs (15 columns per company)

	// Row 1: Headers
	sheet.getCell('A1').value = 'Наименование';
	sheet.getCell('B1').value = '№';

	let col = 3; // Column C
	for (const customer of customers) {
		sheet.getCell(1, col).value = customer;
		sheet.mergeCells(1, col, 1, col + 14); // Merge 15 columns for each customer
		col += 15;
	}

	// Row 2: Day headers for each customer
	col = 3;
	for (let i = 0; i < customers.length; i++) {
		for (let d = 0; d < 7; d++) {
			sheet.getCell(2, col + d).value = dayNames[d];
		}
		// Columns 7-13 are for customization
		for (let d = 7; d < 14; d++) {
			sheet.getCell(2, col + d).value = '';
		}
		// Column 14 is total
		sheet.getCell(2, col + 14).value = 'Итого';
		col += 15;
	}

	// Data rows
	let row = 3;
	for (const item of menuItems) {
		// Column A: Item name
		sheet.getCell(row, 1).value = `${item.name}/${item.name}/${item.name}`;

		// Column B: Row number
		sheet.getCell(row, 2).value = row - 2;

		// Customer columns
		col = 3;
		for (let custIdx = 0; custIdx < customers.length; custIdx++) {
			const customer = customers[custIdx];

			// 7 day columns
			for (let dayIdx = 0; dayIdx < 7; dayIdx++) {
				const date = dates[dayIdx];
				const dailySheet = dailySheets[dayIdx];

				// Reference to daily sheet
				const dailySheetCol = 4 + custIdx * 2; // Even columns in daily sheets
				const cellRef = `'${dailySheet.name}'!${getColumnLetter(dailySheetCol)}${row}`;
				sheet.getCell(row, col + dayIdx).value = { formula: `=${cellRef}` };
			}

			// 7 customization columns (empty)
			for (let d = 7; d < 14; d++) {
				sheet.getCell(row, col + d).value = '';
			}

			// Total column (sum of 7 days + 7 custom columns)
			const startCol = getColumnLetter(col);
			const endCol = getColumnLetter(col + 13);
			sheet.getCell(row, col + 14).value = { formula: `=SUM(${startCol}${row}:${endCol}${row})` };

			col += 15;
		}

		row++;
	}

	// Set column widths
	sheet.getColumn(1).width = 50;
	sheet.getColumn(2).width = 8;
	for (let i = 3; i <= 3 + customers.length * 15; i++) {
		sheet.getColumn(i).width = 8;
	}

	return sheet;
}

/**
 * Create weekly summary sheet
 */
function createWeeklySummarySheet(workbook, menuItems, dailySheets, dayNames) {
	const sheet = workbook.addWorksheet('ЗН НЕДЕЛЬНЫЙ');

	// Headers
	sheet.getCell('A1').value = 'Наименование позиции';
	for (let i = 0; i < 7; i++) {
		sheet.getCell(1, i + 2).value = dayNames[i];
	}
	sheet.getCell(1, 9).value = 'Итого';

	// Data rows
	let row = 2;
	for (const item of menuItems) {
		sheet.getCell(row, 1).value = `${item.name}/${item.name}/${item.name}`;

		// Reference daily sheets for quantities
		for (let dayIdx = 0; dayIdx < 7; dayIdx++) {
			const dailySheet = dailySheets[dayIdx];
			const cellRef = `'${dailySheet.name}'!B${row + 1}`; // Column B is the total column
			sheet.getCell(row, dayIdx + 2).value = { formula: `=${cellRef}` };
		}

		// Total column
		sheet.getCell(row, 9).value = { formula: `=SUM(B${row}:H${row})` };

		row++;
	}

	// Set column widths
	sheet.getColumn(1).width = 50;
	for (let i = 2; i <= 9; i++) {
		sheet.getColumn(i).width = 12;
	}

	return sheet;
}

/**
 * Create АКТЫ sheet (Order Confirmations)
 */
function createActsSheet(workbook, customers, aggregatedData) {
	const sheet = workbook.addWorksheet('АКТЫ');

	// Header
	sheet.getCell('A1').value = 'АКТ ЗАКАЗОВ / ORDER CONFIRMATION / ПОТВРДА О ПОРУЏБИНИ';
	sheet.mergeCells('A1:D1');
	sheet.getRow(1).font = { bold: true, size: 14 };
	sheet.getRow(1).alignment = { horizontal: 'center' };

	// Customer list
	let row = 3;
	sheet.getCell(row, 1).value = 'Компания / Company / Компанија';
	sheet.getCell(row, 2).value = 'Итого / Total / Укупно';
	sheet.getRow(row).font = { bold: true };
	row++;

	for (const customer of customers) {
		sheet.getCell(row, 1).value = customer;

		// Calculate total for this customer
		let total = 0;
		if (aggregatedData[customer]) {
			for (const date in aggregatedData[customer]) {
				for (const itemId in aggregatedData[customer][date]) {
					total += aggregatedData[customer][date][itemId];
				}
			}
		}
		sheet.getCell(row, 2).value = total;
		row++;
	}

	// Set column widths
	sheet.getColumn(1).width = 40;
	sheet.getColumn(2).width = 15;

	return sheet;
}

/**
 * Create packing list sheet (simplified)
 */
function createPackingListSheet(workbook, sheetName, customers) {
	const sheet = workbook.addWorksheet(sheetName);

	sheet.getCell('A1').value = `ЛИСТ СБОРКИ - ${sheetName}`;
	sheet.getRow(1).font = { bold: true, size: 12 };

	let row = 3;
	for (const customer of customers) {
		sheet.getCell(row, 1).value = customer;
		row++;
	}

	sheet.getColumn(1).width = 40;

	return sheet;
}

/**
 * Apply borders to a range of cells
 */
function applyBorders(sheet, startRow, startCol, endRow, endCol) {
	for (let row = startRow; row <= endRow; row++) {
		for (let col = startCol; col <= endCol; col++) {
			sheet.getCell(row, col).border = {
				top: { style: 'thin' },
				left: { style: 'thin' },
				bottom: { style: 'thin' },
				right: { style: 'thin' },
			};
		}
	}
}

/**
 * Convert column number to letter (1 = A, 2 = B, etc.)
 */
function getColumnLetter(col) {
	let letter = '';
	while (col > 0) {
		const mod = (col - 1) % 26;
		letter = String.fromCharCode(65 + mod) + letter;
		col = Math.floor((col - 1) / 26);
	}
	return letter;
}
