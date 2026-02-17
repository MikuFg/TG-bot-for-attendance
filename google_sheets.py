import asyncio

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
        """Возвращает список студентов, у которых есть username (для отметки)."""
        agc = await self.agcm.authorize()
        ss = await agc.open_by_key(self.spreadsheet_id)
        worksheet = await ss.get_worksheet(0)
        rows = await worksheet.get_all_values()

        students = []
        # Пропускаем заголовок (первая строка)
        for row in rows[1:]:
            # Проверяем, что в строке есть данные и есть username в колонке C (индекс 2)
            if len(row) >= 3 and row[2].strip():
                students.append({
                    "name": row[0].strip() if len(row) > 0 else "",
                    "group": row[1].strip() if len(row) > 1 else "",
                    "username": row[2].strip().lstrip('@').lower()
                })
        return students

    async def get_all_students_count(self):
        """Возвращает общее количество студентов в таблице (включая тех, у кого нет username)."""
        agc = await self.agcm.authorize()
        ss = await agc.open_by_key(self.spreadsheet_id)
        worksheet = await ss.get_worksheet(0)
        rows = await worksheet.get_all_values()
        return len(rows) - 1  # минус заголовок

    async def get_next_lesson_title(self):
        """Определяет следующее занятие на основе заголовков в первой строке (начиная с колонки D)."""
        agc = await self.agcm.authorize()
        ss = await agc.open_by_key(self.spreadsheet_id)
        worksheet = await ss.get_worksheet(0)
        header = await worksheet.row_values(1)

        # Заголовки занятий начинаются с колонки D (индекс 3)
        lesson_titles = header[3:]
        max_num = 0

        for title in lesson_titles:
            title = title.strip()
            if title and title.endswith(" занятие"):
                try:
                    num = int(title.split()[0])
                    if num > max_num:
                        max_num = num
                except (ValueError, IndexError):
                    pass

        next_num = max_num + 1
        return f"{next_num} занятие"

    async def update_attendance(self, lesson_title, username_status):
        """
        lesson_title: название занятия (например, "4 занятие")
        username_status: dict {username: '+' or '-'} - только для студентов с username
        """
        agc = await self.agcm.authorize()
        ss = await agc.open_by_key(self.spreadsheet_id)
        worksheet = await ss.get_worksheet(0)
        all_rows = await worksheet.get_all_values()

        if not all_rows:
            print("Таблица пуста")
            return

        header = all_rows[0]

        # Ищем столбец с нужным названием занятия (начиная с колонки D)
        col_index = None
        for i, title in enumerate(header[3:], start=4):
            if title.strip() == lesson_title:
                col_index = i
                break

        if col_index is None:
            # Если такого занятия нет, добавляем новый столбец справа
            col_index = len(header) + 1
            col_letter = self._get_column_letter(col_index)
            await worksheet.update(f"{col_letter}1", lesson_title)
            print(f"Создан новый столбец {col_letter} с названием '{lesson_title}'")
        else:
            col_letter = self._get_column_letter(col_index)
            print(f"Найден существующий столбец {col_letter} с названием '{lesson_title}'")

        # Формируем обновления для каждой строки
        updates = []
        updated_count = 0
        students_without_username = 0

        for row_idx, row in enumerate(all_rows[1:], start=2):
            # Проверяем, есть ли username в колонке C
            if len(row) < 3 or not row[2].strip():
                students_without_username += 1
                continue  # пропускаем, у них автоматически будет минус (пустая ячейка)

            username = row[2].strip().lstrip('@').lower()
            status = username_status.get(username, '-')

            cell_range = f"{col_letter}{row_idx}"
            updates.append({
                'range': cell_range,
                'values': [[status]]
            })
            updated_count += 1

        if updates:
            print(f"Отправляем {len(updates)} обновлений в Google Sheets")
            print(f"Пример: {updates[0]}")
            try:
                await worksheet.batch_update(updates)
                print(f"✅ Успешно обновлено {updated_count} ячеек")
                print(f"👤 Пропущено студентов без username: {students_without_username}")
            except Exception as e:
                print(f"❌ Ошибка при batch_update: {e}")
                # Пробуем обновить по одной ячейке
                print("Пробуем обновить по одной ячейке...")
                for update in updates:
                    try:
                        await worksheet.update(update['range'], update['values'])
                        await asyncio.sleep(0.1)
                    except Exception as cell_error:
                        print(f"Ошибка при обновлении {update['range']}: {cell_error}")
        else:
            print("Нет данных для обновления")

        return students_without_username

    def _get_column_letter(self, col_index):
        letters = ""
        while col_index > 0:
            col_index -= 1
            letters = chr(col_index % 26 + 65) + letters
            col_index //= 26
        return letters