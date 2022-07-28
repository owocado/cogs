from __future__ import annotations

from typing import List, Sequence

import discord
from redbot.core.utils.chat_formatting import pagify

from .api import MovieDetails, MovieSuggestions, TVShowDetails, TVShowSuggestions
from .constants import CelebrityCast
from .utils import format_date, natural_size

CDN_BASE = "https://image.tmdb.org/t/p/original"


def make_movie_embed(data: MovieDetails, colour: discord.Colour) -> discord.Embed:
    embed = discord.Embed(title=data.title, colour=colour)
    description = data.overview
    if imdb_id := data.imdb_id:
        description += f"\n\n**[see IMDB page!](https://www.imdb.com/title/{imdb_id})**"
    embed.url = f"https://www.themoviedb.org/movie/{data.id}"
    embed.description = description
    # embed.set_image(url=f"{CDN_BASE}{data.backdrop_path or '/'}")
    embed.set_thumbnail(url=f"{CDN_BASE}{data.poster_path or '/'}")
    if data.release_date:
        embed.add_field(name="Release Date", value=format_date(data.release_date))
    if data.budget:
        embed.add_field(name="Budget (USD)", value=natural_size(data.budget))
    if data.revenue:
        embed.add_field(name="Revenue (USD)", value=natural_size(data.revenue))
    if data.humanize_runtime:
        embed.add_field(name="Runtime", value=data.humanize_runtime)
    if data.vote_average and data.vote_count:
        embed.add_field(name="TMDB Rating", value=data.humanize_votes)
    if data.spoken_languages:
        embed.add_field(name="Spoken languages", value=data.all_spoken_languages)
    if data.genres:
        embed.add_field(name="Genres", value=data.all_genres)
    if len(embed.fields) in {5, 8}:
        embed.add_field(name="\u200b", value="\u200b")
    embed.set_footer(
        text="Browse more info on this movie on next page!",
        icon_url="https://i.imgur.com/sSE7Usn.png"
    )
    return embed


def parse_credits(
    cast_data: Sequence[CelebrityCast],
    colour: discord.Colour,
    title: str,
    tmdb_id: int
) -> List[discord.Embed]:
    GENDERS_MAP = {"0": "", "1": "♀", "2": "♂", "3": "⚧"}
    pretty_cast = "\n".join(
        f"**`[{i:>2}]`**  {GENDERS_MAP[str(actor.gender)]} [{actor.name}]"
        f"(https://www.themoviedb.org/person/{actor.id})"
        f" as **{actor.character or '???'}**"
        for i, actor in enumerate(cast_data, 1)
    )

    pages = []
    all_pages = list(pagify(pretty_cast, page_length=1500))
    for i, page in enumerate(all_pages, start=1):
        emb = discord.Embed(colour=colour, description=page, title=title)
        emb.url = f"https://www.themoviedb.org/{tmdb_id}/cast"
        emb.set_footer(
            text=f"Celebrities Cast • Page {i} of {len(all_pages)}",
            icon_url="https://i.imgur.com/sSE7Usn.png",
        )
        pages.append(emb)

    return pages


def make_tvshow_embed(data: TVShowDetails, colour: discord.Colour) -> discord.Embed:
    embed = discord.Embed(title=data.name, colour=colour)
    summary = f"► Series status:  **{data.status or 'Unknown'}** ({data.type})\n"
    if runtime := data.episode_run_time:
        summary += f"► Average episode runtime:  **{runtime[0]} minutes**\n"
    if data.in_production:
        summary += f"► In production? ✅ Yes"
    embed.description=f"{data.overview or ''}\n\n{summary}"
    embed.url = f"https://www.themoviedb.org/tv/{data.id}"
    # embed.set_image(url=f"{CDN_BASE}{data.backdrop_path or '/'}")
    embed.set_thumbnail(url=f"{CDN_BASE}{data.poster_path or '/'}")
    if data.created_by:
        embed.add_field(name="Creators", value=data.creators)
    if first_air_date := data.first_air_date:
        embed.add_field(name="First Air Date", value=format_date(first_air_date))
    if last_air_date := data.last_air_date:
        embed.add_field(name="Last Air Date", value=format_date(last_air_date))
    if data.number_of_seasons:
        embed.add_field(name="Total Seasons", value=data.seasons_count)
    if data.genres:
        embed.add_field(name="Genres", value=data.all_genres)
    if data.vote_average and data.vote_count:
            embed.add_field(name="TMDB Rating", value=data.humanize_votes)
    if data.networks:
        embed.add_field(name="Networks", value=data.all_networks)
    if data.spoken_languages:
        embed.add_field(name="Spoken Language(s)", value=data.all_spoken_languages)
    if len(embed.fields) in {5, 8}:
        embed.add_field(name="\u200b", value="\u200b")
    if data.seasons:
        for page in pagify(data.all_seasons, page_length=1000):
            embed.add_field(name="Seasons summary", value=page, inline=False)
    if data.next_episode_to_air:
        embed.add_field(name="Next Episode Info", value=data.next_episode_info, inline=False)
    embed.set_footer(
        text=f"Browse more info on this TV show on next page!",
        icon_url="https://i.imgur.com/sSE7Usn.png",
    )
    return embed


def make_suggestmovies_embed(
    data: MovieSuggestions, colour: discord.Colour, footer: str,
) -> discord.Embed:
    embed = discord.Embed(colour=colour, title=data.title, description=data.overview or "")
    embed.url = f"https://www.themoviedb.org/movie/{data.id}"
    embed.set_image(url=f"{CDN_BASE}{data.backdrop_path or '/'}")
    embed.set_thumbnail(url=f"{CDN_BASE}{data.poster_path or '/'}")
    if data.release_date:
        embed.add_field(name="Release Date", value=format_date(data.release_date))
    if data.vote_average and data.vote_count:
        embed.add_field(name="TMDB Rating", value=data.humanize_votes)
    embed.set_footer(text=footer, icon_url="https://i.imgur.com/sSE7Usn.png")
    return embed


def make_suggestshows_embed(
    data: TVShowSuggestions, colour: discord.Colour, footer: str,
) -> discord.Embed:
    embed = discord.Embed(title=data.name, description=data.overview or "", colour=colour)
    embed.url = f"https://www.themoviedb.org/tv/{data.id}"
    embed.set_image(url=f"{CDN_BASE}{data.backdrop_path or '/'}")
    embed.set_thumbnail(url=f"{CDN_BASE}{data.poster_path or '/'}")
    if data.first_air_date:
        embed.add_field(name="First Aired", value=format_date(data.first_air_date))
    if data.vote_average and data.vote_count:
        embed.add_field(name="TMDB Rating", value=data.humanize_votes)
    embed.set_footer(text=footer, icon_url="https://i.imgur.com/sSE7Usn.png")
    return embed
