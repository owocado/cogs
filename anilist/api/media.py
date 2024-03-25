from __future__ import annotations

from dataclasses import dataclass, field
from io import StringIO
from random import random
from typing import TYPE_CHECKING, Any, Literal

import dacite
import discord
from html import unescape

from .base import (
    CoverImage,
    DateModel,
    ExternalSite,
    MediaTitle,
    MediaTrailer,
    NotFound,
    fetch_data,
)
from .formatters import HANDLE, format_anime_status, format_manga_status

if TYPE_CHECKING:
    from aiohttp import ClientSession


@dataclass(slots=True)
class NextEpisodeInfo:
    episode: int
    airingAt: int


@dataclass(slots=True)
class Studio:
    name: str


@dataclass(slots=True)
class StudioNode:
    nodes: list[Studio] = field(default_factory=list)

    def __str__(self) -> str:
        return ", ".join(s.name for s in self.nodes) if self.nodes else ""


@dataclass(slots=True)
class MediaData:
    id: int
    idMal: int | None
    title: MediaTitle
    coverImage: CoverImage
    description: str | None
    bannerImage: str | None
    format: Literal[
        "TV", "TV_SHORT", "MOVIE", "SPECIAL", "OVA", "ONA", "MUSIC", "MANGA", "NOVEL", "ONE_SHOT"
    ] | None
    status: Literal["FINISHED", "RELEASING", "NOT_YET_RELEASED", "CANCELLED", "HIATUS"] | None
    type: Literal["ANIME", "MANGA"]
    meanScore: float | None
    startDate: DateModel
    endDate: DateModel
    studios: StudioNode | None
    source: str | None
    siteUrl: str | None
    isAdult: bool | None
    duration: int | None
    episodes: int | None
    chapters: int | None
    volumes: int | None
    trailer: MediaTrailer | None
    nextAiringEpisode: NextEpisodeInfo | None
    synonyms: list[str] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)
    externalLinks: list[ExternalSite] = field(default_factory=list)

    @property
    def external_links(self) -> str:
        sites = StringIO()
        sites.write(" • ".join(map(str, self.externalLinks)))
        if self.trailer and self.trailer.site == "youtube":
            sites.write(f" • [YouTube Trailer](https://youtu.be/{self.trailer.id})")
        if self.idMal:
            sites.write(f" • [MyAnimeList](https://myanimelist.net/anime/{self.idMal})")
        output = sites.getvalue()
        sites.close()
        return output

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
        cleaned = HANDLE.handle(unescape(self.description))
        return f"{cleaned} …" if len(cleaned) > 400 else cleaned

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
        return self.source.replace("_", " ").title() if self.source else "Unknown"

    @property
    def prominent_colour(self) -> discord.Colour:
        if self.coverImage.color:
            return discord.Colour(int(self.coverImage.color[1:], 16))
        return discord.Colour.from_hsv(random(), 0.5, 1.0)

    @property
    def release_mode(self) -> str:
        return "Air date:" if self.type == "ANIME" else "Publish date:"

    @property
    def summarized_synonyms(self) -> str:
        if self.synonyms and len(self.synonyms) > 2:
            return f"{', '.join(self.synonyms[:2])} and {len(self.synonyms) - 2} more!"
        return ", ".join(self.synonyms)

    @classmethod
    async def request(
        cls, session: ClientSession, query: str, **kwargs: Any,
    ) -> NotFound | list[MediaData]:
        result = await fetch_data(session, query, **kwargs)
        if result.get("message"):
            return NotFound(**result)

        all_items = result.get("data", {}).get("Page", {}).get("media", [])
        return (
            [dacite.from_dict(data=item, data_class=cls) for item in all_items]
            if all_items
            else NotFound(message="Sad trombone. No results!")
        )
