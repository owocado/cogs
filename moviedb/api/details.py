from __future__ import annotations

import asyncio
from datetime import datetime
from dataclasses import dataclass
from typing import Any

import aiohttp
import dacite
from dateutil.parser import isoparse
from discord.utils import utcnow
from redbot.core.utils.chat_formatting import humanize_number

from .base import (
    CelebrityCast,
    Genre,
    MediaNotFound,
    ProductionCompany,
    ProductionCountry,
    Language,
)
from ..constants import API_BASE
from ..utils import format_date


@dataclass(slots=True)
class MovieDetails:
    id: int
    title: str
    original_title: str
    original_language: str
    adult: bool
    video: bool
    status: str
    tagline: str | None
    overview: str | None
    release_date: str | None
    budget: int | None
    revenue: int | None
    runtime: int | None
    vote_count: int | None
    vote_average: float | None
    popularity: float | None
    homepage: str | None
    imdb_id: str | None
    poster_path: str | None
    backdrop_path: str | None
    genres: list[Genre]
    credits: list[CelebrityCast]
    spoken_languages: list[Language]
    production_companies: list[ProductionCompany]
    production_countries: list[ProductionCountry]

    @property
    def all_genres(self) -> str:
        return ", ".join(g.name for g in self.genres)

    @property
    def all_production_companies(self) -> str:
        return "\n".join(g.name for g in self.production_companies)

    @property
    def all_production_countries(self) -> str:
        return ", ".join(g.name for g in self.production_countries)

    @property
    def all_spoken_languages(self) -> str:
        return ", ".join(str(g) for g in self.spoken_languages)

    @property
    def humanize_runtime(self) -> str:
        if not self.runtime:
            return ""
        h, m = self.runtime // 60, self.runtime % 60
        hours, minutes = f"{h}h" if h else "", f"{m}m" if m else ""
        return f"{hours} {minutes}"

    @property
    def humanize_votes(self) -> str:
        if not self.vote_count:
            return ""
        return f"**{self.vote_average:.1f}** ⭐ ({humanize_number(self.vote_count)} votes)"

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> MovieDetails:
        genres = [Genre(**g) for g in data.pop("genres", [])]
        credits = [CelebrityCast(**c) for c in data.pop("credits", {}).get("cast", [])]
        spoken_languages = [Language(**sl) for sl in data.pop("spoken_languages", [])]
        production_companies = [
            ProductionCompany(**p) for p in data.pop("production_companies", [])
        ]
        production_countries = [
            ProductionCountry(**pc) for pc in data.pop("production_countries", [])
        ]
        return cls(
            genres=genres,
            credits=credits,
            spoken_languages=spoken_languages,
            production_companies=production_companies,
            production_countries=production_countries,
            **data,
        )

    @classmethod
    async def request(
        cls, session: aiohttp.ClientSession, api_key: str, movie_id: Any
    ) -> MediaNotFound | MovieDetails:
        movie_data = {}
        params = {"api_key": api_key, "append_to_response": "credits"}
        try:
            async with session.get(f"{API_BASE}/movie/{movie_id}", params=params) as resp:
                if resp.status in [401, 404]:
                    err_data = await resp.json()
                    return MediaNotFound(err_data["status_message"], resp.status)
                if resp.status != 200:
                    return MediaNotFound("", resp.status)
                movie_data: dict = await resp.json()
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return MediaNotFound("⚠️ Operation timed out.", 408)
        movie_data["credits"] = movie_data.pop("credits", {}).get("cast", [])
        return dacite.from_dict(data_class=cls, data=movie_data)


@dataclass(slots=True)
class Creator:
    id: int
    credit_id: str
    name: str
    gender: int
    profile_path: str | None


@dataclass(slots=True)
class EpisodeInfo:
    id: int
    name: str
    overview: str
    vote_average: float | None
    vote_count: int | None
    air_date: str | None
    episode_number: int
    production_code: str
    runtime: int | None
    season_number: int
    still_path: str | None
    show_id: int | None


@dataclass(slots=True)
class Network:
    id: int
    name: str
    logo_path: str | None
    origin_country: str | None


@dataclass(slots=True)
class Season:
    id: int
    name: str
    air_date: str | None
    overview: str
    episode_count: int
    poster_path: str | None
    season_number: int = 0
    vote_average: float = 0.0

    @property
    def release_date(self) -> datetime | None:
        return isoparse(self.air_date) if self.air_date else None

    @property
    def prefix(self) -> str:
        if not self.release_date:
            return ""
        return "airing" if self.release_date.timestamp() > utcnow().timestamp() else "aired"


