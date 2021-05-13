import aiohttp
import asyncio
import base64

from aiocache import cached, SimpleMemoryCache
from bs4 import BeautifulSoup as bsp
from io import BytesIO
from math import floor
from random import choice
from string import capwords

import discord
from redbot.core import commands
from redbot.core.commands import Context
from redbot.core.utils.chat_formatting import bold, humanize_number, pagify
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

cache = SimpleMemoryCache()

API_URL = "https://pokeapi.co/api/v2"


class Pokebase(commands.Cog):
    """Search for various info about a Pokémon and related data."""

    __author__ = ["phalt", "siu3334"]
    __version__ = "0.2.6"

    def format_help_for_context(self, ctx: Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthors: {', '.join(self.__author__)}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.intro_gen = ["na", "rb", "gs", "rs", "dp", "bw", "xy", "sm", "ss"]
        self.intro_games = {
            "na": "Unknown",
            "rb": "Red/Blue\n(Gen. 1)",
            "gs": "Gold/Silver\n(Gen. 2)",
            "rs": "Ruby/Sapphire\n(Gen. 3)",
            "dp": "Diamond/Pearl\n(Gen. 4)",
            "bw": "Black/White\n(Gen. 5)",
            "xy": "X/Y\n(Gen. 6)",
            "sm": "Sun/Moon\n(Gen. 7)",
            "ss": "Sword/Shield\n(Gen. 8)",
        }
        self.styles = {
            "default": 3,
            "black": 50,
            "collector": 96,
            "dp": 5,
            "purple": 43,
        }
        self.trainers = {
            "ash": 13,
            "red": 922,
            "ethan": 900,
            "lyra": 901,
            "brendan": 241,
            "may": 255,
            "lucas": 747,
            "dawn": 856,
        }
        self.badges = {
            "kanto": [2, 3, 4, 5, 6, 7, 8, 9],
            "johto": [10, 11, 12, 13, 14, 15, 16, 17],
            "hoenn": [18, 19, 20, 21, 22, 23, 24, 25],
            "sinnoh": [26, 27, 28, 29, 30, 31, 32, 33],
            "unova": [34, 35, 36, 37, 38, 39, 40, 41],
            "kalos": [44, 45, 46, 47, 48, 49, 50, 51],
        }

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    def get_generation(self, pkmn_id: int):
        if pkmn_id > 898:
            return 0
        elif pkmn_id >= 810:
            return 8
        elif pkmn_id >= 722:
            return 7
        elif pkmn_id >= 650:
            return 6
        elif pkmn_id >= 494:
            return 5
        elif pkmn_id >= 387:
            return 4
        elif pkmn_id >= 252:
            return 3
        elif pkmn_id >= 152:
            return 2
        elif pkmn_id >= 1:
            return 1
        else:
            return 0

    @cached(ttl=86400, cache=SimpleMemoryCache)
    async def get_pokemon_data(self, pokemon: str):
        try:
            async with self.session.get(
                API_URL + f"/pokemon/{pokemon.lower()}"
            ) as response:
                if response.status != 200:
                    return None
                pokemon_data = await response.json()
        except asyncio.TimeoutError:
            return None

        return pokemon_data

    @cached(ttl=86400, cache=SimpleMemoryCache)
    async def get_species_data(self, pkmn_id: int):
        try:
            async with self.session.get(
                API_URL + f"/pokemon-species/{pkmn_id}"
            ) as response:
                if response.status != 200:
                    return None
                species_data = await response.json()
        except asyncio.TimeoutError:
            return None

        return species_data

    @cached(ttl=86400, cache=SimpleMemoryCache)
    async def get_evolution_chain(self, evo_url: str):
        try:
            async with self.session.get(evo_url) as response:
                if response.status != 200:
                    return None
                evolution_data = await response.json()
        except asyncio.TimeoutError:
            return None

        return evolution_data

    @commands.command()
    @cached(ttl=86400, cache=SimpleMemoryCache)
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def pdex(self, ctx: Context, pokemon: str):
        """Search for various info about a Pokémon.

        You can search by name or ID of a Pokémon.
        Pokémon ID refers to National Pokédex number.
        https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_National_Pok%C3%A9dex_number
        """
        async with ctx.typing():
            data = await self.get_pokemon_data(pokemon)
            if not data:
                return await ctx.send("No results.")

            # pages = []
            embed = discord.Embed(colour=await ctx.embed_colour())
            embed.set_author(
                name=f"#{str(data.get('id')).zfill(3)} - {data.get('name').title()}",
                url=f"https://www.pokemon.com/us/pokedex/{data.get('name')}",
            )
            embed.set_thumbnail(
                url=f"https://assets.pokemon.com/assets/cms2/img/pokedex/full/{str(data.get('id')).zfill(3)}.png",
            )
            introduced_in = str(
                self.intro_games[self.intro_gen[self.get_generation(data.get("id", 0))]]
            )
            embed.add_field(name="Introduced In", value=introduced_in)
            humanize_height = (
                f"{floor(data.get('height', 0) * 3.94 // 12)} ft."
                f"{floor(data.get('height', 0) * 3.94 % 12)} in."
                f"\n({data.get('height') / 10} m.)"
            )
            embed.add_field(name="Height", value=humanize_height)
            humanize_weight = (
                f"{round(data.get('weight', 0) * 0.2205, 2)} lbs."
                f"\n({data.get('weight') / 10} kgs.)"
            )
            embed.add_field(name="Weight", value=humanize_weight)
            embed.add_field(
                name="Types",
                value="/".join(
                    x.get("type").get("name").title() for x in data.get("types")
                ),
            )

            species_data = await self.get_species_data(data.get("id"))
            if species_data:
                gender_rate = species_data.get("gender_rate")
                male_ratio = 100 - ((gender_rate / 8) * 100)
                female_ratio = (gender_rate / 8) * 100
                genders = {
                    "male": 0.0 if gender_rate == -1 else male_ratio,
                    "female": 0.0 if gender_rate == -1 else female_ratio,
                    "genderless": True if gender_rate == -1 else False,
                }
                final_gender_rate = ""
                if genders["genderless"]:
                    final_gender_rate += "Genderless"
                if genders["male"] != 0.0:
                    final_gender_rate += f"♂️ {genders['male']}%\n"
                if genders["female"] != 0.0:
                    final_gender_rate += f"♀️ {genders['female']}%"
                embed.add_field(name="Gender Rate", value=final_gender_rate)
                embed.add_field(
                    name="Base Happiness",
                    value=f"{species_data.get('base_happiness', 0)} / 255",
                )
                embed.add_field(
                    name="Capture Rate",
                    value=f"{species_data.get('capture_rate', 0)} / 255",
                )

                genus = [
                    x.get("genus")
                    for x in species_data.get("genera")
                    if x.get("language").get("name") == "en"
                ]
                genus_text = "The " + genus[0]
                flavor_text = [
                    x.get("flavor_text")
                    for x in species_data.get("flavor_text_entries")
                    if x.get("language").get("name") == "en"
                ]
                flavor_text = (
                    choice(flavor_text)
                    .replace("\n", " ")
                    .replace("\f", " ")
                    .replace("\r", " ")
                )
                flavor_text = flavor_text
                embed.description = f"**{genus_text}**\n\n{flavor_text}"

            if data.get("held_items"):
                held_items = ""
                for item in data.get("held_items"):
                    held_items += "{} ({}%)\n".format(
                        item.get("item").get("name").replace("-", " ").title(),
                        item.get("version_details")[0].get("rarity"),
                    )
                embed.add_field(name="Held Items", value=held_items)
            else:
                embed.add_field(name="Held Items", value="None")

            abilities = ""
            for ability in data.get("abilities"):
                abilities += "[{}](https://bulbapedia.bulbagarden.net/wiki/{}_%28Ability%29){}\n".format(
                    ability.get("ability").get("name").replace("-", " ").title(),
                    ability.get("ability").get("name").title().replace("-", "_"),
                    " (Hidden Ability)" if ability.get("is_hidden") else "",
                )

            embed.add_field(name="Abilities", value=abilities)

            base_stats = {}
            for stat in data.get("stats"):
                base_stats[stat.get("stat").get("name")] = stat.get("base_stat")
            total_base_stats = sum(base_stats.values())

            pretty_base_stats = (
                f"`HP         : |{'█' * round((base_stats['hp'] / 255) * 10) * 2}"
                f"{' ' * (20 - round((base_stats['hp'] / 255) * 10) * 2)}|` **{base_stats['hp']}**\n"
                f"`Attack     : |{'█' * round((base_stats['attack'] / 255) * 10) * 2}"
                f"{' ' * (20 - round((base_stats['attack'] / 255) * 10) * 2)}|` **{base_stats['attack']}**\n"
                f"`Defense    : |{'█' * round((base_stats['defense'] / 255) * 10) * 2}"
                f"{' ' * (20 - round((base_stats['defense'] / 255) * 10) * 2)}|` **{base_stats['defense']}**\n"
                f"`Sp. Attack : |{'█' * round((base_stats['special-attack'] / 255) * 10) * 2}"
                f"{' ' * (20 - round((base_stats['special-attack'] / 255) * 10) * 2)}|` **{base_stats['special-attack']}**\n"
                f"`Sp. Defense: |{'█' * round((base_stats['special-defense'] / 255) * 10) * 2}"
                f"{' ' * (20 - round((base_stats['special-defense'] / 255) * 10) * 2)}|` **{base_stats['special-defense']}**\n"
                f"`Speed      : |{'█' * round((base_stats['speed'] / 255) * 10) * 2}"
                f"{' ' * (20 - round((base_stats['speed'] / 255) * 10) * 2)}|` **{base_stats['speed']}**\n"
                "`-----------------------------------`\n"
                f"`Total      : |{'█' * round((total_base_stats / 1125) * 10) * 2}"
                f"{' ' * (20 - round((total_base_stats / 1125) * 10) * 2)}|` **{total_base_stats}**\n"
            )
            embed.add_field(
                name="Base Stats (Base Form)", value=pretty_base_stats, inline=False
            )

            evolves_to = ""
            evolves_to_2 = ""
            if species_data.get("evolution_chain"):
                evo_url = species_data.get("evolution_chain").get("url")
                evo_data = (await self.get_evolution_chain(evo_url)).get("chain")
                base_evo = evo_data.get("species").get("name").title()
                if evo_data.get("evolves_to"):
                    evolves_to += " -> " + "/".join(
                        x.get("species").get("name").title() for x in evo_data["evolves_to"]
                    )
                if evo_data.get("evolves_to") and evo_data.get("evolves_to")[0].get("evolves_to"):
                    evolves_to_2 += " -> " + "/".join(
                        x.get("species").get("name").title()
                        for x in evo_data.get("evolves_to")[0].get("evolves_to")
                    )
            embed.add_field(
                name="Evolution Chain",
                value=f"{base_evo} {evolves_to} {evolves_to_2}",
                inline=False,
            )
            type_effectiveness = (
                "[See it on Bulbapedia](https://bulbapedia.bulbagarden.net/wiki/"
                f"{data.get('name').title()}_%28Pokémon%29#Type_effectiveness)"
            )
            embed.add_field(name="Weakness/Resistance", value=type_effectiveness)
            embed.set_footer(text="Powered by Poke API")

        await ctx.send(embed=embed)

    @commands.command()
    @cached(ttl=86400, cache=SimpleMemoryCache)
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def ability(self, ctx: Context, *, ability: str):
        """Get various info about a known Pokémon ability.
        You can search by ability's name or it's unique ID.

        Abilities provide passive effects for Pokémon in battle or in the overworld.
        Pokémon have multiple possible abilities but can have only one ability at a time.
        Check out Bulbapedia for greater detail:
        http://bulbapedia.bulbagarden.net/wiki/Ability
        https://bulbapedia.bulbagarden.net/wiki/Ability#List_of_Abilities
        """
        async with ctx.typing():
            try:
                async with self.session.get(
                    API_URL + f"/ability/{ability.replace(' ', '-').lower()}/"
                ) as response:
                    if response.status != 200:
                        await ctx.send(f"https://http.cat/{response.status}")
                        return
                    data = await response.json()
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            embed = discord.Embed(colour=discord.Color.random())
            embed.title = data.get("name").replace("-", " ").title()
            embed.url = "https://bulbapedia.bulbagarden.net/wiki/{}_%28Ability%29".format(
                data.get("name").title().replace("-", "_")
            )
            embed.description = [
                x.get("effect")
                for x in data.get("effect_entries")
                if x.get("language").get("name") == "en"
            ][0]

            if data.get("generation"):
                embed.add_field(
                    name="Introduced In",
                    value="Gen. "
                    + bold(
                        str(data.get("generation").get("name").split("-")[1].upper())
                    ),
                )
            short_effect = [
                x.get("short_effect")
                for x in data.get("effect_entries")
                if x.get("language").get("name") == "en"
            ][0]
            embed.add_field(name="Ability's Effect", value=short_effect, inline=False)
            if data.get("pokemon"):
                pokemons = ", ".join(
                    x.get("pokemon").get("name").title() for x in data.get("pokemon")
                )
                embed.add_field(
                    name=f"Pokémons with {data.get('name').title()}",
                    value=pokemons,
                    inline=False,
                )
            embed.set_footer(text="Powered by Poke API")

        await ctx.send(embed=embed)

    @commands.command()
    @cached(ttl=86400, cache=SimpleMemoryCache)
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def moves(self, ctx: Context, pokemon: str):
        """Get the list of all possible moves a Pokémon has."""
        async with ctx.typing():
            data = await self.get_pokemon_data(pokemon)
            if not data:
                return await ctx.send("No results.")

            if not data.get("moves"):
                return await ctx.send("No moves found for this Pokémon.")

            moves_list = ""
            for i, move in enumerate(data["moves"]):
                moves_list += "`[{}]` **{}**\n".format(
                    str(i + 1).zfill(2),
                    move["move"]["name"].title().replace("-", " "),
                )

            pages = []
            for page in pagify(moves_list, delims=["\n"], page_length=400):
                embed = discord.Embed(colour=await ctx.embed_colour())
                embed.title = f"Moves for : {data['name'].title()} (#{str(data['id']).zfill(3)})"
                embed.set_thumbnail(
                    url=f"https://assets.pokemon.com/assets/cms2/img/pokedex/full/{str(data['id']).zfill(3)}.png",
                )
                embed.description = page
                pages.append(embed)

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=60.0)

    @commands.command()
    @cached(ttl=86400, cache=SimpleMemoryCache)
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def moveinfo(self, ctx: Context, *, move: str):
        """Get various info about a Pokémon's move.
        You can search by a move name or it's ID.

        Moves are the skills of Pokémon in battle.
        In battle, a Pokémon uses one move each turn.
        Some moves (including those learned by Hidden Machine) can be used outside of battle as well,
        usually for the purpose of removing obstacles or exploring new areas.

        You can find a list of known Pokémon moves here:
        https://bulbapedia.bulbagarden.net/wiki/List_of_moves
        """
        move_query = move.replace(",", " ").replace(" ", "-").replace("'", "").lower()
        async with ctx.typing():
            try:
                async with self.session.get(
                    API_URL + f"/move/{move_query}/"
                ) as response:
                    if response.status != 200:
                        await ctx.send(f"https://http.cat/{response.status}")
                        return
                    data = await response.json()
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            embed = discord.Embed(colour=discord.Color.random())
            embed.title = data.get("name").replace("-", " ").title()
            embed.url = "https://bulbapedia.bulbagarden.net/wiki/{}_%28move%29".format(
                capwords(move).replace(" ", "_")
            )
            if data.get("effect_entries"):
                effect = "\n".join(
                    [
                        f"{x.get('short_effect')}\n{x.get('effect')}"
                        for x in data.get("effect_entries")
                        if x.get("language").get("name") == "en"
                    ]
                )
                embed.description = f"**Move Effect:** \n\n{effect}"

            if data.get("generation"):
                embed.add_field(
                    name="Introduced In",
                    value="Gen. "
                    + bold(
                        str(data.get("generation").get("name").split("-")[1].upper())
                    ),
                )
            if data.get("accuracy"):
                embed.add_field(name="Accuracy", value=f"{data.get('accuracy')}%")
            embed.add_field(name="Base Power", value=str(data.get("power")))
            if data.get("effect_chance"):
                embed.add_field(
                    name="Effect Chance", value=f"{data.get('effect_chance')}%"
                )
            embed.add_field(name="Power Points (PP)", value=str(data.get("pp")))
            if data.get("type"):
                embed.add_field(
                    name="Move Type", value=data.get("type").get("name").title()
                )
            if data.get("contest_type"):
                embed.add_field(
                    name="Contest Type",
                    value=data.get("contest_type").get("name").title(),
                )
            if data.get("damage_class"):
                embed.add_field(
                    name="Damage Class",
                    value=data.get("damage_class").get("name").title(),
                )
            embed.add_field(name="\u200b", value="\u200b")
            if data.get("learned_by_pokemon"):
                learned_by = [
                    x.get("name").title() for x in data.get("learned_by_pokemon")
                ]
                embed.add_field(
                    name=f"Learned by {str(len(learned_by))} Pokémons",
                    value=", ".join(learned_by)[:500] + "... and more.",
                    inline=False,
                )
            embed.set_footer(text="Powered by Poke API")

        await ctx.send(embed=embed)

    @commands.command()
    @cached(ttl=86400, cache=SimpleMemoryCache)
    @commands.bot_has_permissions(attach_files=True, embed_links=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def trainercard(
        self,
        ctx: Context,
        name: str,
        style: str,
        trainer: str,
        badge: str,
        *,
        pokemons: str,
    ):
        """Generate a trainer card for a Pokémon trainer in different styles.

        This command requires you to pass values for multiple parameters.
        These parameters are explained briefly as follows:

        `name` - Provide any personalised name of your choice.
        `style` - Only `default`, `black`, `collector`, `dp`, `purple` styles are supported.
        `trainer` - `ash`, `red`, `ethan`, `lyra`, `brendan`, `may`, `lucas`, `dawn` are supported.
        `badge` - `kanto`, `johto`, `hoenn`, `sinnoh`, `unova` and `kalos`  badge leagues are supported.
        `pokemons` - You can provide maximum up to 6 Pokémon's names or IDs.
        (Pokémons from #891 to #898 are not supported yet for trainer card)
        """
        base_url = "https://pokecharms.com/index.php?trainer-card-maker/render"
        if style not in ["default", "black", "collector", "dp", "purple"]:
            return await ctx.send_help()
        if trainer not in ["ash", "red", "ethan", "lyra", "brendan", "may", "lucas", "dawn"]:
            return await ctx.send_help()
        if badge not in ["kanto", "johto", "hoenn", "sinnoh", "unova", "kalos"]:
            return await ctx.send_help()
        if len(pokemons.split()) > 6:
            return await ctx.send_help()

        async with ctx.typing():
            pkmn_ids = []
            for pokemon in pokemons.split():
                get_ids = await self.get_pokemon_data(pokemon)
                if get_ids.get("id"):
                    pkmn_ids.append(get_ids["id"])

            panel_ids = []
            for npn in pkmn_ids:
                panel_url = "https://pokecharms.com/trainer-card-maker/pokemon-panels"
                payload = aiohttp.FormData()
                payload.add_field("number", npn)
                payload.add_field("_xfResponseType", "json")
                async with self.session.post(panel_url, data=payload) as resp:
                    if resp.status != 200:
                        panel_ids.append("1")
                    soup = bsp((await resp.json()).get("templateHtml"), "html.parser")
                    try:
                        panel_ids.append(soup.find_all('li')[0].get('data-id'))
                    except IndexError:
                        panel_ids.append("1")

            form = aiohttp.FormData()
            form.add_field("trainername", name[:12])
            form.add_field("background", str(self.styles[style]))
            form.add_field("character", str(self.trainers[trainer]))
            form.add_field("badges", "8")
            form.add_field("badgesUsed", ",".join(str(x) for x in self.badges[badge]))
            form.add_field("pokemon", str(len(pokemons.split())))
            form.add_field("pokemonUsed", ",".join(panel_ids))
            form.add_field("_xfResponseType", "json")
            try:
                async with self.session.post(base_url, data=form) as response:
                    if response.status != 200:
                        return await ctx.send(f"https://http.cat/{response.status}")
                    output = (await response.json()).get("trainerCard")
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

        if output:
            base64_img_bytes = output.encode("utf-8")
            decoded_image_data = BytesIO(base64.decodebytes(base64_img_bytes))
            decoded_image_data.seek(0)
            await ctx.send(
                file=discord.File(decoded_image_data, "trainer-card.png")
            )
            return
        else:
            await ctx.send("No trainer card was generated. :(")

    @cached(ttl=86400, cache=SimpleMemoryCache)
    async def get_item_info(self, query_url: str):
        try:
            async with self.session.get(query_url) as response:
                if response.status != 200:
                    return None
                item_data = await response.json()
        except asyncio.TimeoutError:
            return None

        return item_data

    @commands.command()
    @cached(ttl=86400, cache=SimpleMemoryCache)
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def item(self, ctx: Context, *, item: str):
        """Get various info about a Pokémon item.
        You can search by an item's name or unique ID.

        An item is an object in the games which the player can pick up,
        keep in their bag, and use in some manner.
        They have various uses, including healing, powering up,
        helping catch Pokémon, or to access a new area. For more info:
        https://bulbapedia.bulbagarden.net/wiki/Item
        https://bulbapedia.bulbagarden.net/wiki/Category:Items
        """
        item = item.replace(" ", "-").lower()
        async with ctx.typing():
            embed = discord.Embed(colour=await ctx.embed_colour())
            item_query_url = f"https://pokeapi.co/api/v2/item/{item}"
            item_data = await self.get_item_info(item_query_url)
            if not item_data:
                return await ctx.send("No results.")

            embed.title = item_data.get("name").title().replace("-", " ")
            embed.url = "https://bulbapedia.bulbagarden.net/wiki/{}".format(item.title().replace("-", "_"))
            item_effect = "**Item effect:** " + [
                x.get("effect")
                for x in item_data.get("effect_entries")
                if x.get("language").get("name") == "en"
            ][0]
            item_summary = "**Summary:** " + [
                x.get("short_effect")
                for x in item_data.get("effect_entries")
                if x.get("language").get("name") == "en"
            ][0]
            embed.description = f"{item_effect}\n\n{item_summary}"
            embed.add_field(name="Cost", value=humanize_number(item_data.get("cost")))
            embed.add_field(
                name="Category",
                value=str(item_data.get("category").get("name", "unknown").title().replace("-", " ")),
            )
            if item_data.get("attributes"):
                attributes = "\n".join(x.get("name").title().replace("-", " ") for x in item_data["attributes"])
                embed.add_field(name="Attributes", value=attributes)
            if item_data.get("fling_power"):
                embed.add_field(name="Fling Power", value=humanize_number(item_data["fling_power"]))
            if item_data.get("fling_effect"):
                fling_data = await self.get_item_info(item_data["fling_effect"]["url"])
                if fling_data:
                    fling_effect = [
                        x.get("effect")
                        for x in fling_data.get("effect_entries")
                        if x.get("language").get("name") == "en"
                    ][0]
                    embed.add_field(name="Fling Effect", value=fling_effect, inline=False)
            if item_data.get("held_by_pokemon"):
                held_by = ", ".join(x.get("pokemon").get("name").title() for x in item_data["held_by_pokemon"])
                embed.add_field(name="Held by Pokémon(s)", value=held_by, inline=False)
            embed.set_footer(text="Powered by Poke API!")

        await ctx.send(embed=embed)

    @commands.command(name="itemcat")
    @cached(ttl=86400, cache=SimpleMemoryCache)
    @commands.bot_has_permissions(embed_links=True)
    async def item_category(self, ctx: Context, *, category: str):
        """Returns the list of items in a given Pokémon item category."""
        category = category.replace(" ", "-").lower()
        async with ctx.typing():
            category_data = await self.get_item_info(f"https://pokeapi.co/api/v2/item-category/{category}/")
            if not category_data:
                return await ctx.send("No results.")
            embed = discord.Embed(colour=await ctx.embed_colour())
            embed.title = f"{category_data['name'].title().replace('-', ' ')}"
            items_list = ""
            for count, item in enumerate(category_data.get("items")):
                items_list += "**{}.** {}\n".format(count + 1, item.get("name").title().replace('-', ' '))

            embed.description = "__**List of items in this category:**__\n\n" + items_list
            embed.set_footer(text="Powered by Poke API!")

        await ctx.send(embed=embed)
