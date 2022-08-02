from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Sequence

import aiohttp
from redbot.core.utils.chat_formatting import humanize_number

from .constants import (
    API_BASE,
    CelebrityCast,
    Genre,
    MediaNotFound,
    ProductionCompany,
    ProductionCountry,
    SpokenLanguage
)
from .utils import format_date


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
class MovieSearchData(BaseSearch):
    title: str = ''
    original_title: str = ''
    release_date: str = ''
    original_language: str = ''
    video: Optional[bool] = None
    adult: Optional[bool] = None

    @classmethod
    async def request(
        cls,
        api_key: str,
        query: str
    ) -> MediaNotFound | Sequence[MovieSearchData]:
        params = {'api_key': api_key, 'query': query.replace(' ', '+')}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'{API_BASE}/search/movie', params=params) as resp:
                    if resp.status in [401, 404]:
                        err_data = await resp.json()
                        return MediaNotFound(err_data['status_message'], resp.status)
                    if resp.status != 200:
                        return MediaNotFound('', resp.status)
                    data: Dict[str, Any] = await resp.json()
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return MediaNotFound('⚠️ Operation timed out.', 408)

        if not data.get('results') or data['total_results'] < 1:
            return MediaNotFound('❌ No results.', 404)

        # data['results'].sort(key=lambda x: x.get('release_date'), reverse=True)
        return [cls(**q) for q in data['results']]


@dataclass
class TVShowSearchData(BaseSearch):
    name: str = ''
    original_name: str = ''
    first_air_date: str = ''
    original_language: str = ''
    origin_country: Sequence[str] = field(default_factory=list)

    @classmethod
    async def request(
        cls,
        api_key: str,
        query: str
    ) -> MediaNotFound | Sequence[TVShowSearchData]:
        params = {'api_key': api_key, 'query': query.replace(' ', '+')}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'{API_BASE}/search/tv', params=params) as resp:
                    if resp.status in [401, 404]:
                        err_data = await resp.json()
                        return MediaNotFound(err_data['status_message'], resp.status)
                    if resp.status != 200:
                        return MediaNotFound('', resp.status)
                    data: Dict[str, Any] = await resp.json()
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return MediaNotFound('⚠️ Operation timed out.', 408)

        if not data.get('results') or data['total_results'] < 1:
            return MediaNotFound('❌ No results.', 404)

        # data['results'].sort(key=lambda x: x.get('first_air_date'), reverse=True)
        return [cls(**q) for q in data['results']]


@dataclass
class MovieDetails:
    id: int
    title: str
    original_title: str
    original_language: str
    adult: bool
    video: bool
    status: str
    tagline: str = ''
    overview: str = ''
    release_date: str = ''
    budget: int = 0
    revenue: int = 0
    runtime: int = 0
    vote_count: int = 0
    vote_average: float = 0.0
    popularity: float = 0.0
    homepage: Optional[str] = None
    imdb_id: Optional[str] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    belongs_to_collection: Optional[Dict[str, Any]] = None
    genres: Sequence[Genre] = field(default_factory=list)
    credits: Sequence[CelebrityCast] = field(default_factory=list)
    spoken_languages: Sequence[SpokenLanguage] = field(default_factory=list)
    production_companies: Sequence[ProductionCompany] = field(default_factory=list)
    production_countries: Sequence[ProductionCountry] = field(default_factory=list)

    @property
    def all_genres(self) -> str:
        return ', '.join([g.name for g in self.genres])

    @property
    def all_production_companies(self) -> str:
        return ', '.join([g.name for g in self.production_companies])

    @property
    def all_production_countries(self) -> str:
        return ', '.join([g.name for g in self.production_countries])

    @property
    def all_spoken_languages(self) -> str:
        return ', '.join([g.name for g in self.spoken_languages])

    @property
    def humanize_runtime(self) -> str:
        if not self.runtime:
            return ''
        return f'{self.runtime // 60}h {self.runtime % 60}m'

    @property
    def humanize_votes(self) -> str:
        if not self.vote_count:
            return ''
        return f'**{self.vote_average:.1f}** ⭐ / 10\n({humanize_number(self.vote_count)} votes)'

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> MovieDetails:
        btc = data.pop('belongs_to_collection', None)
        genres = [Genre(**g) for g in data.pop('genres', [])]
        credits = [CelebrityCast(**c) for c in data.pop('credits', {}).get('cast', [])]
        spoken_languages = [
            SpokenLanguage(**l) for l in data.pop('spoken_languages', [])
        ]
        production_companies = [
            ProductionCompany(**p) for p in data.pop('production_companies', [])
        ]
        production_countries = [
            ProductionCountry(**pc) for pc in data.pop('production_countries', [])
        ]
        return cls(
            belongs_to_collection=btc,
            genres=genres,
            credits=credits,
            spoken_languages=spoken_languages,
            production_companies=production_companies,
            production_countries=production_countries,
            **data
        )

    @classmethod
    async def request(
        cls, session: aiohttp.ClientSession, api_key: str, movie_id: int
    ) -> MediaNotFound | MovieDetails:
        movie_data = {}
        params = {'api_key': api_key, 'append_to_response': 'credits'}
        try:
            async with session.get(f'{API_BASE}/movie/{movie_id}', params=params) as resp:
                if resp.status in [401, 404]:
                    err_data = await resp.json()
                    return MediaNotFound(err_data['status_message'], resp.status)
                if resp.status != 200:
                    return MediaNotFound('', resp.status)
                movie_data = await resp.json()
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return MediaNotFound('⚠️ Operation timed out.', 408)

        return cls.from_json(movie_data)


