/**
 * Minimal Excel test worker
 */

import ExcelJS from 'exceljs';

export default {
	async fetch(request, env, ctx) {
		try {
			console.log('Creating minimal workbook');

			const workbook = new ExcelJS.Workbook();
			workbook.creator = 'Test';
			workbook.created = new Date();

			const sheet = workbook.addWorksheet('Test Sheet');

			// Add simple data
			sheet.getCell('A1').value = 'Hello';
			sheet.getCell('B1').value = 'World';
			sheet.getCell('A2').value = 123;
			sheet.getCell('B2').value = 456;

			console.log('Writing buffer');
			const buffer = await workbook.xlsx.writeBuffer();
			console.log('Buffer size:', buffer.byteLength);

			return new Response(buffer, {
				status: 200,
				headers: {
					'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
					'Content-Disposition': 'attachment; filename="test.xlsx"',
					'Content-Length': buffer.byteLength.toString(),
				},
			});
		} catch (error) {
			console.error('Error:', error);
			return new Response(JSON.stringify({
				error: error.message,
				stack: error.stack
			}), {
				status: 500,
				headers: { 'Content-Type': 'application/json' }
			});
		}
	},
};
