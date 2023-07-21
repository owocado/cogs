from __future__ import annotations

import math
from io import StringIO
from typing import TYPE_CHECKING, List, Literal, Sequence

import discord
from dateutil.parser import isoparse
from redbot.core.utils.chat_formatting import pagify

from .api.base import CDN_BASE, CelebrityCast
from .api.person import Person
from .api.suggestions import MovieSuggestions, TVShowSuggestions
from .constants import TMDB_ICON

if TYPE_CHECKING:
    from .api.details import MovieDetails, TVShowDetails

GENDERS = (
    "",
    "\N{FEMALE SIGN}\N{VARIATION SELECTOR-16}",
    "\N{MALE SIGN}\N{VARIATION SELECTOR-16}",
    "\N{MALE WITH STROKE AND MALE AND FEMALE SIGN}",
)


def format_date(
    date_string: str | None,
    style: Literal["f", "F", "d", "D", "t", "T", "R"] = "R",
    *,
    prefix: str = ""
) -> str:
    if not date_string:
        return ""
    return prefix + discord.utils.format_dt(isoparse(date_string), style=style)


# credits to devon (Gorialis)
def natural_size(value: int) -> str:
    if value < 1000:
        return str(value)

    units = ('', 'K', 'M', 'B')
    power = int(math.log(max(abs(value), 1), 1000))
    return f"{value / (1000 ** power):.1f}{units[power]}"


def make_person_embed(person: Person, colour: discord.Colour | int) -> discord.Embed:
    emb = discord.Embed(colour=colour, title=person.name)
    # emb.description = shorten(person.biography or "", 500, placeholder=" …")
    emb.url = f"https://themoviedb.org/person/{person.id}"
    emb.set_thumbnail(url=person.person_image)
    out = StringIO()
    if bio := person.biography:
        out.write(f"{bio[:500] + ' …' if len(bio) > 500 else bio}\n\n")
    out.write(f"- **Known for:**  {person.known_for_department}\n")
    if dob := person.birthday:
        out.write(f"- **Birthday:**  {format_date(dob, 'D')} ({format_date(dob)})\n")
    if rip := person.deathday:
        out.write(f"- **Died:**  {format_date(rip, 'D')} ({format_date(rip)})\n")
    if person.place_of_birth:
        out.write(f"- **Place of Birth:**  {person.place_of_birth}\n")
    ext_links = []
    if person.imdb_id:
        ext_links.append(f"[IMDb](https://imdb.com/name/{person.imdb_id})")
    if person.homepage:
        ext_links.append(f"[Personal website]({person.homepage})\n")
    if ext_links:
        out.write(f"- **External links:**  {' · '.join(ext_links)}\n")
    emb.description = out.getvalue()
    out.close()
    emb.set_footer(text="Data provided by TheMovieDB!", icon_url=TMDB_ICON)
    return emb


def make_movie_embed(data: MovieDetails, colour: discord.Colour | int) -> discord.Embed:
    embed = discord.Embed(colour=colour, title=data.title)
    out = StringIO()
    out.write(f"{data.overview}\n\n")
    if imdb_id := data.imdb_id:
        out.write(f"- [IMDB page!](https://imdb.com/title/{imdb_id})\n")
    embed.url = f"https://themoviedb.org/movie/{data.id}"
    embed.set_image(url=f"{CDN_BASE}{data.backdrop_path or '/'}")
    embed.set_thumbnail(url=f"{CDN_BASE}{data.poster_path or '/'}")
    if data.release_date:
        out.write(f"- **Release Date:**  {format_date(data.release_date)}\n")
    if data.budget:
        out.write(f"- **Budget:**  {natural_size(data.budget)} USD\n")
    if data.revenue:
        out.write(f"- **Revenue:**  {natural_size(data.revenue)} USD\n")
    if data.humanize_runtime:
        out.write(f"- **Runtime:**  {data.humanize_runtime}\n")
    if data.vote_average and data.vote_count:
        out.write(f"- **TMDB rating:**  {data.humanize_votes}\n")
    if data.spoken_languages:
        out.write(f"- **Spoken languages:**  {data.all_spoken_languages}\n")
    if data.genres:
        out.write(f"- **Genres:**  {data.all_genres}\n")
    embed.description = out.getvalue()
    out.close()
    embed.set_footer(text="See next page for more info this movie!", icon_url=TMDB_ICON)
    return embed


