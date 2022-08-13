from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional, Sequence

import aiohttp
from .formatters import format_anime_status


@dataclass
class MediaNode:
    episodes: int
    format: str
    siteUrl: str
    status: str
    title: Title

    def __str__(self) -> str:
        return f"**[{self.title}]({self.siteUrl})**"

    @property
    def episodes_count(self) -> str:
        if self.format == "MOVIE":
            return ""
        if not self.episodes:
            return f"  »  `{format_anime_status(self.status)}`"

        return f"  »  **{self.episodes}** {'episodes' if self.episodes > 1 else 'episode'}"

    @classmethod
    def from_data(cls, data: dict) -> MediaNode:
        return cls(title=Title(**data.pop("title", {})), **data)


@dataclass
class Title:
    english: Optional[str]
    romaji: Optional[str]

    def __str__(self) -> str:
        return self.english or self.romaji or "Title ???"


@dataclass
class StudioData:
    name: str
    favourites: int
    isAnimationStudio: bool
    siteUrl: str
    media_nodes: Sequence[MediaNode] = field(default_factory=list)

    @classmethod
    def from_data(cls, data: dict) -> StudioData:
        nodes = data.pop("media", {}).get("nodes", [])
        return cls(media_nodes=[MediaNode.from_data(node) for node in nodes], **data)

    @classmethod
    async def request(
        cls, session: aiohttp.ClientSession, query: str, **kwargs
    ) -> str | Sequence[StudioData]:
        try:
            async with session.post(
                "https://graphql.anilist.co", json={"query": query, "variables": kwargs}
            ) as resp:
                if resp.status != 200:
                    return f"https://http.cat/{resp.status}.jpg"
                result: dict = await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return f"https://http.cat/408.jpg"

        if err := result.get("errors"):
            return f"{err[0]['message']} (Status: {err[0]['status']})"

        all_studios = result.get("data", {}).get("Page", {}).get("studios", [])
        if not all_studios:
            return f"https://http.cat/404.jpg"

        return [cls.from_data(item) for item in all_studios]
