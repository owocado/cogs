from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional, Sequence

import aiohttp

from .media import CoverImage


@dataclass
class BaseStats:
    count: int
    meanScore: float


@dataclass
class AnimeStats(BaseStats):
    minutesWatched: int
    episodesWatched: int


@dataclass
class MangaStats(BaseStats):
    chaptersRead: int
    volumesRead: int


@dataclass
class PreviousName:
    name: str
    createdAt: int = 0
    updatedAt: int = 0


@dataclass
class Statistics:
    anime: AnimeStats
    manga: MangaStats

    @classmethod
    def from_data(cls, data: dict) -> Statistics:
        return cls(
            anime=AnimeStats(**data.pop("anime", {})),
            manga=MangaStats(**data.pop("manga", {}))
        )


@dataclass
class UserData:
    id: int
    name: str
    about: Optional[str]
    avatar: CoverImage
    bannerImage: Optional[str]
    siteUrl: str
    statistics: Statistics
    previousNames: Sequence[PreviousName] = field(default_factory=list)

    @property
    def opengraph_banner(self) -> str:
        return f"https://img.anili.st/user/{self.id}"

    @property
    def previous_username(self) -> str:
        if not self.previousNames:
            return ""

        return self.previousNames[0].name

    @classmethod
    def from_data(cls, data: dict) -> UserData:
        previous_names = data.pop("previousNames", [])
        return cls(
            avatar=CoverImage(**data.pop("avatar", {})),
            statistics=Statistics.from_data(data.pop("statistics", {})),
            previousNames=[PreviousName(**pn) for pn in previous_names],
            **data
        )

    @classmethod
    async def request(
        cls, session: aiohttp.ClientSession, query: str, **kwargs
    ) -> str | Sequence[UserData]:
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

        all_items = result.get("data", {}).get("Page", {}).get("users", [])
        if not all_items:
            return f"https://http.cat/404.jpg"

        return [cls.from_data(item) for item in all_items]
