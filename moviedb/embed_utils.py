from __future__ import annotations

from textwrap import shorten
from typing import List, Sequence

import discord
from redbot.core.utils.chat_formatting import pagify

from .api.base import CDN_BASE, CelebrityCast
from .api.details import MovieDetails, TVShowDetails
from .api.person import Person
from .api.suggestions import MovieSuggestions, TVShowSuggestions
from .utils import format_date, natural_size

GENDERS = ["", "♀ ", "♂ ", "⚧ "]


def make_person_embed(person: Person, colour: discord.Colour) -> discord.Embed:
    emb = discord.Embed(colour=colour, title=person.name)
    emb.description = shorten(person.biography or "", 500, placeholder=" …")
    emb.url = f"https://www.themoviedb.org/person/{person.id}"
    emb.set_thumbnail(url=person.person_image)
    emb.add_field(name="Known For", value=person.known_for_department)
    if dob := person.birthday:
        emb.add_field(name="Birth Date", value=f"{format_date(dob, 'D')}\n({format_date(dob)})")
    if rip := person.deathday:
        emb.add_field(
            name="🙏 Passed away on", value=f"{format_date(rip, 'D')}\n({format_date(rip)})"
        )
    if person.place_of_birth:
        emb.add_field(name="Place of Birth", value=person.place_of_birth)
    ext_links: List[str] = []
    if person.imdb_id:
        ext_links.append(f"[IMDb](https://www.imdb.com/name/{person.imdb_id})")
    if person.homepage:
        ext_links.append(f"[Personal website]({person.homepage})\n")
    if ext_links:
        emb.add_field(name="External Links", value=", ".join(ext_links))
    emb.set_footer(text="Data provided by TheMovieDB!", icon_url="https://i.imgur.com/sSE7Usn.png")
    return emb


def make_movie_embed(data: MovieDetails, colour: discord.Colour) -> discord.Embed:
    embed = discord.Embed(title=data.title, colour=colour)
    description = data.overview
    if imdb_id := data.imdb_id:
        description += f"\n\n**[see IMDB page!](https://www.imdb.com/title/{imdb_id})**"
    embed.url = f"https://www.themoviedb.org/movie/{data.id}"
    embed.description = description
    embed.set_image(url=f"{CDN_BASE}{data.backdrop_path or '/'}")
    embed.set_thumbnail(url=f"{CDN_BASE}{data.poster_path or '/'}")
    if data.release_date:
        embed.add_field(name="Release Date", value=format_date(data.release_date))
    if data.budget:
        embed.add_field(name="Budget (USD)", value=f"${natural_size(data.budget)}")
    if data.revenue:
        embed.add_field(name="Revenue (USD)", value=f"${natural_size(data.revenue)}")
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
    tmdb_id: str
) -> List[discord.Embed]:
    pretty_cast = "\n".join(
        f"**`[{i:>2}]`**  {GENDERS[actor.gender]} [{actor.name}]"
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
    embed.set_image(url=f"{CDN_BASE}{data.backdrop_path or '/'}")
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
