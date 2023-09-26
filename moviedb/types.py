from __future__ import annotations

from typing import List, Optional, TypedDict


class CommonModel(TypedDict):
    adult: bool
    id: int
    overview: str
    popularity: float
    media_type: str


class MultiResult(CommonModel):
    backdrop_path: str | None
    name: str | None
    original_name: str | None
    title: str | None
    original_title: str | None
    original_language: str
    poster_path: str | None
    genre_ids: List[int]
    release_date: str | None
    first_air_date: str | None
    video: bool
    vote_average: float
    vote_count: int
    origin_country: Optional[List[str]]


class Celebrity(CommonModel):
    name: str
    original_name: str
    gender: int
    known_for_department: str
    profile_path: str
    known_for: List[MultiResult]

