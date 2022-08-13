from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional, Sequence

import aiohttp

from .media import CoverImage, ExternalSite, Title as MediaTitle, Trailer


@dataclass
class MediaNode:
    idMal: Optional[int]
    siteUrl: str
    title: MediaTitle
    coverImage: CoverImage
    duration: Optional[int]
    format: str
    isAdult: bool
    trailer: Optional[Trailer]
    externalLinks: Sequence[ExternalSite] = field(default_factory=list)

    @classmethod
    def from_data(cls, data: dict) -> MediaNode:
        trailer = data.pop("trailer", None)
        ext_links = data.pop("externalLinks", [])
        return cls(
            title=MediaTitle(**data.pop("title", {})),
            coverImage=CoverImage(**data.pop("coverImage", {})),
            trailer=Trailer(**trailer) if trailer else None,
            externalLinks=[ExternalSite(**site) for site in ext_links],
            **data
        )


@dataclass
class ScheduleData:
    airingAt: int
    episode: int
    media: MediaNode

    @property
    def external_links(self) -> str:
        sites = " • ".join(map(str, self.media.externalLinks))
        if self.media.trailer and self.media.trailer.site == "youtube":
            sites += f' • [YouTube Trailer](https://youtu.be/{self.media.trailer.id})'
        if self.media.idMal:
            sites += f' • [MyAnimeList](https://myanimelist.net/anime/{self.media.idMal})'
        return sites

    @classmethod
    def from_data(cls, data: dict) -> MediaNode:
        return cls(media=MediaNode.from_data(data.pop("media", {})), **data)

    @classmethod
    async def request(
        cls, session: aiohttp.ClientSession, query: str, **kwargs
    ) -> str | Sequence[ScheduleData]:
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

        all_items = result.get("data", {}).get("Page", {}).get("airingSchedules", [])
        if not all_items:
            return f"https://http.cat/404.jpg"

        return [cls.from_data(item) for item in all_items]
