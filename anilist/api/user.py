from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

from .base import BaseStats, CoverImage, fetch_data


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
            anime=AnimeStats(**data.pop("anime", {})), manga=MangaStats(**data.pop("manga", {}))
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
            **data,
        )

    @classmethod
    async def request(cls, session, query: str, **kwargs) -> str | Sequence[UserData]:
        result = await fetch_data(session, query, **kwargs)
        if type(result) is str:
            return result

        all_items = result.get("data", {}).get("Page", {}).get("users", [])
        if not all_items:
            return f"Sad trombone. No results!"

        return [cls.from_data(item) for item in all_items]
