"""
Неко-бот для экспериментов с Telegram Stars и подарками 🐾
Основан на Pyrogram (pip install pyrogram tgcrypto)
"""

import time
import logging
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    LabeledPrice,
    PreCheckoutQuery,
)
from pyrogram.errors import (
    RPCError,
    UserNotParticipant,
    PeerIdInvalid,
    StarGiftNotAvailable,
    PaymentUnsupported,
)

# ─── Конфигурация ──────────────────────────────────────────────
API_ID    = 0               # Вставь свой api_id с my.telegram.org
API_HASH  = "YOUR_API_HASH" # Вставь свой api_hash
BOT_TOKEN = "YOUR_TOKEN"    # Токен от @BotFather
OWNER_ID  = 123456789       # Вставь свой Telegram user_id
# ───────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger(__name__)

app = Client(
    name="gift_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)


# ─── Хелперы ───────────────────────────────────────────────────

def owner_only(func):
    """Декоратор: пропускает только OWNER_ID, остальным — ня~."""
    async def wrapper(client: Client, message: Message):
        if message.from_user and message.from_user.id != OWNER_ID:
            await message.reply("Не для тебя, ня~ 🙅‍♀️")
            return
        return await func(client, message)
    return wrapper


async def resolve_user(client: Client, target: str) -> int:
    """Разрешает @username или строку с числом в user_id (int)."""
    if target.lstrip("-").isdigit():
        return int(target)
    # username → id через get_users
    user = await client.get_users(target.lstrip("@"))
    return user.id


# ─── /start ────────────────────────────────────────────────────

@app.on_message(filters.command("start") & filters.private)
async def cmd_start(client: Client, message: Message):
    await message.reply(
        "Мяу, я нека-бот для Stars и подарков 🐾✨\n\n"
        "Команды:\n"
        "• /invoice `<кол-во>` — выставить счёт на Stars\n"
        "• /sendgift `<user_id/@username> <gift_id>` — отправить подарок\n"
        "• /gifts — список доступных подарков\n\n"
        "_Чувствительные команды — только для овнера._",
        parse_mode="markdown",
    )


# ─── /invoice ──────────────────────────────────────────────────

@app.on_message(filters.command("invoice") & filters.private)
@owner_only
async def cmd_invoice(client: Client, message: Message):
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.reply("Использование: `/invoice <количество>`\nПример: `/invoice 300`")
        return

    amount = int(parts[1])
    if amount < 1:
        await message.reply("❌ Количество должно быть ≥ 1")
        return

    payload = f"topup_{OWNER_ID}_{time.time()}"

    try:
        await client.send_invoice(
            chat_id=message.chat.id,
            title="Пополнение Stars для подарков",
            description="Кидаю звёздочки себе, чтобы дарить подарки :3",
            payload=payload,
            currency="XTR",          # Telegram Stars
            prices=[LabeledPrice(label="Stars", amount=amount)],
            provider_token="",        # Пустая строка для XTR — обязательно!
        )
        log.info("Invoice отправлен: %d XTR, payload=%s", amount, payload)

    except RPCError as e:
        log.error("send_invoice error: %s", e)
        await message.reply(f"❌ Ошибка при создании invoice:\n`{e}`")


# ─── Pre-checkout (обязательно подтвердить) ────────────────────

@app.on_pre_checkout_query()
async def pre_checkout_handler(client: Client, query: PreCheckoutQuery):
    # Telegram требует ответить в течение 10 секунд
    await query.answer(ok=True)


# ─── Successful payment ────────────────────────────────────────

@app.on_message(filters.successful_payment & filters.private)
async def successful_payment_handler(client: Client, message: Message):
    payment = message.successful_payment
    amount  = payment.total_amount  # В XTR это целое число звёзд
    payload = payment.invoice_payload

    log.info("Оплата получена: %d XTR, payload=%s", amount, payload)
    await message.reply(f"✅ Получено {amount} Stars на баланс! 🌟")


# ─── /gifts ────────────────────────────────────────────────────

@app.on_message(filters.command("gifts") & filters.private)
async def cmd_gifts(client: Client, message: Message):
    try:
        gifts_result = await client.get_available_gifts()
        gifts = gifts_result.gifts  # список StarGift

        if not gifts:
            await message.reply("😿 Доступных подарков пока нет.")
            return

        lines = ["🎁 **Доступные подарки:**\n"]
        for g in gifts:
            sticker_emoji = getattr(g.sticker, "emoji", "🎀") or "🎀"
            total    = g.total_count
            sold_out = g.remaining_count == 0 if g.remaining_count is not None else False
            status   = "❌ закончился" if sold_out else (
                f"{g.remaining_count} осталось" if g.remaining_count is not None else "∞"
            )
            lines.append(
                f"{sticker_emoji} `{g.id}`\n"
                f"   💫 {g.star_count} Stars | {status}"
            )

        await message.reply("\n".join(lines), parse_mode="markdown")

    except RPCError as e:
        log.error("get_available_gifts error: %s", e)
        await message.reply(f"❌ Не удалось получить список подарков:\n`{e}`")


# ─── /sendgift ─────────────────────────────────────────────────

@app.on_message(filters.command("sendgift") & filters.private)
@owner_only
async def cmd_sendgift(client: Client, message: Message):
    parts = message.text.split()
    if len(parts) != 3:
        await message.reply(
            "Использование: `/sendgift <user_id/@username> <gift_id>`\n"
            "Пример: `/sendgift @durov 123456789`"
        )
        return

    target_raw = parts[1]
    gift_id    = parts[2]

    # Разрешаем user_id
    try:
        target_user_id = await resolve_user(client, target_raw)
    except (PeerIdInvalid, UserNotParticipant, RPCError) as e:
        await message.reply(f"❌ Не удалось найти пользователя `{target_raw}`:\n`{e}`")
        return

    # Отправляем подарок
    try:
        await client.send_gift(
            user_id=target_user_id,
            gift_id=gift_id,
            pay_for_upgrade=True,   # Бот сам оплачивает возможный апгрейд
            text="Держи подарочек от меня, мяу~ 🐾✨",
        )
        log.info("Подарок %s отправлен пользователю %d", gift_id, target_user_id)
        await message.reply(
            f"🎁 Подарок успешно отправлен!\n"
            f"👤 Получатель: `{target_user_id}`\n"
            f"🆔 Gift ID: `{gift_id}`"
        )

    except StarGiftNotAvailable:
        await message.reply("❌ Этот подарок закончился или недоступен 😿")

    except PaymentUnsupported:
        await message.reply("❌ Недостаточно Stars на балансе бота. Пополни через /invoice!")

    except RPCError as e:
        error_msg = str(e)
        # Человекочитаемые сообщения для частых ошибок
        friendly: dict[str, str] = {
            "STARGIFT_USAGE_LIMITED":   "Достигнут лимит отправок этого подарка.",
            "BALANCE_TOO_LOW":          "Недостаточно Stars на балансе.",
            "GIFT_SEND_FORBIDDEN":      "Пользователь запретил получение подарков.",
            "USER_NOT_MUTUAL_CONTACT":  "Нельзя отправить — пользователь не в контактах.",
        }
        for key, hint in friendly.items():
            if key in error_msg:
                await message.reply(f"❌ {hint}")
                return

        log.error("send_gift error: %s", e)
        await message.reply(f"❌ Ошибка при отправке подарка:\n`{e}`")


# ─── Запуск ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🐾 Нека-бот запускается...")
    app.run()
