from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Sequence

import aiohttp


@dataclass
class BanList:
    ban_tcg: str = ""
    ban_ocg: str = ""
    ban_goat: str = ""


@dataclass
class CardImage:
    image_url: str
    image_url_small: str
    id: Optional[int] = None


@dataclass
class CardPrice:
    cardmarket_price: str = ""
    tcgplayer_price: str = ""
    ebay_price: str = ""
    amazon_price: str = ""
    coolstuffinc_price: str = ""


@dataclass
class CardSet:
    set_name: str = ""
    set_code: str = ""
    set_rarity: str = ""
    set_rarity_code: str = ""
    set_price: str = ""


@dataclass
class NotFound:
    error: str
    http_code: int
    message: str = ""

    def __str__(self) -> str:
        return self.error or f"https://http.cat/{self.http_code}.jpg"


@dataclass
class YuGiOhData:
    id: int
    name: str
    type: str
    desc: str
    attack: int
    defense: int
    level: int
    race: str
    archetype: Optional[str] = None
    attribute: Optional[str] = None
    scale: Optional[int] = None
    linkval: Optional[int] = None
    linkmarkers: Sequence[str] = field(default_factory=list)
    banlist_info: Optional[BanList] = field(default_factory=dict)
    card_images: Sequence[CardImage] = field(default_factory=list)
    card_prices: Sequence[CardPrice] = field(default_factory=list)
    card_sets: Sequence[CardSet] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> YuGiOhData:
        attack = data.pop("atk", 0)
        defense = data.pop("def", 0)
        level = data.pop("level", 0)
        banlist_info = BanList(**data.pop("banlist_info", {}))
        card_images = [CardImage(**img) for img in data.pop("card_images", [])]
        card_prices = [CardPrice(**price) for price in data.pop("card_prices", [])]
        card_sets = [CardSet(**set_) for set_ in data.pop("card_sets", [])]
        return cls(
            attack=attack,
            defense=defense,
            level=level,
            banlist_info=banlist_info,
            card_images=card_images,
            card_prices=card_prices,
            card_sets=card_sets,
            **data
        )

    @classmethod
    async def request(
        cls, session: aiohttp.ClientSession, url: str
    ) -> NotFound | Sequence[YuGiOhData] | YuGiOhData:
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    if 'json' in resp.headers.get('Content-Type', ''):
                        data = await resp.json()
                        if data.get('error'):
                            return NotFound(http_code=resp.status, **data)
                    return NotFound("", http_code=resp.status)

                ygo_data = await resp.json()
        except asyncio.TimeoutError:
            return NotFound("Error: 408! Operation timed out.", http_code=408)

        if not ygo_data.get("data"):
            return cls.from_dict(ygo_data)
        return [cls.from_dict(card) for card in ygo_data['data']]
