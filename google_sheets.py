import gspread_asyncio
from google.oauth2.service_account import Credentials
from config import GOOGLE_SHEETS_CREDENTIALS_FILE, GOOGLE_SHEETS_SPREADSHEET_ID

class GoogleSheetsClient:
    def __init__(self):
        self.agcm = gspread_asyncio.AsyncioGspreadClientManager(self.get_creds)
        self.spreadsheet_id = GOOGLE_SHEETS_SPREADSHEET_ID

    def get_creds(self):
        return Credentials.from_service_account_file(
            GOOGLE_SHEETS_CREDENTIALS_FILE,
            scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        )

    async def get_students(self):
        """Возвращает список студентов с полями 'name' и 'username' (приведён к нижнему регистру)."""
        agc = await self.agcm.authorize()
        ss = await agc.open_by_key(self.spreadsheet_id)
        worksheet = await ss.get_worksheet(0)  # первый лист
        rows = await worksheet.get_all_values()
        students = []
        for row in rows[1:]:  # пропускаем заголовок
            if len(row) >= 2 and row[1]:
                students.append({
                    "name": row[0],
                    "username": row[1].strip().lstrip('@').lower()
                })
        return students

    async def get_next_lesson_title(self):
        """Определяет следующее занятие на основе заголовков в первой строке (начиная с колонки C)."""
        agc = await self.agcm.authorize()
        ss = await agc.open_by_key(self.spreadsheet_id)
        worksheet = await ss.get_worksheet(0)
        header = await worksheet.row_values(1)  # получаем первую строку

        # Заголовки занятий начинаются с колонки C (индекс 2)
        lesson_titles = header[2:]  # срез от колонки C до конца
        max_num = 0
        for title in lesson_titles:
            title = title.strip()
            if title and title.endswith(" занятие"):
                try:
                    num = int(title.split()[0])  # берём число перед " занятие"
                    if num > max_num:
                        max_num = num
                except:
                    pass
        next_num = max_num + 1
        return f"{next_num} занятие"

    async def update_attendance(self, lesson_title, username_status):
        """
        lesson_title: название занятия (например, "4 занятие")
        username_status: dict {username: '+' or '-'}
        Обновляет столбец с названием занятия в первом листе.
        """
        agc = await self.agcm.authorize()
        ss = await agc.open_by_key(self.spreadsheet_id)
        worksheet = await ss.get_worksheet(0)
        all_rows = await worksheet.get_all_values()
        if not all_rows:
            return

        header = all_rows[0]  # первая строка (заголовки)

        # Ищем столбец с нужным названием занятия
        col_index = None
        for i, title in enumerate(header):
            if title.strip() == lesson_title:
                col_index = i + 1  # 1-based индекс для Google Sheets
                break

        if col_index is None:
            # Если такого занятия нет, добавляем новый столбец справа
            col_index = len(header) + 1
            col_letter = self._get_column_letter(col_index)
            # Записываем название занятия в первую ячейку нового столбца
            await worksheet.update(f"{col_letter}1", lesson_title)
        else:
            col_letter = self._get_column_letter(col_index)

        # Формируем обновления для каждой строки (каждый студент)
        updates = []
        for row_idx, row in enumerate(all_rows[1:], start=2):  # начиная со 2 строки
            if len(row) < 2:
                continue
            username = row[1].strip().lstrip('@').lower()
            if not username:
                continue
            status = username_status.get(username, '-')
            cell_range = f"{col_letter}{row_idx}"
            updates.append({
                'range': cell_range,
                'values': [[status]]
            })

        if updates:
            await worksheet.batch_update(updates)

    def _get_column_letter(self, col_index):
        letters = ""
        while col_index > 0:
            col_index -= 1
            letters = chr(col_index % 26 + 65) + letters
            col_index //= 26
        return letters