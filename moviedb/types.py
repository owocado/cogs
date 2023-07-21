from __future__ import annotations

from typing import List, Optional, TypedDict


class CommonModel(TypedDict):
    adult: bool
    id: int
    overview: str
    popularity: float
    media_type: str


class MultiResult(CommonModel):
    backdrop_path: Optional[str]
    name: Optional[str]
    original_name: Optional[str]
    title: Optional[str]
    original_title: Optional[str]
    original_language: str
    poster_path: Optional[str]
    genre_ids: List[int]
    release_date: Optional[str]
    first_air_date: Optional[str]
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

