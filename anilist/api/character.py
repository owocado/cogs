from __future__ import annotations

from dataclasses import dataclass, field
from html import unescape
from typing import TYPE_CHECKING, Any, Literal

import dacite

from .base import CoverImage, DateModel, MediaTitle, NotFound, fetch_data
from .formatters import format_description

if TYPE_CHECKING:
    from aiohttp import ClientSession


@dataclass(slots=True)
class Name:
    full: str | None
    native: str | None
    userPreferred: str | None
    alternative: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        if self.userPreferred:
            return self.userPreferred
        # This is a very rare possibility, so future-proof it in case
        if not self.full and not self.native and not self.alternative:
            return "NAME MISSING ???"
        # https://anilist.co/character/135069 - both full and native name can be null
        if not self.full and not self.native and self.alternative:
            return " • ".join(self.alternative)
        if self.full and self.native and self.full == self.native:
            return self.full

        return f"{self.full} ({self.native})" if self.native else (self.full or "")


@dataclass(slots=True)
class PageInfo:
    total: int
    perPage: int
    currentPage: int
    lastPage: int | None
    hasNextPage: bool


@dataclass(slots=True)
class MiniMediaNode:
    type: Literal["ANIME", "MANGA"]
    isAdult: bool
    title: MediaTitle
    siteUrl: str
    startDate: DateModel


@dataclass(slots=True)
class Edge:
    characterRole: Literal["MAIN", "SUPPORTING", "BACKGROUND"]
    node: MiniMediaNode

    @property
    def year(self):
        return self.node.startDate.year

    @property
    def site_url(self):
        return self.node.siteUrl

    @property
    def type(self):
        return self.node.type

    @property
    def title(self):
        return self.node.title


@dataclass(slots=True)
class MediaMetadata:
    pageInfo: PageInfo
    edges: list[Edge] = field(default_factory=list)


@dataclass(slots=True)
class CharacterData:
    name: Name
    image: CoverImage
    description: str | None
    gender: str | None
    dateOfBirth: DateModel
    age: str | None
    siteUrl: str
    media: MediaMetadata | None

    @property
    def character_summary(self) -> str:
        if not self.description:
            return ""
        return format_description(unescape(self.description), 500)

    @property
    def appeared_in(self) -> str | None:
        if not self.media:
            return None
        return "\n".join(
            f"[{media.title}]({media.site_url}) (`{media.type.lower()}`) ~ {media.year or 'Upcoming'}"
            for media in self.media.edges[:10]
        )

    @classmethod
    async def request(
        cls, session: ClientSession, query: str, **kwargs: Any
    ) -> NotFound | list[CharacterData]:
        result = await fetch_data(session, query, **kwargs)
        if result.get("message"):
            return NotFound(**result)

        all_items = result.get("data", {}).get("Page", {}).get("characters", [])
        return (
            [dacite.from_dict(data=item, data_class=cls) for item in all_items]
            if all_items
            else NotFound("Sad trombone. No results!")
        )

