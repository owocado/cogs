import random

from discord import Interaction, app_commands
from rapidfuzz import process, utils
from redbot.core.bot import Red
from redbot.core.commands import BadArgument, Context

from .api.base import fetch_data
from .schemas import TAG_COLLECTION_SCHEMA
from .tags import ANILIST_GENRES, ANILIST_TAGS


class GenreTagFinder(app_commands.Transformer):

    async def convert(self, ctx: Context[Red], argument: str) -> str:
        if argument.casefold() == "random":
            return random.choice(ANILIST_GENRES)
        genre = process.extractOne(argument, ANILIST_GENRES, score_cutoff=75, processor=utils.default_process)
        if genre:
            return genre[0]

        LATEST_TAGS = []
        data = await fetch_data(ctx.bot.session, query=TAG_COLLECTION_SCHEMA)
        if data:
            LATEST_TAGS = [x["name"] for x in data["data"]["MediaTagCollection"]]
        tag = process.extractOne(
            argument, LATEST_TAGS or ANILIST_TAGS, score_cutoff=75, processor=utils.default_process
        )
        if tag:
            return tag[0]
        raise BadArgument("could not match given argument to a valid genre or tag!")

    async def transform(self, i: Interaction[Red], value: str) -> str:
        return value

    async def autocomplete(self, i: Interaction[Red], value: str) -> list[app_commands.Choice]:
        entries = ANILIST_GENRES + ANILIST_TAGS
        if not value:
            return [app_commands.Choice(name=x, value=x) for x in entries][:25]
        results = process.extract(
            value, entries, score_cutoff=75, processor=utils.default_process, limit=None
        )
        return [app_commands.Choice(name=x[0], value=x[0]) for x in results][:25]
