from __future__ import annotations

from dataclasses import dataclass, field
from random import random
from typing import Optional, Sequence

from discord import Colour
from html import unescape
from textwrap import shorten

from .base import CoverImage, DateModel, ExternalSite, MediaTitle, MediaTrailer, fetch_data
from .formatters import HANDLE, format_anime_status, format_manga_status


@dataclass
class NextEpisodeInfo:
    episode: int
    airingAt: int


@dataclass
class MediaData:
    id: int
    idMal: Optional[int]
    title: MediaTitle
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
    trailer: Optional[MediaTrailer]
    nextAiringEpisode: Optional[NextEpisodeInfo]
    synonyms: Sequence[str] = field(default_factory=list)
    genres: Sequence[str] = field(default_factory=list)
    externalLinks: Sequence[ExternalSite] = field(default_factory=list)

    @property
    def external_links(self) -> str:
        sites = " • ".join(map(str, self.externalLinks))
        if self.trailer and self.trailer.site == "youtube":
            sites += f" • [YouTube Trailer](https://youtu.be/{self.trailer.id})"
        if self.idMal:
            sites += f" • [MyAnimeList](https://myanimelist.net/anime/{self.idMal})"
        return sites

    @property
    def humanize_duration(self) -> str:
        if not self.duration:
            return ""
        if self.duration < 60:
            return f"{self.duration} minutes"
        return f"{self.duration // 60}h {self.duration - 60}m."

    @property
    def media_description(self) -> str:
        if not self.description:
            return ""
        return shorten(HANDLE.handle(unescape(self.description)), 400, placeholder="…")

    @property
    def media_status(self) -> str:
        if self.type == "ANIME":
            status = format_anime_status(str(self.status))
        elif self.type == "MANGA":
            status = format_manga_status(str(self.status))
        else:
            status = "Unknown"
        return f"Status: {status}"

    @property
    def media_source(self) -> str:
        if not self.source:
            return "Unknown"
        return self.source.replace("_", " ").title()

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
            title=MediaTitle(**data.pop("title", {})),
            coverImage=CoverImage(**data.pop("coverImage", {})),
            startDate=DateModel(**data.pop("startDate", {})),
            endDate=DateModel(**data.pop("endDate", {})),
            studios=", ".join(studio["name"] for studio in studios) if studios else "",
            synonyms=data.pop("synonyms", []),
            genres=data.pop("genres", []),
            trailer=MediaTrailer(**trailer) if trailer else None,
            externalLinks=[ExternalSite(**site) for site in data.pop("externalLinks", [])],
            nextAiringEpisode=NextEpisodeInfo(**next_ep) if next_ep else None,
            **data,
        )

    @classmethod
    async def request(cls, session, query: str, **kwargs) -> str | Sequence[MediaData]:
        result = await fetch_data(session, query, **kwargs)
        if type(result) is str:
            return result

        all_items = result.get("data", {}).get("Page", {}).get("media", [])
        if not all_items:
            return f"Sad trombone. No results!"

        return [cls.from_data(item) for item in all_items]
