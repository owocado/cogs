from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import aiohttp
import dacite
from redbot.core.utils.chat_formatting import humanize_number

from .base import MediaNotFound
from ..constants import API_BASE


@dataclass(slots=True)
class BaseSuggestions:
    id: int
    adult: bool
    overview: str
    original_language: str
    media_type: str
    popularity: float
    vote_count: int
    vote_average: float
    genre_ids: list[int]


@dataclass(slots=True)
class MovieSuggestions(BaseSuggestions):
    title: str
    original_title: str
    release_date: str
    video: bool
    backdrop_path: str | None
    poster_path: str | None

    @property
    def humanize_votes(self) -> str:
        return f"**{self.vote_average:.1f}** ★ ({humanize_number(self.vote_count)} votes)"

    @classmethod
    async def request(
        cls, session: aiohttp.ClientSession, api_key: str, movie_id: Any
    ) -> MediaNotFound | list[MovieSuggestions]:
        url = f"{API_BASE}/movie/{movie_id}/recommendations"
        try:
            async with session.get(url, params={"api_key": api_key}) as resp:
                if resp.status in [401, 404]:
                    err_data = await resp.json()
                    return MediaNotFound(err_data["status_message"], resp.status)
                if resp.status != 200:
                    return MediaNotFound("", resp.status)
                data: dict = await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return MediaNotFound("⚠️ Operation timed out.", 408)

        if not data.get("results") or data["total_results"] < 1:
            return MediaNotFound("❌ No recommendations found related to that movie.", 404)

        return [dacite.from_dict(data_class=cls, data=obj) for obj in data["results"]]


@dataclass(slots=True)
class TVShowSuggestions(BaseSuggestions):
    name: str
    original_name: str
    first_air_date: str
    origin_country: list[str]
    backdrop_path: str | None
    poster_path: str | None

    @property
    def humanize_votes(self) -> str:
        return f"**{self.vote_average:.1f}** ★ ({humanize_number(self.vote_count)} votes)"

    @classmethod
    async def request(
        cls, session: aiohttp.ClientSession, api_key: str, tmdb_id: Any
    ) -> MediaNotFound | list[TVShowSuggestions]:
        url = f"{API_BASE}/tv/{tmdb_id}/recommendations"
        try:
            async with session.get(url, params={"api_key": api_key}) as resp:
                if resp.status in [401, 404]:
                    err_data = await resp.json()
                    return MediaNotFound(err_data["status_message"], resp.status)
                if resp.status != 200:
                    return MediaNotFound("", resp.status)
                data: dict = await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return MediaNotFound("⚠️ Operation timed out.", 408)

        if not data.get("results") or data["total_results"] < 1:
            return MediaNotFound("❌ No recommendations found related to that TV show.", 404)

        return [dacite.from_dict(data_class=cls, data=obj) for obj in data["results"]]
