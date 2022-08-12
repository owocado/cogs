from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from random import random
from typing import List, Optional

import aiohttp
from discord import Colour
from html import unescape
from textwrap import shorten

from .formatters import HANDLE, format_anime_status, format_date, format_manga_status


@dataclass
class CoverImage:
    large: str = ""
    color: str = ""


@dataclass
class DateModel:
    year: int = 0
    month: int = 0
    day: int = 0

    def __eq__(self, other: object) -> bool:
        return self.day == other.day and self.month == other.month and self.year == other.year

    def __str__(self) -> str:
        if not self.day:
            if self.year:
                return str(self.year)
            return "TBD?"
        return format_date(self.day, self.month, self.year)


@dataclass
class ExternalSite:
    site: str
    url: str

    def __str__(self) -> str:
        return f"[{self.site}]({self.url})"


@dataclass
class NextEpisodeInfo:
    episode: int
    timeUntilAiring: int
    airingAt: int


@dataclass
class Title:
    romaji: str = ""
    english: str = ""

    def __str__(self) -> str:
        return self.romaji or self.english or "Title Missing"


@dataclass
class Trailer:
    id: str
    site: str


@dataclass
class MediaData:
    id: int
    idMal: Optional[int]
    title: Title
    coverImage: CoverImage
    description: str
    bannerImage: str
    format: Optional[str]
    status: Optional[str]
    type: str
    meanScore: float
    startDate: DateModel
    endDate: DateModel
    source: Optional[str]
    studios: str
    siteUrl: Optional[str]
    isAdult: Optional[bool]
    duration: Optional[int]
    episodes: Optional[int]
    chapters: Optional[int]
    volumes: Optional[int]
    trailer: Optional[Trailer]
    nextAiringEpisode: Optional[NextEpisodeInfo]
    synonyms: List[str] = field(default_factory=list)
    genres: List[str] = field(default_factory=list)
    externalLinks: List[ExternalSite] = field(default_factory=list)

    @property
    def external_links(self) -> str:
        return " • ".join(f"[{x.site}]({x.url})" for x in self.externalLinks)

    @property
    def media_description(self) -> str:
        if not self.description:
            return ""

        return shorten(HANDLE.handle(unescape(self.description)), 400, placeholder="…")

    @property
    def media_end_date(self) -> str:
        return str(self.endDate)

    @property
    def media_start_date(self) -> str:
        return str(self.startDate)

    @property
    def media_status(self) -> str:
        if self.type == 'ANIME':
            status = format_anime_status(str(self.status))
        elif self.type == 'MANGA':
            status = format_manga_status(str(self.status))
        else:
            status = "Unknown"

        return f"Status: {status}"

    @property
    def media_source(self) -> str:
        if not self.source:
            return "Unknown"
        return self.source.replace('_', ' ').title()

    @property
    def preview_image(self) -> str:
        return f"https://img.anili.st/media/{self.id}"

    @property
    def prominent_colour(self) -> Colour:
        if self.coverImage.color:
            return Colour(int(self.coverImage.color[1:], 16))
        return Colour.from_hsv(random(), 0.5, 1.0)

    @property
    def release_mode(self) -> str:
        return f"Air date:" if self.type == "ANIME" else f"Publish date:"

    @classmethod
    def from_data(cls, data: dict) -> MediaData:
        studios = data.pop("studios", {}).get("nodes", [])
        trailer = data.pop("trailer", {})
        next_ep = data.pop("nextAiringEpisode", {})
        return cls(
            title=Title(**data.pop("title", {})),
            coverImage=CoverImage(**data.pop("coverImage", {})),
            startDate=DateModel(**data.pop("startDate", {})),
            endDate=DateModel(**data.pop("endDate", {})),
            studios=", ".join(studio["name"] for studio in studios) if studios else "",
            synonyms=data.pop("synonyms", []),
            genres=data.pop("genres", []),
            trailer=Trailer(**trailer) if trailer else None,
            externalLinks=[ExternalSite(**site) for site in data.pop("externalLinks", [])],
            nextAiringEpisode=NextEpisodeInfo(**next_ep) if next_ep else None,
            **data
        )

    @classmethod
    async def request(
        cls, session: aiohttp.ClientSession, query: str, **kwargs
    ) -> str | List[MediaData]:
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

        all_items = result.get("data", {}).get("Page", {}).get("media", [])
        if not all_items:
            return f"https://http.cat/404.jpg"

        return [cls.from_data(item) for item in all_items]
