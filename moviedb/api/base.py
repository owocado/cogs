from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Literal

import aiohttp

from ..types import Celebrity, MultiResult

API_BASE = "https://api.themoviedb.org/3"
CDN_BASE = "https://image.tmdb.org/t/p/original"

__all__ = (
    "BaseSearch",
    "CelebrityCast",
    "Genre",
    "Language",
    "MediaNotFound",
    "ProductionCompany",
    "ProductionCountry",
    "multi_search",
)


@dataclass(slots=True)
class BaseSearch:
    adult: bool
    backdrop_path: str | None
    id: int
    overview: str | None
    poster_path: str | None
    media_type: str
    genre_ids: list[int]
    popularity: float
    vote_count: int
    vote_average: float


@dataclass(slots=True)
class MediaNotFound:
    status_message: str
    http_code: int | None = None
    status_code: int | None = None
    success: bool = False

    def __len__(self) -> int:
        return 0

    def __str__(self) -> str:
        return self.status_message or f'https://http.cat/{self.http_code}.jpg'


@dataclass(slots=True)
class CelebrityCast:
    id: int
    order: int
    name: str
    original_name: str
    adult: bool
    credit_id: str
    character: str
    known_for_department: str
    profile_path: str | None
    gender: int = 0
    cast_id: int = 0
    popularity: float = 0.0


@dataclass(slots=True)
class Genre:
    id: int
    name: str


@dataclass(slots=True)
class ProductionCompany:
    id: int
    name: str
    logo_path: str | None
    origin_country: str | None


@dataclass(slots=True)
class ProductionCountry:
    iso_3166_1: str
    name: str


@dataclass(slots=True)
class Language:
    name: str
    iso_639_1: str
    english_name: str | None

    def __str__(self) -> str:
        return self.english_name or self.name


async def multi_search(
    session: aiohttp.ClientSession,
    api_key: str,
    query: str,
    include_adult: Literal["true", "false"] = "false",
) -> list[Celebrity | MultiResult] | MediaNotFound:
    try:
        async with session.get(
            f"{API_BASE}/search/multi",
            params={"api_key": api_key, "query": query, "include_adult": include_adult}
        ) as resp:
            if resp.status in [401, 404]:
                data = await resp.json()
                return MediaNotFound(**data)
            if resp.status != 200:
                return MediaNotFound("No results found.", resp.status)
            all_data: dict = await resp.json()
    except (asyncio.TimeoutError, aiohttp.ClientError):
        return MediaNotFound("Operation timed out!", 408)

    if not all_data.get("results"):
        return MediaNotFound("No results found.", resp.status)
    return all_data.get("results", [])

