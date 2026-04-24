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

# Универсальный метод для отправки Star Gift
class SendGift(TelegramMethod[bool]):
    __returning__ = bool
    __api_method__ = "sendGift"

    gift_id: str
    user_id: Optional[int] = None  # Для юзеров
    chat_id: Optional[int] = None  # Для каналов
    text: Optional[str] = None

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


@dp.message(Command("gift"))
async def gift_command(message: Message):
    """
    /gift GIFT_ID USER_ID
    Пример: /gift 5922558454332916696 123456789
    """
    args = message.text.split()
    if len(args) < 3:
        await message.answer(
            "Использование: <code>/gift GIFT_ID USER_ID</code>\n"
            "Пример: <code>/gift 5922558454332916696 123456789</code>"
        )
        return

    gift_id = args[1]

    try:
        target_id = int(args[2])
    except ValueError:
        await message.answer("❌ USER_ID должен быть числом. @username не поддерживается Telegram API.")
        return

    try:
        if target_id > 0:
            await bot(SendGift(user_id=target_id, gift_id=gift_id))
        else:
            await bot(SendGift(chat_id=target_id, gift_id=gift_id))

        await message.answer(f"✅ <b>Подарок успешно отправлен</b> пользователю <code>{target_id}</code>!")

    except Exception as e:
        logging.error(f"Ошибка /gift: {e}")
        await message.answer(f"❌ <b>Ошибка:</b> {e}")


@dp.message(Command("invoice"))
async def invoice_command(message: Message):
    """
    /invoice {количество звезд}
    Пример: /invoice 50
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
        provider_token="",
        start_parameter="invoice"
    )


@dp.pre_checkout_query()
async def process_pre_checkout(q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(q.id, ok=True)


@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    payment = message.successful_payment
    charge_id = payment.telegram_payment_charge_id

    await message.answer(
        f"✅ <b>Оплата прошла успешно!</b>\n"
        f"Списано: <b>{payment.total_amount} ⭐️</b>\n"
        f"ID транзакции: <code>{charge_id}</code>"
    )


@dp.message(Command("refund"))
async def refund_command(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Используйте: /refund <ID_транзакции>")
        return
    try:
        await bot.refund_star_payment(user_id=message.from_user.id, telegram_payment_charge_id=args[1])
        await message.answer("✅ Средства возвращены!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
