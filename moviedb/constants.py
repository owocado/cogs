from __future__ import annotations

from dataclasses import dataclass


API_BASE: str = "https://api.themoviedb.org/3"
CDN_BASE: str = "https://image.tmdb.org/t/p/original"
TMDB_ICON: str = "https://i.imgur.com/sSE7Usn.png"


@dataclass(slots=True)
class MediaNotFound:
    status_message: str
    http_code: int
    success: bool = False

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
    gender: int = 0
    cast_id: int = 0
    popularity: float = 0.0
    profile_path: str = ""


@dataclass(slots=True)
class Genre:
    id: int
    name: str


@dataclass(slots=True)
class ProductionCompany:
    id: int
    name: str
    logo_path: str = ""
    origin_country: str = ""


@dataclass(slots=True)
class ProductionCountry:
    iso_3166_1: str
    name: str


@dataclass(slots=True)
class SpokenLanguage:
    name: str
    iso_639_1: str
    english_name: str = ""
