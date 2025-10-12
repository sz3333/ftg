# ©️ Лид и Мочи, 2025
# 🐾 Hikka: форс-присоединение по инвайт-ссылке с проверкой
# Команда: .joing <ссылка>

from .. import loader, utils
from telethon import functions
from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import FloodWaitError, UserAlreadyParticipantError
import re, asyncio

@loader.tds
class JoinGroupForce(loader.Module):
    """🐾 Присоединяется к приватным/публичным группам (с raw-фолбэком)"""
    strings = {"name": "JoinGroupForce"}

    async def joingcmd(self, message):
        """<ссылка> — присоединиться к группе по ссылке"""
        link = utils.get_args_raw(message).strip()
        if not link:
            return await utils.answer(message, "😿 Укажи ссылку, ня~")

        # приватные инвайты имеют + или joinchat/
        m = re.search(r"(?:joinchat/|\+)([A-Za-z0-9_-]+)", link)
        try:
            if m:
                code = m.group(1)

                # инфо по инвайту (может вернуть ChatInvite или ChatInviteAlready)
                try:
                    info = await self.client(CheckChatInviteRequest(code))
                    title = getattr(getattr(info, "chat", None), "title", None) or getattr(info, "title", "неизвестная группа")
                except Exception:
                    title = "неизвестная группа"

                await utils.answer(message, f"Felix •|afk|:\n🐾 Пытаюсь войти через <b>ImportChatInviteRequest</b>...")

                try:
                    res = await self.client(ImportChatInviteRequest(code))
                    if getattr(res, "chats", None):
                        return await utils.answer(message, f"✅ Присоединился к <b>{title}</b>, нyaa~ 🐾")
                except UserAlreadyParticipantError:
                    return await utils.answer(message, "⚠️ Ты уже участник, мяу~")
                except FloodWaitError as fw:
                    return await utils.answer(message, f"⏳ Подожди {fw.seconds}s — FloodWait от Telegram 😿")

                # RAW fallback через invoke (без внутренних обёрток)
                await utils.answer(message, "⚙️ Стандартный метод не сработал, пробую raw join…")
                try:
                    res2 = await self.client.invoke(functions.messages.ImportChatInviteRequest(hash=code))
                    await asyncio.sleep(1.2)
                    if getattr(res2, "chats", None):
                        return await utils.answer(message, f"✅ Raw-join ок! Проверь список чатов: <b>{title}</b> 😽")
                    return await utils.answer(message, f"⚠️ Telegram не подтвердил вступление в <b>{title}</b> 😿")
                except UserAlreadyParticipantError:
                    return await utils.answer(message, "⚠️ Уже внутри (по данным RAW), мяу~")
                except FloodWaitError as fw:
                    return await utils.answer(message, f"⏳ FloodWait {fw.seconds}s на raw-вызове.")
                except Exception as e:
                    return await utils.answer(message, f"🚫 RAW ошибка: <code>{e}</code>")

            else:
                # публичные ссылки: t.me/<username>
                username = re.sub(r"^(https?://)?t\.me/|^@", "", link)
                await self.client(JoinChannelRequest(username))
                return await utils.answer(message, "✅ Присоединился к публичной группе, мурр~")

        except Exception as e:
            await utils.answer(message, f"🚫 Ошибка: <code>{e}</code>")