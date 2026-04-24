import asyncio
import logging
from typing import Optional

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters.command import Command
from aiogram.types import (
    Message, LabeledPrice, PreCheckoutQuery
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.methods.base import TelegramMethod

# Токен бота (совет: не делись им в публичных местах!)
BOT_TOKEN = "7604253117:AAFjrfCahWV0taFPHdAreyEo3zBiNHl_sEI"

logging.basicConfig(level=logging.INFO)

# Улучшенный метод для отправки Star Gift через API Telegram
class SendGift(TelegramMethod[bool]):
    __returning__ = bool
    __api_method__ = "sendGift"

    gift_id: str
    user_id: Optional[int] = None
    chat_id: Optional[int] = None
    text: Optional[str] = None
    text_parse_mode: Optional[str] = "HTML"  # Позволяет использовать <b>, <i> и т.д.
    is_anonymous: Optional[bool] = None      # Можно поставить True, чтобы скрыть отправителя

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- КОМАНДА ОТПРАВКИ ПОДАРКА ---
@dp.message(Command("gift"))
async def gift_command(message: Message):
    """
    /gift GIFT_ID USER_ID [Текст подписи]
    Пример: /gift 5922558454332916696 123456789 С днюхой, бро! 🎉
    """
    # maxsplit=3: разделяем на ['/gift', 'ID_подарка', 'ID_юзера', 'Весь остальной текст']
    args = message.text.split(maxsplit=3)
    
    if len(args) < 3:
        await message.answer(
            "⚠️ <b>Недостаточно данных!</b>\n\n"
            "Формат: <code>/gift GIFT_ID USER_ID Текст подписи</code>\n"
            "Пример: <code>/gift 5922558454332916696 123456789 С днюхой!</code>"
        )
        return

    gift_id = args[1]
    
    try:
        target_id = int(args[2])
    except ValueError:
        await message.answer("❌ <b>USER_ID</b> должен быть числом.")
        return

    # Извлекаем текст, если он есть (аргумент под индексом 3)
    gift_message = args[3] if len(args) > 3 else None
    
    # Лимит Telegram на длину текста в подарке — около 128 символов
    if gift_message and len(gift_message) > 128:
        await message.answer("❌ <b>Ошибка:</b> Текст слишком длинный (макс. 128 символов).")
        return

    try:
        # Отправляем подарок через наш кастомный метод
        if target_id > 0:
            await bot(SendGift(user_id=target_id, gift_id=gift_id, text=gift_message))
        else:
            await bot(SendGift(chat_id=target_id, gift_id=gift_id, text=gift_message))

        success_msg = f"✅ <b>Подарок успешно отправлен!</b>\n👤 Получатель: <code>{target_id}</code>"
        if gift_message:
            success_msg += f"\n📝 С подписью: <i>{gift_message}</i>"
            
        await message.answer(success_msg)

    except Exception as e:
        logging.error(f"Ошибка при отправке подарка: {e}")
        await message.answer(f"❌ <b>Ошибка API:</b>\n<code>{e}</code>")

# --- КОМАНДА ВЫСТАВЛЕНИЯ СЧЕТА (Звезды) ---
@dp.message(Command("invoice"))
async def invoice_command(message: Message):
    """
    /invoice {количество звезд}
    """
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "Использование: <code>/invoice {количество звёзд}</code>\n"
            "Пример: <code>/invoice 50</code>"
        )
        return

    try:
        stars = int(args[1])
        if stars <= 0:
            raise ValueError("Количество звёзд должно быть больше 0")
    except ValueError as e:
        await message.answer(f"❌ Неверное количество звёзд: {e}")
        return

    await message.answer_invoice(
        title="Пополнение звёзд",
        description=f"Оплата {stars} ⭐️ в бота",
        prices=[LabeledPrice(label="Звёзды", amount=stars)],
        payload=f"invoice_{stars}_{message.from_user.id}",
        currency="XTR",
        provider_token="", # Для звезд провайдер токен не нужен
        start_parameter="invoice"
    )

# --- ПОДТВЕРЖДЕНИЕ ПЛАТЕЖА ---
@dp.pre_checkout_query()
async def process_pre_checkout(q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(q.id, ok=True)

# --- ОБРАБОТКА УСПЕШНОЙ ОПЛАТЫ ---
@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    payment = message.successful_payment
    charge_id = payment.telegram_payment_charge_id

    await message.answer(
        f"✅ <b>Оплата прошла успешно!</b>\n"
        f"Списано: <b>{payment.total_amount} ⭐️</b>\n"
        f"ID транзакции: <code>{charge_id}</code>"
    )

# --- КОМАНДА ВОЗВРАТА (REFUND) ---
@dp.message(Command("refund"))
async def refund_command(message: Message):
    """
    /refund {ID_транзакции}
    """
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Используйте: /refund <ID_транзакции>")
        return
    try:
        await bot.refund_star_payment(
            user_id=message.from_user.id, 
            telegram_payment_charge_id=args[1]
        )
        await message.answer("✅ Средства возвращены!")
    except Exception as e:
        await message.answer(f"❌ Ошибка возврата: {e}")

# --- ЗАПУСК БОТА ---
async def main():
    # Удаляем вебхуки и запускаем поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")