def parse_credits(
    cast_data: Sequence[CelebrityCast],
    colour: discord.Colour | int,
    title: str,
    tmdb_id: str
) -> List[discord.Embed]:
    pretty_cast = "\n".join(
        f"**`[{i:>2}]`**  {GENDERS[actor.gender]} [{actor.name}]"
        f"(https://themoviedb.org/person/{actor.id})"
        f" as **{actor.character or '???'}**"
        for i, actor in enumerate(cast_data, 1)
    )

    pages = []
    all_pages = list(pagify(pretty_cast, page_length=1500))
    for i, page in enumerate(all_pages, start=1):
        emb = discord.Embed(colour=colour, description=page, title=title)
        emb.url = f"https://themoviedb.org/{tmdb_id}/cast"
        emb.set_footer(
            text=f"Celebrities Cast • Page {i} of {len(all_pages)}",
            icon_url=TMDB_ICON,
        )
        pages.append(emb)

    return pages


def make_tvshow_embed(data: TVShowDetails, colour: discord.Colour | int) -> discord.Embed:
    embed = discord.Embed(colour=colour, title=data.name)
    out = StringIO()
    if data.overview:
        out.write(f"{data.overview}\n\n")
    embed.url = f"https://themoviedb.org/tv/{data.id}"
    #  embed.set_image(url=f"{CDN_BASE}{data.backdrop_path or '/'}")
    embed.set_thumbnail(url=f"{CDN_BASE}{data.poster_path or '/'}")
    if data.created_by:
        out.write(f"- **Creators:**  {data.creators}\n")
    if data.status:
        out.write(f"- **Series status:**  {data.status} ({data.type})\n")
    if data.in_production:
        out.write("- **In production:**  ✅ Yes\n")
    if first_air_date := data.first_air_date:
        out.write(f"- **First Aired:**  {format_date(first_air_date)}\n")
    if last_air_date := data.last_air_date:
        out.write(f"- **Last Aired:**  {format_date(last_air_date)}\n")
    if data.number_of_seasons:
        out.write(f"- **Total Seasons:**  {data.seasons_count}\n")
    if runtime := data.episode_run_time:
        out.write(f"- **Average episode runtime:**  {runtime[0]} minutes\n")
    if data.genres:
        out.write(f"- **Genres:**  {data.all_genres}\n")
    if data.vote_average and data.vote_count:
        out.write(f"- **TMDB rating:**  {data.humanize_votes}\n")
    if data.networks:
        out.write(f"- **Networks:**  {data.all_networks}\n")
    if data.spoken_languages:
        out.write(f"- **Spoken Languages:**  {data.all_spoken_languages}\n")
    embed.description = out.getvalue()
    out.close()
    if data.seasons:
        for page in pagify(data.all_seasons, page_length=1024):
            embed.add_field(name="Seasons:", value=page, inline=True)
    if data.next_episode_to_air:
        embed.add_field(name="Next Episode:", value=data.next_episode_info, inline=False)
    embed.set_footer(text="See next page for more info on this series!", icon_url=TMDB_ICON)
    return embed


def make_suggestmovies_embed(
    data: MovieSuggestions, colour: discord.Colour | int, footer: str,
) -> discord.Embed:
    embed = discord.Embed(colour=colour, title=data.title)
    out = StringIO()
    if data.overview:
        out.write(f"{data.overview}\n\n")
    embed.url = f"https://themoviedb.org/movie/{data.id}"
    embed.set_image(url=f"{CDN_BASE}{data.backdrop_path or '/'}")
    embed.set_thumbnail(url=f"{CDN_BASE}{data.poster_path or '/'}")
    if data.release_date:
        out.write(f"- **Release Date:**  {format_date(data.release_date)}\n")
    if data.vote_average and data.vote_count:
        out.write(f"- **TMDB rating:**  {data.humanize_votes}\n")
    embed.set_footer(text=footer, icon_url=TMDB_ICON)
    embed.description = out.getvalue()
    out.close()
    return embed


def make_suggestshows_embed(
    data: TVShowSuggestions, colour: discord.Colour | int, footer: str,
) -> discord.Embed:
    embed = discord.Embed(colour=colour, title=data.name)
    out = StringIO()
    if data.overview:
        out.write(f"{data.overview}\n\n")
    embed.url = f"https://themoviedb.org/tv/{data.id}"
    embed.set_image(url=f"{CDN_BASE}{data.backdrop_path or '/'}")
    embed.set_thumbnail(url=f"{CDN_BASE}{data.poster_path or '/'}")
    if data.first_air_date:
        out.write(f"- **First Aired:**  {format_date(data.first_air_date)}\n")
    if data.vote_average and data.vote_count:
        out.write(f"- **TMDB rating:**  {data.humanize_votes}\n")
    embed.set_footer(text=footer, icon_url=TMDB_ICON)
    embed.description = out.getvalue()
    out.close()
    return embed