@dataclass
class TVShowNotFound:
    status_message: str
    status_code: int

    def __str__(self) -> str:
        return self.status_message or f'https://http.cat/{self.status_code}.jpg'


@dataclass
class Creator:
    id: int
    credit_id: str
    name: str
    gender: int
    profile_path: str = ''


@dataclass
class EpisodeInfo:
    id: int
    name: str
    overview: str
    air_date: str
    episode_number: int
    season_number: int
    production_code: str
    runtime: None
    show_id: int = 0
    vote_average: float = 0.0
    vote_count: int = 0
    still_path: str = ''



@dataclass
class Network:
    id: int
    name: str
    logo_path: str = ''
    origin_country: str = ''


@dataclass
class Season:
    id: int
    name: str
    air_date: str
    overview: str
    episode_count: int
    poster_path: str = ''
    season_number: int = 0


@dataclass
class TVShowDetails:
    id: int
    adult: bool
    name: str
    original_name: str
    first_air_date: str
    last_air_date: str
    homepage: str
    overview: str
    in_production: bool
    status: str
    type: str = ''
    tagline: str = ''
    number_of_episodes: int = 0
    number_of_seasons: int = 0
    popularity: float = 0.0
    vote_average: float = 0.0
    vote_count: int = 0
    original_language: str = ''
    backdrop_path: str = ''
    poster_path: str = ''
    next_episode_to_air: Optional[EpisodeInfo] = None
    last_episode_to_air: Optional[EpisodeInfo] = None
    created_by: Sequence[Creator] = field(default_factory=list)
    credits: Sequence[CelebrityCast] = field(default_factory=list)
    episode_run_time: Sequence[int] = field(default_factory=list)
    genres: Sequence[Genre] = field(default_factory=list)
    seasons: Sequence[Season] = field(default_factory=list)
    languages: Sequence[str] = field(default_factory=list)
    networks: Sequence[Network] = field(default_factory=list)
    origin_country: Sequence[str] = field(default_factory=list)
    production_companies: Sequence[ProductionCompany] = field(default_factory=list)
    production_countries: Sequence[ProductionCountry] = field(default_factory=list)
    spoken_languages: Sequence[SpokenLanguage] = field(default_factory=list)

    @property
    def all_genres(self) -> str:
        return ', '.join([g.name for g in self.genres])

    @property
    def all_production_companies(self) -> str:
        return ', '.join([g.name for g in self.production_companies])

    @property
    def all_production_countries(self) -> str:
        return ', '.join([g.name for g in self.production_countries])

    @property
    def all_spoken_languages(self) -> str:
        return ', '.join([g.name for g in self.spoken_languages])

    @property
    def all_networks(self) -> str:
        return ', '.join([g.name for g in self.networks])

    @property
    def all_seasons(self) -> str:
        return '\n'.join(
            f'**{i}.** {tv.name}{format_date(tv.air_date, prefix=", aired ")}'
            f'  ({tv.episode_count or 0} episodes)'
            for i, tv in enumerate(self.seasons, start=1)
        )

    @property
    def creators(self) -> str:
        return '\n'.join([c.name for c in self.created_by])

    @property
    def humanize_votes(self) -> str:
        return f'**{self.vote_average:.1f}** ⭐ / 10\n({humanize_number(self.vote_count)} votes)'

    @property
    def next_episode_info(self) -> str:
        if not self.next_episode_to_air:
            return ''

        next_ep = self.next_episode_to_air
        next_airing = 'not sure when this episode will air!'
        if next_ep.air_date:
            next_airing = format_date(next_ep.air_date, prefix="likely airing ")
        return (
            f'**S{next_ep.season_number or 0}E{next_ep.episode_number or 0}**'
            f' : {next_airing}\n**Titled as:** {next_ep.name}'
        )

    @property
    def seasons_count(self) -> str:
        return f'{self.number_of_seasons} ({self.number_of_episodes} episodes)'

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TVShowDetails:
        n_eta = data.pop('next_episode_to_air', {})
        l_eta = data.pop('last_episode_to_air', {})
        created_by = [Creator(**c) for c in data.pop('created_by', [])]
        credits = [CelebrityCast(**ccs) for ccs in data.pop('credits', {}).get('cast', [])]
        genres = [Genre(**g) for g in data.pop('genres', [])]
        seasons = [Season(**s) for s in data.pop('seasons', [])]
        networks = [Network(**n) for n in data.pop('networks', [])]
        production_companies = [
            ProductionCompany(**pcom) for pcom in data.pop('production_companies', [])
        ]
        production_countries = [
            ProductionCountry(**pctr) for pctr in data.pop('production_countries', [])
        ]
        spoken_languages = [
            SpokenLanguage(**sl) for sl in data.pop('spoken_languages', [])
        ]
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
            **data
        )

    @classmethod
    async def request(
        cls,
        session: aiohttp.ClientSession,
        api_key: str,
        tvshow_id: int
    ) -> MediaNotFound | TVShowDetails:
        tvshow_data = {}
        params = {'api_key': api_key, 'append_to_response': 'credits'}
        try:
            async with session.get(f'{API_BASE}/tv/{tvshow_id}', params=params) as resp:
                if resp.status in [401, 404]:
                    err_data = await resp.json()
                    return MediaNotFound(err_data['status_message'], resp.status)
                if resp.status != 200:
                    return MediaNotFound('', resp.status)
                tvshow_data = await resp.json()
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return MediaNotFound('⚠️ Operation timed out.', 408)

        return cls.from_dict(tvshow_data)


