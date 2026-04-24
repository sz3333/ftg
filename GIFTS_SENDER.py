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

# Токен бота
BOT_TOKEN = "7604253117:AAFjrfCahWV0taFPHdAreyEo3zBiNHl_sEI"

logging.basicConfig(level=logging.INFO)

# Улучшенный метод для отправки Star Gift
class SendGift(TelegramMethod[bool]):
    __returning__ = bool
    __api_method__ = "sendGift"

    gift_id: str
    user_id: Optional[int] = None
    chat_id: Optional[int] = None
    text: Optional[str] = None
    text_parse_mode: Optional[str] = "HTML" # Позволяет использовать <b></b> и т.д.
    is_anonymous: Optional[bool] = None     # Можно скрыть отправителя

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(Command("gift"))
async def gift_command(message: Message):
    """
    Использование: /gift {GIFT_ID} {USER_ID} {Ваш текст подписи}
    Пример: /gift 5922558454332916696 123456789 С днем рождения, бро!
    """
    # maxsplit=3 позволяет захватить весь текст после ID пользователя в один аргумент
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

    # Если текст есть, берем его, если нет — оставляем None
    gift_message = args[3] if len(args) > 3 else None
    
    # Проверка длины текста (лимит Telegram ~128 символов для подарков)
    if gift_message and len(gift_message) > 128:
        await message.answer("❌ <b>Ошибка:</b> Текст слишком длинный (макс. 128 символов).")
        return

    try:
        # Формируем запрос
        payload = {
            "gift_id": gift_id,
            "text": gift_message,
            "text_parse_mode": "HTML"
        }
        
        if target_id > 0:
            payload["user_id"] = target_id
        else:
            payload["chat_id"] = target_id

        await bot(SendGift(**payload))

        success_msg = f"✅ <b>Подарок успешно отправлен!</b>\n👤 Получатель: <code>{target_id}</code>"
        if gift_message:
            success_msg += f"\n📝 Текст: <i>{gift_message}</i>"
            
        await message.answer(success_msg)

    except Exception as e:
        logging.error(f"Ошибка при отправке подарка: {e}")
        await message.answer(f"❌ <b>Ошибка API:</b>\n<code>{e}</code>")

# --- Остальные функции (invoice, refund) остаются без изменений ---
@dp.message(Command("invoice"))
async def invoice_command(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: <code>/invoice {звезды}</code>")
        return
    try:
        stars = int(args[1])
        await message.answer_invoice(
            title="Пополнение звёзд",
            description=f"Оплата {stars} ⭐️",
            prices=[LabeledPrice(label="Звёзды", amount=stars)],
            payload=f"invoice_{stars}_{message.from_user.id}",
            currency="XTR",
            provider_token="",
            start_parameter="invoice"
        )
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.pre_checkout_query()
async def process_pre_checkout(q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(q.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    await message.answer(f"✅ Оплата на {message.successful_payment.total_amount} ⭐️ принята!")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())