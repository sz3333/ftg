#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://static.dan.tatar/catboy_icon.png
# meta banner: https://mods.hikariatama.ru/badges/catboy.jpg
# meta developer: @hikarimods
# scope: inline
# scope: hikka_only
# scope: hikka_min 1.3.0

import requests
import random
from telethon.tl.types import Message

from .. import loader, utils
from ..inline.types import InlineQuery


async def photo() -> str:
    # e926 API, фильтр: feline male -female -femboy + только safe
    params = {
        "tags": "feline male -female -femboy rating:safe",
        "limit": 100,
        "page": random.randint(1, 50),  # рандом по страницам
    }
    data = (
        await utils.run_sync(
            requests.get,
            "https://e926.net/posts.json",
            params=params,
            headers={"User-Agent": "HikkaCatboyMod/1.0"},
        )
    ).json()

    posts = data.get("posts", [])
    if not posts:
        return "https://static.dan.tatar/catboy_icon.png"

    post = random.choice(posts)
    return post["file"]["url"]


@loader.tds
class CatboyMod(loader.Module):
    """Sends cute anime boy pictures"""

    strings = {"name": "Catboy"}
    strings_ru = {"_cls_doc": "Отправляет фотографии милых аниме мальчиков"}
    strings_de = {"_cls_doc": "Sendet Anime-Katzenjungen-Bilder"}
    strings_uz = {"_cls_doc": "Anime o'g'irlar rasmlarini jo'natadi"}
    strings_hi = {"_cls_doc": "एक एनीमे कैटबॉय तस्वीर भेजें"}
    strings_tr = {"_cls_doc": "Anime kedi erkek resmi gönderir"}

    @loader.command(
        ru_doc="Показать кошкомальчика",
        de_doc="Zeigt ein Anime-Katzenjungen-Bild",
        uz_doc="Anime kishi rasmlarini ko'rsatadi",
        hi_doc="एक एनीमे कैटबॉय तस्वीर दिखाएं",
        tr_doc="Anime kedi erkek resmi gönderir",
    )
    async def catboycmd(self, message: Message):
        """Send catboy picture"""
        await self.inline.gallery(
            caption=lambda: f"<i>{utils.ascii_face()}</i>",
            message=message,
            next_handler=photo,
            preload=5,
        )

    @loader.inline_handler(
        ru_doc="Показать кошкомальчиков",
        de_doc="Zeigt Anime-Katzenjungen-Bilder",
        uz_doc="Anime kishi rasmlarini ko'rsatadi",
        hi_doc="एनीमे कैटबॉय तस्वीरें दिखाएं",
        tr_doc="Anime kedi erkek resimleri gönderir",
    )
    async def catboy(self, query: InlineQuery):
        """Send Catboys"""
        await self.inline.query_gallery(
            query,
            [
                {
                    "title": "👩‍🎤 Catboy",
                    "description": "Send catboy photo",
                    "next_handler": photo,
                    "thumb_handler": photo,
                    "caption": lambda: f"<i>Enjoy! {utils.ascii_face()}</i>",
                }
            ],
        )