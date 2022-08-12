from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional, Sequence

import aiohttp

from .formatters import format_description


@dataclass
class DateModel:
    year: Optional[int]
    month: Optional[int]
    day: Optional[int]


@dataclass
class Image:
    large: Optional[str]


@dataclass
class Name:
    full: str
    native: str
    alternative: Sequence[str] = field(default_factory=list)

    def __str__(self) -> str:
        if self.full == self.native:
            return self.full
        return f"{self.full} ({self.native})" if self.native else self.full


@dataclass
class MediaNode:
    siteUrl: str
    type: str
    title: MediaTitle

    @classmethod
    def from_data(cls, data: dict) -> MediaNode:
        return cls(title=MediaTitle(**data.pop("title", {})), **data)


@dataclass
class MediaTitle:
    english: Optional[str]
    romaji: Optional[str]

    def __str__(self) -> str:
        return self.english or self.romaji or "Title Unknown"


@dataclass
class CharacterData:
    name: Name
    image: Image
    description: Optional[str]
    gender: str
    dateOfBirth: DateModel
    age: Optional[str]
    siteUrl: str
    media_nodes: Sequence[MediaNode] = field(default_factory=list)

    @property
    def character_summary(self) -> str:
        return format_description(self.description, 1800) if self.description else ""

    @property
    def appeared_in(self) -> str:
        return "\n".join(
            f"[{media.title}]({media.siteUrl}) ({media.type.title()})"
            for media in self.media_nodes
        )

    @classmethod
    def from_data(cls, data: dict) -> CharacterData:
        nodes = data.pop("media", {}).get("nodes", [])
        return cls(
            name=Name(**data.pop("name", {})),
            image=Image(**data.pop("image", {})),
            dateOfBirth=DateModel(**data.pop("dateOfBirth", {})),
            media_nodes=[MediaNode.from_data(node) for node in nodes],
            **data
        )

    @classmethod
    async def request(
        cls, session: aiohttp.ClientSession, query: str, **kwargs
    ) -> str | Sequence[CharacterData]:
        try:
            async with session.post(
                "https://graphql.anilist.co", json={"query": query, "variables": kwargs}
            ) as resp:
                if resp.status != 200:
                    return f"https://http.cat/{resp.status}.jpg"
                result: dict = await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            return f"https://http.cat/408.jpg"

        if err := result.get("errors"):
            return f"{err[0]['message']} (Status: {err[0]['status']})"

        all_items = result.get("data", {}).get("Page", {}).get("characters", [])
        if not all_items:
            return f"https://http.cat/404.jpg"

        return [cls.from_data(item) for item in all_items]
