# Hikka module: DeepSeek Chat with async memory (Heroku-ready)
# by neko helper :3

from .. import loader, utils
import aiohttp

API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"

DEFAULT_SYSTEM_PROMPT = (
    "Ты милый, но умный ассистент. Говори кратко, по делу, без воды. "
    "Помни контекст диалога и помогай пользователю максимально эффективно."
)

@loader.tds
class DeepSeekMod(loader.Module):
    """DeepSeek API с памятью и системным промтом (async, Heroku-ready)"""

    strings = {"name": "DeepSeek"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "api_key",
                "",
                lambda: "DeepSeek API ключ",
                validator=loader.validators.Hidden()
            ),
            loader.ConfigValue(
                "model",
                DEFAULT_MODEL,
                lambda: "Модель DeepSeek"
            ),
            loader.ConfigValue(
                "system_prompt",
                DEFAULT_SYSTEM_PROMPT,
                lambda: "Системный промт"
            ),
        )

    async def client_ready(self, client, db):
        self.client = client
        self.db = db  # async Hikka DB

    async def _save_msg(self, user_id, role, content):
        # ключ вида "memory:{user_id}:{index}"
        mem = await self._get_memory(user_id)
        index = len(mem)
        key = f"memory:{user_id}:{index}"
        await self.db.set(key, f"{role}|{content}")

    async def _get_memory(self, user_id, limit=10):
        keys = await self.db.keys(f"memory:{user_id}:*")
        keys = sorted(keys)[-limit:]
        mem = []
        for k in keys:
            val = await self.db.get(k)
            if val:
                role, content = val.split("|", 1)
                mem.append({"role": role, "content": content})
        return mem

    async def _clear_memory(self, user_id):
        keys = await self.db.keys(f"memory:{user_id}:*")
        for k in keys:
            await self.db.delete(k)

    @loader.command()
    async def ds(self, message):
        """Общение с DeepSeek"""
        api_key = self.config["api_key"]
        if not api_key:
            await message.edit("❌ укажи API ключ в конфиге модуля")
            return

        user_text = utils.get_args_raw(message)
        if not user_text:
            await message.edit("❌ напиши текст")
            return

        uid = message.sender_id
        await self._save_msg(uid, "user", user_text)

        messages = [
            {"role": "system", "content": self.config["system_prompt"]},
            *await self._get_memory(uid),
        ]

        payload = {
            "model": self.config["model"],
            "messages": messages,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        await message.edit("⏳ думаю...")

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    await message.edit(f"❌ ошибка API: {resp.status}")
                    return
                data = await resp.json()

        reply = data["choices"][0]["message"]["content"]
        await self._save_msg(uid, "assistant", reply)

        await message.edit(reply)

    @loader.command()
    async def dsclear(self, message):
        """Очистить память диалога"""
        uid = message.sender_id
        await self._clear_memory(uid)
        await message.edit("🧹 память очищена")