@dataclass(slots=True)
class TVShowDetails:
    id: int
    adult: bool
    name: str
    original_name: str
    first_air_date: str | None
    last_air_date: str | None
    homepage: str | None
    overview: str
    in_production: bool
    status: str
    type: str | None
    tagline: str | None
    number_of_episodes: int | None
    number_of_seasons: int | None
    popularity: float | None
    vote_average: float | None
    vote_count: int | None
    original_language: str | None
    backdrop_path: str | None
    poster_path: str | None
    next_episode_to_air: EpisodeInfo | None
    last_episode_to_air: EpisodeInfo | None
    created_by: list[Creator]
    credits: list[CelebrityCast]
    episode_run_time: list[int]
    genres: list[Genre]
    seasons: list[Season]
    languages: list[str]
    networks: list[Network]
    origin_country: list[str]
    production_companies: list[ProductionCompany]
    production_countries: list[ProductionCountry]
    spoken_languages: list[Language]

    @property
    def all_genres(self) -> str:
        return ", ".join([g.name for g in self.genres])

    @property
    def all_production_companies(self) -> str:
        return ", ".join([g.name for g in self.production_companies])

    @property
    def all_production_countries(self) -> str:
        return ", ".join([g.name for g in self.production_countries])

    @property
    def all_spoken_languages(self) -> str:
        return ", ".join([g.name for g in self.spoken_languages])

    @property
    def all_networks(self) -> str:
        if len(self.networks) > 3:
            left = len(self.networks) - 3
            return f"{', '.join(n.name for n in self.networks[:3])} & {left} more!"
        return ", ".join([g.name for g in self.networks])

    @property
    def all_seasons(self) -> str:
        return "\n".join(
            f'{i}. {tv.name}{format_date(tv.air_date, prefix=f", {tv.prefix} ")}'
            f"  ({tv.episode_count or 0} episodes)"
            for i, tv in enumerate(self.seasons, start=1)
        )

    @property
    def creators(self) -> str:
        return ", ".join([c.name for c in self.created_by])

    @property
    def humanize_votes(self) -> str:
        if not self.vote_count:
            return ""
        return f"**{self.vote_average:.1f}** ⭐  ({humanize_number(self.vote_count)} votes)"

    @property
    def next_episode_info(self) -> str:
        if not self.next_episode_to_air:
            return ""

        next_ep = self.next_episode_to_air
        next_airing = "unsure when it will air guhh!"
        if next_ep.air_date:
            next_airing = format_date(next_ep.air_date, prefix="likely airing ")
        return (
            f"**S{next_ep.season_number or 0}E{next_ep.episode_number or 0}**"
            f" : {next_airing}\n**Titled as:** {next_ep.name}"
        )

    @property
    def seasons_count(self) -> str:
        return f"{self.number_of_seasons} ({self.number_of_episodes} episodes)"

    @property
    def title(self) -> str:
        return self.name or self.original_name

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TVShowDetails:
        n_eta = data.pop("next_episode_to_air", {})
        l_eta = data.pop("last_episode_to_air", {})
        created_by = [Creator(**c) for c in data.pop("created_by", [])]
        credits = [CelebrityCast(**ccs) for ccs in data.pop("credits", {}).get("cast", [])]
        genres = [Genre(**g) for g in data.pop("genres", [])]
        seasons = [Season(**s) for s in data.pop("seasons", [])]
        networks = [Network(**n) for n in data.pop("networks", [])]
        production_companies = [
            ProductionCompany(**pcom) for pcom in data.pop("production_companies", [])
        ]
        production_countries = [
            ProductionCountry(**pctr) for pctr in data.pop("production_countries", [])
        ]
        spoken_languages = [Language(**sl) for sl in data.pop("spoken_languages", [])]
        return cls(
            next_episode_to_air=EpisodeInfo(**n_eta) if n_eta else None,
            last_episode_to_air=EpisodeInfo(**l_eta) if l_eta else None,
            created_by=created_by,
            credits=credits,
            genres=genres,
            seasons=seasons,
            networks=networks,
            production_companies=production_companies,
            production_countries=production_countries,
            spoken_languages=spoken_languages,
            **data,
        )

    @classmethod
    async def request(
        cls, session: aiohttp.ClientSession, api_key: str, tvshow_id: Any
    ) -> MediaNotFound | TVShowDetails:
        tvshow_data = {}
        params = {"api_key": api_key, "append_to_response": "credits"}
        try:
            async with session.get(f"{API_BASE}/tv/{tvshow_id}", params=params) as resp:
                if resp.status in [401, 404]:
                    err_data = await resp.json()
                    return MediaNotFound(err_data["status_message"], resp.status)
                if resp.status != 200:
                    return MediaNotFound("", resp.status)
                tvshow_data: dict = await resp.json()
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return MediaNotFound("⚠️ Operation timed out.", 408)
        tvshow_data["credits"] = tvshow_data.pop("credits", {}).get("cast", [])
        return dacite.from_dict(data_class=cls, data=tvshow_data)
