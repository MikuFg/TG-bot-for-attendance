import asyncio
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import ADMIN_IDS, GROUP_CHAT_ID
from google_sheets import GoogleSheetsClient
from attendance import get_session, set_session, delete_session, Session

router = Router()
gs_client = GoogleSheetsClient()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# -------------------------------------------------------------------
# Команда /start (личные сообщения)
# -------------------------------------------------------------------
@router.message(Command("start"), F.chat.type == "private")
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я бот для отметки посещаемости.\n\n"
        "Команды для администратора (только в личке):\n"
        "/start_session [название] [минут] — начать отметку (название опционально)\n"
        "/stop_session — завершить досрочно\n"
        "/status — количество отметившихся"
    )

# -------------------------------------------------------------------
# Команда /start_session (личные сообщения)
# -------------------------------------------------------------------
@router.message(Command("start_session"), F.chat.type == "private")
async def cmd_start_session(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ У вас нет прав администратора.")

    if GROUP_CHAT_ID == 0:
        return await message.answer("❌ Ошибка: не указан ID группы в конфигурации.")

    # Проверяем, нет ли уже активной сессии для этой группы
    if get_session(GROUP_CHAT_ID) and get_session(GROUP_CHAT_ID).active:
        return await message.answer("⚠️ В группе уже активна сессия отметки.")

    # Разбор аргументов
    args = message.text.split()
    lesson_title = None
    timeout_minutes = None

    if len(args) >= 2:
        lesson_title = args[1]
        if len(args) >= 3 and args[2].isdigit():
            timeout_minutes = int(args[2])
    else:
        # Автоопределение следующего занятия
        try:
            lesson_title = await gs_client.get_next_lesson_title()
            await message.answer(f"🆕 Автоматически определено следующее занятие: **{lesson_title}**")
        except Exception as e:
            logging.error(f"Не удалось определить следующее занятие: {e}")
            return await message.answer("❌ Ошибка при определении следующего занятия. Укажите название вручную.")

    # Отправляем сообщение с кнопкой в группу (без звука)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отметиться", callback_data="mark")]
    ])
    try:
        msg = await message.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=f"📢 Отметка на занятие **{lesson_title}** началась!\nНажмите кнопку, чтобы подтвердить присутствие.",
            reply_markup=keyboard,
            parse_mode="Markdown",
            disable_notification=True
        )
    except Exception as e:
        logging.error(f"Не удалось отправить сообщение в группу: {e}")
        return await message.answer("❌ Ошибка при отправке сообщения в группу. Проверьте, добавлен ли бот в группу и есть ли у него права.")

    # Создаём сессию для группы
    session = Session(
        group_chat_id=GROUP_CHAT_ID,
        message_id=msg.message_id,
        lesson_title=lesson_title,
        admin_chat_id=message.chat.id
    )
    set_session(GROUP_CHAT_ID, session)

    # Загружаем список студентов (фоново)
    asyncio.create_task(load_students_for_session(GROUP_CHAT_ID))

    # Ответ админу
    response = f"✅ Сессия для занятия **{lesson_title}** запущена в группе."
    if timeout_minutes:
        asyncio.create_task(auto_stop_session(GROUP_CHAT_ID, message.bot, timeout_minutes * 60))
        response += f" Отметка продлится {timeout_minutes} мин."
    else:
        response += " Остановите вручную командой /stop_session."
    await message.answer(response)

