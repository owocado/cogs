from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Sequence

import aiohttp


API_BASE = "https://api.themoviedb.org/3"
CDN_BASE = "https://image.tmdb.org/t/p/original"


@dataclass
class BaseSearch:
    id: int
    overview: str = ''
    popularity: float = 0.0
    vote_count: int = 0
    vote_average: float = 0.0
    backdrop_path: str = ''
    poster_path: str = ''
    genre_ids: Sequence[int] = field(default_factory=list)


@dataclass
class MediaNotFound:
    status_message: str
    http_code: int
    status_code: Optional[int] = None
    success: bool = False

    def __str__(self) -> str:
        return self.status_message or f'https://http.cat/{self.http_code}.jpg'


@dataclass
class CelebrityCast:
    id: int
    order: int
    name: str
    original_name: str
    adult: bool
    credit_id: str
    character: str
    known_for_department: str
    gender: int = 0
    cast_id: int = 0
    popularity: float = 0.0
    profile_path: str = ""


@dataclass
class Genre:
    id: int
    name: str


@dataclass
class ProductionCompany:
    id: int
    name: str
    logo_path: str = ""
    origin_country: str = ""


@dataclass
class ProductionCountry:
    iso_3166_1: str
    name: str


@dataclass
class SpokenLanguage:
    name: str
    iso_639_1: str
    english_name: str = ""


async def multi_search(
    session: aiohttp.ClientSession,
    api_key: str,
    query: str,
    include_adult: Literal["true", "false"] = "false",
) -> List[Dict[str, Any]] | MediaNotFound:
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
    return all_data["results"]
