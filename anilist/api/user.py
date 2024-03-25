from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import dacite
from arrow.api import get as arrow_get

from .base import BaseStats, CoverImage, NotFound, fetch_data

if TYPE_CHECKING:
    from aiohttp import ClientSession


@dataclass
class AnimeStats(BaseStats):
    minutesWatched: int
    episodesWatched: int


@dataclass
class MangaStats(BaseStats):
    chaptersRead: int
    volumesRead: int


@dataclass(slots=True)
class PreviousName:
    name: str
    createdAt: int = 0
    updatedAt: int = 0


@dataclass(slots=True)
class Statistics:
    anime: AnimeStats
    manga: MangaStats


@dataclass(slots=True)
class UserData:
    id: int
    name: str
    about: str | None
    donatorTier: int
    createdAt: int | None
    updatedAt: int | None
    avatar: CoverImage
    bannerImage: str | None
    siteUrl: str
    statistics: Statistics
    previousNames: list[PreviousName] = field(default_factory=list)

    @property
    def created_on(self) -> str:
        if not self.createdAt:
            return "many years"
        return arrow_get(self.createdAt).humanize()

    @property
    def opengraph_banner(self) -> str:
        return f"https://img.anili.st/user/{self.id}"

    @property
    def previous_username(self) -> str:
        return self.previousNames[0].name if self.previousNames else ""

    @classmethod
    async def request(
        cls, session: ClientSession, query: str, **kwargs: Any,
    ) -> NotFound | list[UserData]:
        result = await fetch_data(session, query, **kwargs)
        if result.get("message"):
            return NotFound(**result)

        all_items = result.get("data", {}).get("Page", {}).get("users", [])
        return (
            [dacite.from_dict(data=item, data_class=cls) for item in all_items]
            if all_items
            else NotFound("Sad trombone. No results!")
        )
