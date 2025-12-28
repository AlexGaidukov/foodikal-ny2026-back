/**
 * Excel Generator Worker for Foodikal NY - Single ЗАКАЗ Sheet
 * Generates order sheet with fixed structure
 */

import ExcelJS from 'exceljs';

export default {
	async fetch(request, env, ctx) {
		// CORS handling
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
			return new Response(JSON.stringify({ error: 'Method not allowed' }), {
				status: 405,
				headers: { 'Content-Type': 'application/json' }
			});
		}

		try {
			// Parse incoming data
			const data = await request.json();
			console.log('Received data:', {
				menuItemsCount: data.menu_items?.length,
				ordersCount: data.orders?.length,
				dateRangePreset: data.date_range?.preset
			});

			// Generate Excel workbook
			const workbook = await generateOrderSheet(data);

			// Write to buffer
			const buffer = await workbook.xlsx.writeBuffer();
			console.log('Excel buffer generated, size:', buffer.byteLength);

			// Determine filename based on date range preset
			const preset = data.date_range?.preset || 'full_week';
			const filenameMap = {
				'first_half': 'Заказы_нг_фуршет_25-28.xlsx',
				'second_half': 'Заказы_нг_фуршет_29-31.xlsx',
				'full_week': 'Заказы_фуршет_нг.xlsx'
			};
			const filename = filenameMap[preset] || 'Заказы_фуршет_нг.xlsx';

			// Encode filename for HTTP header (RFC 2231)
			const encodedFilename = encodeURIComponent(filename);

			// Return Excel file
			return new Response(buffer, {
				status: 200,
				headers: {
					'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
					'Content-Disposition': `attachment; filename*=UTF-8''${encodedFilename}`,
					'Content-Length': buffer.byteLength.toString(),
					'Access-Control-Allow-Origin': '*',
				},
			});
		} catch (error) {
			console.error('Excel generation error:', error);
			return new Response(JSON.stringify({
				error: 'Excel generation failed',
				message: error.message,
				stack: error.stack
			}), {
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
 * Sheet structure definition - Column A content
 * Format: { type: 'category'|'item', display: 'Display name', itemId: database_id }
 */
const SHEET_STRUCTURE = [
	{ row: 1, type: 'empty', display: '' },
	{ row: 2, type: 'empty', display: '' },
	{ row: 3, type: 'header', display: 'Наименование позиции' },
	{ row: 4, type: 'category', display: 'Брускетты' },
	{ row: 5, type: 'item', display: 'Брускетта с вяленой свининой (60г)', itemId: 9 },
	{ row: 6, type: 'item', display: 'Брускетта с гравлаксом (60г)', itemId: 10 },
	{ row: 7, type: 'item', display: 'Брускетта с грибной икрой (60г)', itemId: 11 },
	{ row: 8, type: 'item', display: 'Брускетта с грушей и горгонзоллой (60г)', itemId: 12 },
	{ row: 9, type: 'item', display: 'Брускетта с гуакамоле (60г)', itemId: 13 },
	{ row: 10, type: 'item', display: 'Брускетта с паштетом из куриной печени (60г)', itemId: 14 },
	{ row: 11, type: 'item', display: 'Брускетта с пршутом и персиком (60г)', itemId: 15 },
	{ row: 12, type: 'item', display: 'Брускетта с рикоттой (60г)', itemId: 16 },
	{ row: 13, type: 'item', display: 'Брускетта с творожным сыром и сладким перцем (60г)', itemId: 17 },
	{ row: 14, type: 'item', display: 'Брускетта с хумусом и свежими овощами (60г)', itemId: 18 },
	{ row: 15, type: 'item', display: 'Брускетта с шампиньонами (60г)', itemId: 19 },
	// Hidden rows 16-44
	{ row: 45, type: 'category', display: 'Горячее' },
	{ row: 46, type: 'item', display: 'Баранья нога  (запеченая, 1780г )', itemId: 20 },
	{ row: 47, type: 'item', display: 'Куриный шашлычок с картофелем фри (200г)', itemId: 21 },
	{ row: 48, type: 'item', display: 'Овощи гриль ( 550 г )', itemId: 22 },
	{ row: 49, type: 'item', display: 'Рулетики из ветчины с сыром (2шт, 120г)', itemId: 23 },
	{ row: 50, type: 'item', display: 'Свиная рулька ( 1100 г )', itemId: 24 },
	{ row: 51, type: 'item', display: 'Свиной шашлычок (100г)', itemId: 25 },
	{ row: 52, type: 'item', display: 'Тушеная капуста ( 650-700 г )', itemId: 26 },
	// Hidden rows 53-65
	{ row: 66, type: 'category', display: 'Закуски' },
	{ row: 67, type: 'item', display: 'Ассорти сыров и мясных деликатесов (300г)', itemId: 27 },
	{ row: 68, type: 'item', display: 'Хумус с баклажаном (закуска, 1шт 50г)', itemId: 28 },
	// Hidden rows 69-86
	{ row: 87, type: 'category', display: 'Канапе' },
	{ row: 88, type: 'item', display: 'Канапе овощное (45г)', itemId: 29 },
	{ row: 89, type: 'item', display: 'Канапе с ветчиной (40г)', itemId: 30 },
	{ row: 90, type: 'item', display: 'Канапе с грушей и пршутом (25г)', itemId: 31 },
	{ row: 91, type: 'item', display: 'Канапе с креветкой и авокадо (25г)', itemId: 32 },
	{ row: 92, type: 'item', display: 'Канапе с салями и вяленым томатом (55г)', itemId: 33 },
	{ row: 93, type: 'item', display: 'Канапе с салями и черным хлебом (20г)', itemId: 34 },
	{ row: 94, type: 'item', display: 'Канапе с сыром и виноградом (30г)', itemId: 35 },
	{ row: 95, type: 'item', display: 'Канапе фруктовое (60г)', itemId: 36 },
	{ row: 96, type: 'category', display: 'Салаты' },
	{ row: 97, type: 'item', display: 'Винегрет (мини-порция, 120г)', itemId: 37 },
	{ row: 98, type: 'item', display: 'Крабовый салат (1кг, без огурца)', itemId: 38 },
	{ row: 99, type: 'item', display: 'Крабовый салат (мини-порция, 120г)', itemId: 40 },
	{ row: 100, type: 'item', display: 'Оливье с говядиной (1кг)', itemId: 41 },
	{ row: 101, type: 'item', display: 'Оливье с говядиной (мини-порция, 120г)', itemId: 42 },
	{ row: 102, type: 'item', display: 'Селедка под шубой (1кг)', itemId: 39 },
	{ row: 103, type: 'empty', display: '' },
	// Hidden rows 104-127
	{ row: 128, type: 'category', display: 'Тарталетки' },
	{ row: 129, type: 'item', display: 'Тарталетка с икрой (имитация, 35г)', itemId: 43 },
	{ row: 130, type: 'item', display: 'Тарталетка с крабовым салатом (30г)', itemId: 44 },
	{ row: 131, type: 'item', display: 'Тарталетка с креветкой (30г)', itemId: 45 },
	{ row: 132, type: 'item', display: 'Тарталетка со свекольным муссом и сельдью (35г)', itemId: 46 },
	{ row: 133, type: 'item', display: 'Тарталетка со слабосоленым лососем (35г)', itemId: 47 },
];

// Hidden row ranges
const HIDDEN_ROWS = [
	{ start: 16, end: 44 },   // After Брускетты
	{ start: 53, end: 65 },   // After Горячее
	{ start: 69, end: 86 },   // After Закуски
	{ start: 104, end: 127 }, // After Салаты
];

/**
 * Date to weekday mapping for Dec 25-31, 2025
 * Maps weekday name to actual date
 */
const WEEKDAY_TO_DATE = {
	'mon': '2025-12-29',
	'tue': '2025-12-30',
	'wed': '2025-12-31',
	'thu': '2025-12-25',
	'fri': '2025-12-26',
	'sat': '2025-12-27',
	'sun': '2025-12-28',
};

const WEEKDAY_ORDER = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];

/**
 * Generate the order sheet workbook
 */
async function generateOrderSheet(data) {
	const workbook = new ExcelJS.Workbook();

	workbook.creator = 'Foodikal NY Backend';
	workbook.created = new Date();
	workbook.modified = new Date();

	const { aggregated_data = {}, customers = [] } = data;

	console.log('Creating ЗАКАЗ sheet with', customers.length, 'customers');

	// Create single sheet named "ЗАКАЗ"
	const sheet = workbook.addWorksheet('ЗАКАЗ');

	// Set column widths for A and B
	sheet.getColumn(1).width = 50; // Column A - Item names
	sheet.getColumn(2).width = 0.71; // Column B - 5px spacer

	// Populate Column A and B according to structure
	for (const row of SHEET_STRUCTURE) {
		const cell = sheet.getCell(row.row, 1);
		cell.value = row.display;

		// Style headers and categories
		if (row.type === 'header' || row.type === 'category') {
			cell.font = { bold: true };
		}

		// Add border to all non-empty cells
		if (row.type !== 'empty') {
			cell.border = {
				top: { style: 'thin' },
				left: { style: 'thin' },
				bottom: { style: 'thin' },
				right: { style: 'thin' },
			};
		}

		// Column B - always empty
		const cellB = sheet.getCell(row.row, 2);
		cellB.value = '';
		if (row.type !== 'empty') {
			cellB.border = {
				top: { style: 'thin' },
				left: { style: 'thin' },
				bottom: { style: 'thin' },
				right: { style: 'thin' },
			};
		}
	}

	// Add customer columns
	customers.forEach((customerName, customerIndex) => {
		const startCol = 3 + (customerIndex * 15); // C=3, R=18, AG=33, etc. (14 data cols + 1 spacer)

		createCustomerColumns(sheet, customerName, startCol, aggregated_data[customerName] || {});
	});

	// Hide specified row ranges between categories
	console.log('Hiding rows in ranges:', HIDDEN_ROWS);
	HIDDEN_ROWS.forEach(range => {
		for (let rowNum = range.start; rowNum <= range.end; rowNum++) {
			const row = sheet.getRow(rowNum);
			// Set a value to ensure row exists in XML (empty string in column A)
			row.getCell(1).value = '';
			row.hidden = true;
			row.commit();
		}
	});
	console.log('Row hiding complete');

	console.log('ЗАКАЗ sheet generation complete');

	return workbook;
}

/**
 * Create column block for a single customer
 */
function createCustomerColumns(sheet, customerName, startCol, customerData) {
	// Set column widths for all 14 data columns (2px each - 5x narrower)
	for (let i = 0; i < 14; i++) {
		sheet.getColumn(startCol + i).width = 2;
	}

	// Row 1: Customer name header
	sheet.mergeCells(1, startCol, 1, startCol + 6); // C1:I1
	const nameCell = sheet.getCell(1, startCol);
	nameCell.value = customerName;
	nameCell.font = { bold: true };
	nameCell.alignment = { horizontal: 'center' };
	nameCell.border = {
		top: { style: 'thin' },
		left: { style: 'thin' },
		bottom: { style: 'thin' },
		right: { style: 'thin' },
	};

	// Row 1: Empty merged cell for custom section
	sheet.mergeCells(1, startCol + 7, 1, startCol + 13); // J1:P1
	const emptyCell = sheet.getCell(1, startCol + 7);
	emptyCell.value = '';
	emptyCell.border = {
		top: { style: 'thin' },
		left: { style: 'thin' },
		bottom: { style: 'thin' },
		right: { style: 'thin' },
	};

	// Row 2: "Total" header
	sheet.mergeCells(2, startCol, 2, startCol + 6); // C2:I2
	const totalCell = sheet.getCell(2, startCol);
	totalCell.value = 'Total';
	totalCell.font = { bold: true };
	totalCell.alignment = { horizontal: 'center' };
	totalCell.border = {
		top: { style: 'thin' },
		left: { style: 'thin' },
		bottom: { style: 'thin' },
		right: { style: 'thin' },
	};

	// Row 2: "Custom" header
	sheet.mergeCells(2, startCol + 7, 2, startCol + 13); // J2:P2
	const customCell = sheet.getCell(2, startCol + 7);
	customCell.value = 'Custom';
	customCell.font = { bold: true };
	customCell.alignment = { horizontal: 'center' };
	customCell.border = {
		top: { style: 'thin' },
		left: { style: 'thin' },
		bottom: { style: 'thin' },
		right: { style: 'thin' },
	};

	// Row 3: Day labels (Total section)
	WEEKDAY_ORDER.forEach((day, index) => {
		const col = startCol + index;
		const cell = sheet.getCell(3, col);
		cell.value = day;
		cell.font = { bold: true };
		cell.alignment = { horizontal: 'center' };
		cell.border = {
			top: { style: 'thin' },
			left: { style: 'thin' },
			bottom: { style: 'thin' },
			right: { style: 'thin' },
		};
	});

	// Row 3: Day labels (Custom section)
	WEEKDAY_ORDER.forEach((day, index) => {
		const cell = sheet.getCell(3, startCol + 7 + index);
		cell.value = day;
		cell.font = { bold: true };
		cell.alignment = { horizontal: 'center' };
		cell.border = {
			top: { style: 'thin' },
			left: { style: 'thin' },
			bottom: { style: 'thin' },
			right: { style: 'thin' },
		};
	});

	// Rows 4-48: Data
	for (const rowDef of SHEET_STRUCTURE) {
		if (rowDef.type === 'item') {
			// Total columns (C-I)
			WEEKDAY_ORDER.forEach((day, dayIndex) => {
				const date = WEEKDAY_TO_DATE[day];
				const quantity = (customerData[date] && customerData[date][rowDef.itemId]) || 0;

				const cell = sheet.getCell(rowDef.row, startCol + dayIndex);
				cell.value = quantity > 0 ? quantity : '';
				cell.border = {
					top: { style: 'thin' },
					left: { style: 'thin' },
					bottom: { style: 'thin' },
					right: { style: 'thin' },
				};
			});

			// Custom columns (J-P) - empty
			for (let i = 0; i < 7; i++) {
				const cell = sheet.getCell(rowDef.row, startCol + 7 + i);
				cell.value = '';
				cell.border = {
					top: { style: 'thin' },
					left: { style: 'thin' },
					bottom: { style: 'thin' },
					right: { style: 'thin' },
				};
			}
		} else if (rowDef.type === 'category') {
			// Add borders to category rows (but NOT header row 3 which has day labels)
			for (let i = 0; i < 14; i++) {
				const cell = sheet.getCell(rowDef.row, startCol + i);
				cell.value = '';
				cell.border = {
					top: { style: 'thin' },
					left: { style: 'thin' },
					bottom: { style: 'thin' },
					right: { style: 'thin' },
				};
			}
		} else if (rowDef.type === 'header') {
			// Header row (row 3) already has day labels set above, just add borders
			for (let i = 0; i < 14; i++) {
				const cell = sheet.getCell(rowDef.row, startCol + i);
				// Don't set value - day labels already set above
				if (!cell.value) {
					cell.border = {
						top: { style: 'thin' },
						left: { style: 'thin' },
						bottom: { style: 'thin' },
						right: { style: 'thin' },
					};
				}
			}
		}
	}

	// Spacer column Q (5px width)
	const spacerCol = startCol + 14;
	sheet.getColumn(spacerCol).width = 0.71;
	for (let row = 1; row <= 48; row++) {
		sheet.getCell(row, spacerCol).value = '';
	}
}