# -------------------------------------------------------------------
# Команда /stop_session (личные сообщения)
# -------------------------------------------------------------------
@router.message(Command("stop_session"), F.chat.type == "private")
async def cmd_stop_session(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ У вас нет прав администратора.")

    if GROUP_CHAT_ID == 0:
        return await message.answer("❌ Ошибка: не указан ID группы.")

    session = get_session(GROUP_CHAT_ID)
    if not session or not session.active:
        return await message.answer("⚠️ В группе нет активной сессии.")

    await finalize_session(GROUP_CHAT_ID, message.bot)

# -------------------------------------------------------------------
# Команда /status (личные сообщения)
# -------------------------------------------------------------------
@router.message(Command("status"), F.chat.type == "private")
async def cmd_status(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ У вас нет прав администратора.")

    if GROUP_CHAT_ID == 0:
        return await message.answer("❌ Ошибка: не указан ID группы.")

    session = get_session(GROUP_CHAT_ID)
    if not session or not session.active:
        return await message.answer("⚠️ В группе нет активной сессии.")

    async with session.lock:
        count = len(session.marked_users)
    await message.answer(f"👥 В группе отметилось: **{count}** человек.")

# -------------------------------------------------------------------
# Обработчик нажатия кнопки "Отметиться" (работает в группе)
# -------------------------------------------------------------------
@router.callback_query(F.data == "mark")
async def callback_mark(callback: CallbackQuery):
    group_chat_id = callback.message.chat.id
    user = callback.from_user
    session = get_session(group_chat_id)

    if not session or not session.active:
        await callback.answer("❌ Отметка не активна.", show_alert=False)
        return

    if not user.username:
        await callback.answer(
            "❌ У вас не установлен username. Пожалуйста, установите его в настройках Telegram.",
            show_alert=True
        )
        return

    username = user.username.lower()

    # Проверяем, есть ли студент в списке (если список загружен)
    if session.students_set is not None and username not in session.students_set:
        await callback.answer("❌ Вы не найдены в списке студентов. Отметка не засчитана.", show_alert=True)
        return

    async with session.lock:
        if username in session.marked_users:
            await callback.answer("✅ Вы уже отмечены.", show_alert=False)
        else:
            session.marked_users.add(username)
            await callback.answer("✅ Вы отмечены!", show_alert=False)

# -------------------------------------------------------------------
# Вспомогательные функции
# -------------------------------------------------------------------
async def load_students_for_session(group_chat_id: int):
    """Загружает список студентов из Google Sheets и сохраняет в сессию."""
    session = get_session(group_chat_id)
    if not session:
        return
    try:
        students = await gs_client.get_students()
        session.students_set = {s["username"] for s in students if s["username"]}
        logging.info(f"Загружено {len(session.students_set)} студентов для группы {group_chat_id}")
    except Exception as e:
        logging.error(f"Failed to load students: {e}")

async def auto_stop_session(group_chat_id: int, bot, delay: int):
    """Автоматически завершает сессию через указанное количество секунд."""
    await asyncio.sleep(delay)
    session = get_session(group_chat_id)
    if session and session.active:
        await finalize_session(group_chat_id, bot)

async def finalize_session(group_chat_id: int, bot):
    """Завершает сессию: удаляет сообщение с кнопкой, обновляет Google Sheets, отправляет отчёт админу."""
    session = get_session(group_chat_id)
    if not session:
        return

    async with session.lock:
        session.active = False
        marked_ids = session.marked_users.copy()

    # 1. Удаляем сообщение с кнопкой из группы
    try:
        await bot.delete_message(chat_id=group_chat_id, message_id=session.message_id)
        logging.info(f"Сообщение с кнопкой удалено из группы {group_chat_id}")
    except Exception as e:
        logging.warning(f"Не удалось удалить сообщение из группы: {e}")
        # Пытаемся хотя бы убрать кнопку
        try:
            await bot.edit_message_text(
                "🔒 Отметка завершена.",
                chat_id=group_chat_id,
                message_id=session.message_id,
                reply_markup=None
            )
        except:
            pass

    # 2. Получаем студентов из таблицы
    try:
        students = await gs_client.get_students()
    except Exception as e:
        logging.error(f"Failed to get students: {e}")
        await bot.send_message(session.admin_chat_id, "❌ Ошибка при получении списка студентов из таблицы.")
        delete_session(group_chat_id)
        return

    # 3. Формируем статусы для Google Sheets
    username_status = {}
    for student in students:
        username = student["username"]
        if not username:
            status = '-'
        else:
            status = '+' if username in marked_ids else '-'
        username_status[username] = status

    # 4. Записываем в Google Sheets
    try:
        await gs_client.update_attendance(session.lesson_title, username_status)
        total = len(students)
        present = len(marked_ids)
        # Отправляем отчёт админу
        await bot.send_message(
            session.admin_chat_id,
            f"📊 **Итоги отметки**\n"
            f"Занятие: **{session.lesson_title}**\n"
            f"Присутствовало: **{present}** из **{total}**\n"
            f"Отсутствовало: **{total - present}**",
            disable_notification=True
        )
    except Exception as e:
        logging.error(f"Failed to update attendance: {e}")
        await bot.send_message(session.admin_chat_id, "❌ Ошибка при обновлении таблицы.")
    finally:
        delete_session(group_chat_id)