@dataclass
class BaseSuggestions:
    id: int
    adult: bool
    overview: str
    original_language: str
    media_type: str
    popularity: float
    vote_count: int
    vote_average: float
    genre_ids: Sequence[int]


@dataclass
class MovieSuggestions(BaseSuggestions):
    title: str
    original_title: str
    release_date: str
    video: bool
    backdrop_path: str = ''
    poster_path: str = ''

    @property
    def humanize_votes(self) -> str:
        return f'**{self.vote_average:.1f}** ⭐ / 10\n({humanize_number(self.vote_count)} votes)'

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> MovieSuggestions:
        genre_ids = data.pop('genre_ids', [])
        return cls(genre_ids=genre_ids, **data)

    @classmethod
    async def request(
        cls,
        session: aiohttp.ClientSession,
        api_key: str,
        movie_id: str
    ) -> MediaNotFound | Sequence[MovieSuggestions]:
        url = f"{API_BASE}/movie/{movie_id}/recommendations"
        try:
            async with session.get(url, params={"api_key": api_key}) as resp:
                if resp.status in [401, 404]:
                    err_data = await resp.json()
                    return MediaNotFound(err_data['status_message'], resp.status)
                if resp.status != 200:
                    return MediaNotFound('', resp.status)
                data = await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return MediaNotFound('⚠️ Operation timed out.', 408)

        if not data.get('results') or data['total_results'] < 1:
            return MediaNotFound('❌ No recommendations found related to that movie.', 404)

        return [cls.from_json(obj) for obj in data['results']]


@dataclass
class TVShowSuggestions(BaseSuggestions):
    name: str
    original_name: str
    first_air_date: str
    origin_country: Sequence[str]
    backdrop_path: str = ''
    poster_path: str = ''

    @property
    def humanize_votes(self) -> str:
        return f'**{self.vote_average:.1f}** ⭐ / 10\n({humanize_number(self.vote_count)} votes)'

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> TVShowSuggestions:
        genre_ids = data.pop('genre_ids', [])
        origin_country = data.pop('origin_country', [])
        return cls(origin_country=origin_country, genre_ids=genre_ids, **data)

    @classmethod
    async def request(
        cls,
        session: aiohttp.ClientSession,
        api_key: str,
        query: str
    ) -> MediaNotFound | Sequence[TVShowSuggestions]:
        url = f"{API_BASE}/tv/{query}/recommendations"
        try:
            async with session.get(url, params={"api_key": api_key}) as resp:
                if resp.status in [401, 404]:
                    err_data = await resp.json()
                    return MediaNotFound(err_data['status_message'], resp.status)
                if resp.status != 200:
                    return MediaNotFound('', resp.status)
                data = await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return MediaNotFound('⚠️ Operation timed out.', 408)

        if not data.get('results') or data['total_results'] < 1:
            return MediaNotFound('❌ No recommendations found related to that TV show.', 404)

        return [cls.from_json(obj) for obj in data['results']]
