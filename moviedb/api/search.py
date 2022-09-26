from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List

import aiohttp

from .base import BaseSearch, MediaNotFound, multi_search


@dataclass
class PersonSearch:
    id: int
    adult: bool
    name: str
    gender: int
    media_type: str
    popularity: float
    known_for_department: str
    profile_path: Optional[str] = None
    known_for: List[dict] = field(default_factory=list)

    @property
    def notable_roles(self) -> str:
        if not self.known_for:
            return ""
        first = self.known_for[0].get('title') or self.known_for[0].get('name')
        if len(self.known_for) > 1:
            first += f" & {len(self.known_for) - 1} more!"
        return f"(known for {first})"

    @classmethod
    async def request(
        cls,
        session: aiohttp.ClientSession,
        api_key: str,
        query: str
    ) -> MediaNotFound | List[PersonSearch]:
        all_data = await multi_search(session, api_key, query)
        if isinstance(all_data, MediaNotFound):
            return all_data
        filtered_data = [media for media in all_data if media.get("media_type") == "person"]
        if not filtered_data:
            return MediaNotFound("❌ No results.", 404)

        # filtered_data.sort(key=lambda x: x.get('name'))
        return [cls(**person) for person in filtered_data]


@dataclass
class MovieSearch(BaseSearch):
    title: str = ''
    original_title: str = ''
    release_date: str = ''
    original_language: str = ''
    video: Optional[bool] = None
    adult: Optional[bool] = None

    @classmethod
    async def request(
        cls,
        session: aiohttp.ClientSession,
        api_key: str,
        query: str
    ) -> MediaNotFound | List[MovieSearch]:
        all_data = await multi_search(session, api_key, query)
        if isinstance(all_data, MediaNotFound):
            return all_data
        filtered_data = [media for media in all_data if media.get("media_type") == "movie"]
        if not filtered_data:
            return MediaNotFound("❌ No results.", 404)

        filtered_data.sort(key=lambda x: x.get('release_date'), reverse=True)
        return [cls(**movie) for movie in filtered_data]


@dataclass
class TVShowSearch(BaseSearch):
    name: str = ''
    original_name: str = ''
    first_air_date: str = ''
    original_language: str = ''
    origin_country: List[str] = field(default_factory=list)

    @classmethod
    async def request(
        cls,
        session: aiohttp.ClientSession,
        api_key: str,
        query: str
    ) -> MediaNotFound | List[TVShowSearch]:
        all_data = await multi_search(session, api_key, query)
        if isinstance(all_data, MediaNotFound):
            return all_data
        filtered_data = [media for media in all_data if media.get("media_type") == "tv"]
        if not filtered_data:
            return MediaNotFound("❌ No results.", 404)

        filtered_data.sort(key=lambda x: x.get('first_air_date'), reverse=True)
        return [cls(**tvshow) for tvshow in filtered_data]
