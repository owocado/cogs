from random import choice

import discord
from redbot.core import Config, commands
from redbot.core.commands import Context
from redbot.core.utils.chat_formatting import bold, quote

from .constants import *


class PDA(commands.Cog):
    """Do roleplay with your Discord friends or virtual strangers."""

    __author__ = "siu3334 (<@306810730055729152>)"
    __version__ = "0.4.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 123456789987654321, force_registration=True)
        default_global = {"schema_version": 1}
        default_user = {
            "BAKA_TO": 0,
            "BAKA_FROM": 0,
            "BULLY_TO": 0,
            "BULLY_FROM": 0,
            "CUDDLE_TO": 0,
            "CUDDLE_FROM": 0,
            "CRY_COUNT": 0,
            "FEED_TO": 0,
            "FEED_FROM": 0,
            "HIGHFIVE_TO": 0,
            "HIGHFIVE_FROM": 0,
            "HUG_TO": 0,
            "HUG_FROM": 0,
            "KILL_TO": 0,
            "KILL_FROM": 0,
            "KISS_TO": 0,
            "KISS_FROM": 0,
            "LICK_TO": 0,
            "LICK_FROM": 0,
            "NOM_TO": 0,
            "NOM_FROM": 0,
            "PAT_TO": 0,
            "PAT_FROM": 0,
            "POKE_TO": 0,
            "POKE_FROM": 0,
            "PUNCH_TO": 0,
            "PUNCH_FROM": 0,
            "SLAP_TO": 0,
            "SLAP_FROM": 0,
            "SMUG_COUNT": 0,
            "TICKLE_TO": 0,
            "TICKLE_FROM": 0,
        }
        self.config.register_global(**default_global)
        self.config.register_member(**default_user)
        self.config.register_user(**default_user)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def baka(self, ctx: Context, *, member: discord.Member):
        """Call someone a BAKA with a GIF reaction!"""
        if member.id == ctx.me.id:
            return await ctx.send("**Ｎ Ｏ   Ｕ**")

        if member.id == ctx.author.id:
            return await ctx.send(f"{bold(ctx.author.name)}, you really are BAKA. Stupid!! 💩")

        await ctx.trigger_typing()
        baka_to = await self.config.member(ctx.author).BAKA_TO()
        baka_from = await self.config.member(member).BAKA_FROM()
        gbaka_to = await self.config.user(ctx.author).BAKA_TO()
        gbaka_from = await self.config.user(member).BAKA_FROM()
        await self.config.member(ctx.author).BAKA_TO.set(baka_to + 1)
        await self.config.member(member).BAKA_FROM.set(baka_from + 1)
        await self.config.user(ctx.author).BAKA_TO.set(gbaka_to + 1)
        await self.config.user(member).BAKA_FROM.set(gbaka_from + 1)
        embed = discord.Embed(colour=member.colour)
        message = f"_**{ctx.author.name}** calls {member.mention} a BAKA bahahahahaha!!!_"
        embed.set_image(url=choice(BAKA))
        footer = (
            f"So far, {ctx.author} called {baka_to + 1} people a BAKA,\n{member} "
            + f"got called a BAKA {baka_from + 1} times by others in this server."
        )
        embed.set_footer(text=footer)

        await ctx.send(content=quote(message), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 90, commands.BucketType.member)
    async def bully(self, ctx: Context, *, member: discord.Member):
        """Bully someone in this server with a funny GIF!"""
        if member.id == ctx.me.id:
            return await ctx.send("**Ｎ Ｏ   Ｕ**")

        if member.id == ctx.author.id:
            return await ctx.send(
                f"{ctx.author.mention} Self bullying doesn't make sense. Stop it, get some help."
            )

        await ctx.trigger_typing()
        bully_to = await self.config.member(ctx.author).BULLY_TO()
        bully_from = await self.config.member(member).BULLY_FROM()
        gbully_to = await self.config.user(ctx.author).BULLY_TO()
        gbully_from = await self.config.user(member).BULLY_FROM()
        await self.config.member(ctx.author).BULLY_TO.set(bully_to + 1)
        await self.config.member(member).BULLY_FROM.set(bully_from + 1)
        await self.config.user(ctx.author).BULLY_TO.set(gbully_to + 1)
        await self.config.user(member).BULLY_FROM.set(gbully_from + 1)
        embed = discord.Embed(colour=member.colour)
        message = f"_**{ctx.author.name}** bullies {member.mention}_ 🤡"
        embed.set_image(url=choice(BULLY))
        footer = (
            f"So far, {ctx.author} bullied others {bully_to + 1} times,\n{member} "
            + f"got bullied {bully_from + 1} times in this server.\n"
            + f"Someone call police to get {ctx.author.name} arrested."
        )
        embed.set_footer(text=footer)

        await ctx.send(content=quote(message), embed=embed)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def cry(self, ctx: Context):
        """Let others know that you feel like crying or just wanna cry."""
        await ctx.trigger_typing()
        cry_count = await self.config.member(ctx.author).CRY_COUNT()
        gcry_count = await self.config.user(ctx.author).CRY_COUNT()
        await self.config.member(ctx.author).CRY_COUNT.set(cry_count + 1)
        await self.config.user(ctx.author).CRY_COUNT.set(gcry_count + 1)
        embed = discord.Embed(colour=ctx.author.colour)
        embed.description = f"{ctx.author.mention} {choice(CRY_STRINGS)}"
        embed.set_image(url=choice(CRY))
        footer = f"{ctx.author} has cried {cry_count + 1} times in this server so far."
        embed.set_footer(text=footer)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def cuddle(self, ctx: Context, *, member: discord.Member):
        """Cuddle with a server member!"""
        if member.id == ctx.author.id:
            return await ctx.send(
                f"{ctx.author.mention} According to all known laws of roleplay, "
                + "there is no way you can cuddle yourself! Go cuddle with "
                + "someone... or a pillow, if you're lonely like me. 😔"
            )

        await ctx.trigger_typing()
        cuddle_to = await self.config.member(ctx.author).CUDDLE_TO()
        cuddle_from = await self.config.member(member).CUDDLE_FROM()
        gcuddle_to = await self.config.user(ctx.author).CUDDLE_TO()
        gcuddle_from = await self.config.user(member).CUDDLE_FROM()
        await self.config.member(ctx.author).CUDDLE_TO.set(cuddle_to + 1)
        await self.config.member(member).CUDDLE_FROM.set(cuddle_from + 1)
        await self.config.user(ctx.author).CUDDLE_TO.set(gcuddle_to + 1)
        await self.config.user(member).CUDDLE_FROM.set(gcuddle_from + 1)
        embed = discord.Embed(colour=member.colour)
        if member.id == ctx.me.id:
            message = (
                f"Awww thanks for cuddles, {bold(ctx.author.name)}! Very kind of you. 😳"
            )
        else:
            message = f"_**{ctx.author.name}** cuddles_ {member.mention}"
        embed.set_image(url=str(choice(CUDDLE)))
        footer = (
            f"So far, {ctx.author} sent {cuddle_to + 1} cuddles,\n"
            + f"{'I' if member == ctx.me else member} received"
            + f" {cuddle_from + 1} cuddles in this server."
        )
        embed.set_footer(text=footer)

        await ctx.send(content=quote(message), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def feed(self, ctx: Context, *, member: discord.Member):
        """Feed someone from this server virtually!"""
        if member.id == ctx.author.id:
            return await ctx.send(f"_{ctx.author.mention} eats {bold(choice(RECIPES))}!_")

        await ctx.trigger_typing()
        feed_to = await self.config.member(ctx.author).FEED_TO()
        feed_from = await self.config.member(member).FEED_FROM()
        gfeed_to = await self.config.user(ctx.author).FEED_TO()
        gfeed_from = await self.config.user(member).FEED_FROM()
        await self.config.member(ctx.author).FEED_TO.set(feed_to + 1)
        await self.config.member(member).FEED_FROM.set(feed_from + 1)
        await self.config.user(ctx.author).FEED_TO.set(gfeed_to + 1)
        await self.config.user(member).FEED_FROM.set(gfeed_from + 1)
        embed = discord.Embed(colour=member.colour)
        if member.id == ctx.me.id:
            message = f"OWO! Thanks for yummy food..., {bold(ctx.author.name)}! ❤️"
        else:
            message = f"_**{ctx.author.name}** feeds {member.mention} some delicious food!_"
        embed.set_image(url=choice(FEED))
        footer = (
            f"So far, {ctx.author} have fed {feed_to + 1} people,\n"
            + f"{'I' if member == ctx.me else member} was fed "
            + f"some food {feed_from + 1} times in this server."
        )
        embed.set_footer(text=footer)

        await ctx.send(content=quote(message), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def highfive(self, ctx: Context, *, member: discord.Member):
        """High-fives a user!"""
        if member.id == ctx.author.id:
            return await ctx.send(
                f"_{ctx.author.mention} high-fives themselves in mirror, I guess?_"
            )

        await ctx.trigger_typing()
        h5_to = await self.config.member(ctx.author).HIGHFIVE_TO()
        h5_from = await self.config.member(member).HIGHFIVE_FROM()
        gh5_to = await self.config.user(ctx.author).HIGHFIVE_TO()
        gh5_from = await self.config.user(member).HIGHFIVE_FROM()
        await self.config.member(ctx.author).HIGHFIVE_TO.set(h5_to + 1)
        await self.config.member(member).HIGHFIVE_FROM.set(h5_from + 1)
        await self.config.user(ctx.author).HIGHFIVE_TO.set(gh5_to + 1)
        await self.config.user(member).HIGHFIVE_FROM.set(gh5_from + 1)
        embed = discord.Embed(colour=member.colour)
        if member.id == ctx.me.id:
            message = f"_high-fives back to {bold(ctx.author.name)}_ 👀"
            embed.set_image(url="https://i.imgur.com/hQPCYUJ.gif")
        else:
            message = f"_**{ctx.author.name}** high fives_ {member.mention}"
            embed.set_image(url=choice(HIGHFIVE))
        footer = (
            f"So far, {ctx.author} sent {h5_to + 1} high-fives,\n"
            + f"{'I' if member == ctx.me else member} received "
            + f"{h5_from + 1} high-fives in this server."
        )
        embed.set_footer(text=footer)

        await ctx.send(content=quote(message), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def hugs(self, ctx: Context, *, member: discord.Member):
        """Hug a user virtually on Discord!"""
        if member.id == ctx.author.id:
            return await ctx.send(
                f"{ctx.author.mention} One dOEs NOt SiMplY hUg THeIR oWn sELF!!!!!"
            )

        await ctx.trigger_typing()
        hug_to = await self.config.member(ctx.author).HUG_TO()
        hug_from = await self.config.member(member).HUG_FROM()
        ghug_to = await self.config.user(ctx.author).HUG_TO()
        ghug_from = await self.config.user(member).HUG_FROM()
        await self.config.member(ctx.author).HUG_TO.set(hug_to + 1)
        await self.config.member(member).HUG_FROM.set(hug_from + 1)
        await self.config.user(ctx.author).HUG_TO.set(ghug_to + 1)
        await self.config.user(member).HUG_FROM.set(ghug_from + 1)
        embed = discord.Embed(colour=member.colour)
        if member.id == ctx.me.id:
            message = f"Awwww thanks! So nice of you! _hugs **{ctx.author.name}** back_ 🤗"
        else:
            message = f"_**{ctx.author.name}** hugs_ {member.mention} 🤗"
        embed.set_image(url=str(choice(HUG)))
        footer = (
            f"So far, {ctx.author} gave {hug_to + 1} hugs,\n"
            + f"{'I' if member == ctx.me else member} received "
            + f"{hug_from + 1} hugs from others in this server!"
        )
        embed.set_footer(text=footer)

        await ctx.send(content=quote(message), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 90, commands.BucketType.member)
    async def kill(self, ctx: Context, *, member: discord.Member):
        """Virtually attempt to kill a server member with a GIF reaction!"""
        if member.id == ctx.me.id:
            return await ctx.send("**Ｎ Ｏ   Ｕ**")

        if member.id == ctx.author.id:
            return await ctx.send(
                f"{ctx.author.mention} Seppukku is not allowed on my watch. 💀"
            )

        await ctx.trigger_typing()
        kill_to = await self.config.member(ctx.author).KILL_TO()
        kill_from = await self.config.member(member).KILL_FROM()
        gkill_to = await self.config.user(ctx.author).KILL_TO()
        gkill_from = await self.config.user(member).KILL_FROM()
        await self.config.member(ctx.author).KILL_TO.set(kill_to + 1)
        await self.config.member(member).KILL_FROM.set(kill_from + 1)
        await self.config.user(ctx.author).KILL_TO.set(gkill_to + 1)
        await self.config.user(member).KILL_FROM.set(gkill_from + 1)
        embed = discord.Embed(colour=member.colour)
        message = f"_**{ctx.author.name}** tries to kill {member.mention}!_ 🇫"
        embed.set_image(url=choice(KILL))
        footer = (
            f"So far, {ctx.author} attempted {kill_to + 1} kills,\n{member} "
            + f"almost got killed {kill_from + 1} times in this server!"
        )
        embed.set_footer(text=footer)

        await ctx.send(content=quote(message), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def kiss(self, ctx: Context, *, member: discord.Member):
        """[NSFW] Kiss a user! Only allowed in NSFW channel."""
        if not ctx.channel.is_nsfw():
            return await ctx.send("NSFW command blocked in non NSFW channel.")

        if member.id == ctx.author.id:
            return await ctx.send(
                f"Poggers {bold(ctx.author.name)}, you just kissed yourself! LOL!!! 💋"
            )

        await ctx.trigger_typing()
        kiss_to = await self.config.member(ctx.author).KISS_TO()
        kiss_from = await self.config.member(member).KISS_FROM()
        gkiss_to = await self.config.user(ctx.author).KISS_TO()
        gkiss_from = await self.config.user(member).KISS_FROM()
        await self.config.member(ctx.author).KISS_TO.set(kiss_to + 1)
        await self.config.member(member).KISS_FROM.set(kiss_from + 1)
        await self.config.user(ctx.author).KISS_TO.set(gkiss_to + 1)
        await self.config.user(member).KISS_FROM.set(gkiss_from + 1)
        embed = discord.Embed(colour=member.colour)
        if member.id == ctx.me.id:
            message = f"Awwww so nice of you! _kisses **{ctx.author.name}** back!_ 😘 🥰"
        else:
            message = f"_**{ctx.author.name}** kisses_ {member.mention} 😘 🥰"
        embed.set_image(url=str(choice(KISS)))
        footer = (
            f"So far, {ctx.author} have kissed {kiss_to + 1} people,\n"
            + f"{member} received {kiss_from + 1} kisses in this server!"
        )
        embed.set_footer(text=footer)

        await ctx.send(content=quote(message), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def lick(self, ctx: Context, *, member: discord.Member):
        """[NSFW] Lick a user! Only allowed in NSFW channel."""
        if not ctx.channel.is_nsfw():
            return await ctx.send("NSFW command blocked in non NSFW channel.")

        if member.id == ctx.me.id:
            return await ctx.send(
                f"{ctx.author.mention} You wanna lick a bot? Very horny! Here, lick this: 🍆"
            )

        await ctx.trigger_typing()
        lick_to = await self.config.member(ctx.author).LICK_TO()
        lick_from = await self.config.member(member).LICK_FROM()
        glick_to = await self.config.user(ctx.author).LICK_TO()
        glick_from = await self.config.user(member).LICK_FROM()
        await self.config.member(ctx.author).LICK_TO.set(lick_to + 1)
        await self.config.member(member).LICK_FROM.set(lick_from + 1)
        await self.config.user(ctx.author).LICK_TO.set(glick_to + 1)
        await self.config.user(member).LICK_FROM.set(glick_from + 1)
        embed = discord.Embed(colour=member.colour)
        message = (
            f"{ctx.author.mention} Poggers, you just licked yourself. 👏"
            if member.id == ctx.author.id
            else f"_**{ctx.author.name}** licks_ {member.mention} 😳"
        )
        embed.set_image(url=choice(LICK))
        footer = (
            f"So far, {ctx.author} have licked others {lick_to + 1} times,\n"
            + f"{member} got licked {lick_from + 1} times in this server!"
        )
        embed.set_footer(text=footer)

        await ctx.send(content=quote(message), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def nom(self, ctx: Context, *, member: discord.Member):
        """Try to nom/bite a server member!"""
        if member.id == ctx.me.id:
            return await ctx.send(f"**OH NO!** _runs away_")

        message = (
            f"Waaaaaa! {bold(ctx.author.name)}, You bit yourself! Whyyyy?? 😭"
            if member.id == ctx.author.id
            else f"_**{ctx.author.name}** casually noms_ {member.mention} 😈"
        )
        await ctx.trigger_typing()
        nom_to = await self.config.member(ctx.author).NOM_TO()
        nom_from = await self.config.member(member).NOM_FROM()
        gnom_to = await self.config.user(ctx.author).NOM_TO()
        gnom_from = await self.config.user(member).NOM_FROM()
        await self.config.member(ctx.author).NOM_TO.set(nom_to + 1)
        await self.config.member(member).NOM_FROM.set(nom_from + 1)
        await self.config.user(ctx.author).NOM_TO.set(gnom_to + 1)
        await self.config.user(member).NOM_FROM.set(gnom_from + 1)
        embed = discord.Embed(colour=member.colour)
        embed.set_image(url=choice(BITE))
        footer = (
            f"So far, {ctx.author} sent {nom_to + 1} noms to others,\n"
            + f"{member} got nom'd {nom_from + 1} times in this server!"
        )
        embed.set_footer(text=footer)

        await ctx.send(content=quote(message), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def pat(self, ctx: Context, *, member: discord.Member):
        """Pat a server member with wholesome GIF!"""
        if member.id == ctx.author.id:
            return await ctx.send(
                f"{ctx.author.mention} _pats themselves, I guess? **yay**_ 🎉"
            )

        await ctx.trigger_typing()
        pat_to = await self.config.member(ctx.author).PAT_TO()
        pat_from = await self.config.member(member).PAT_FROM()
        gpat_to = await self.config.user(ctx.author).PAT_TO()
        gpat_from = await self.config.user(member).PAT_FROM()
        await self.config.member(ctx.author).PAT_TO.set(pat_to + 1)
        await self.config.member(member).PAT_FROM.set(pat_from + 1)
        await self.config.user(ctx.author).PAT_TO.set(gpat_to + 1)
        await self.config.user(member).PAT_FROM.set(gpat_from + 1)
        message = (
            f"Wowie! Thanks {bold(ctx.author.name)} for giving me pats. 😳 😘"
            if member.id == ctx.me.id
            else f"_**{ctx.author.name}** pats_ {member.mention}"
        )
        embed = discord.Embed(colour=member.colour)
        embed.set_image(url=choice(PAT))
        footer = (
            f"So far, {ctx.author} gave {pat_to + 1} pats to others,\n"
            + f"{'I' if member == ctx.me else member} "
            + f"received {pat_from + 1} pats in this server!"
        )
        embed.set_footer(text=footer)

        await ctx.send(content=quote(message), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def poke(self, ctx: Context, *, member: discord.Member):
        """Poke your Discord friends or strangers!"""
        if member.id == ctx.author.id:
            return await ctx.send(f"{bold(ctx.author.name)} wants to play self poke huh?!")

        await ctx.trigger_typing()
        poke_to = await self.config.member(ctx.author).POKE_TO()
        poke_from = await self.config.member(member).POKE_FROM()
        gpoke_to = await self.config.user(ctx.author).POKE_TO()
        gpoke_from = await self.config.user(member).POKE_FROM()
        await self.config.member(ctx.author).POKE_TO.set(poke_to + 1)
        await self.config.member(member).POKE_FROM.set(poke_from + 1)
        await self.config.user(ctx.author).POKE_TO.set(gpoke_to + 1)
        await self.config.user(member).POKE_FROM.set(gpoke_from + 1)
        embed = discord.Embed(colour=member.colour)
        embed = discord.Embed(colour=member.colour)
        if member.id == ctx.me.id:
            message = f"Awwww! Hey there. _pokes **{ctx.author.name}** back!_"
        else:
            message = f"_**{ctx.author.name}** casually pokes_ {member.mention}"
        embed.set_image(url=choice(POKE))
        footer = (
            f"So far, {ctx.author} gave {poke_to + 1} pokes to others,"
            + f"\n{'I' if member == ctx.me else member} received"
            + f" {poke_from + 1} pokes in this server!"
        )
        embed.set_footer(text=footer)

        await ctx.send(content=quote(message), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 30, commands.BucketType.member)
    async def punch(self, ctx: Context, *, member: discord.Member):
        """Punch someone on Discord with a GIF reaction!"""
        if member.id == ctx.me.id:
            message = (
                f"{ctx.author.mention} tried to punch a bot but failed miserably,\n"
                + "and they actually punched themselves instead.\n"
                + "How disappointing LMFAO! 😂 😂 😂"
            )
            em = discord.Embed(colour=await ctx.embed_colour())
            em.set_image(url="https://i.imgur.com/iVgOijZ.gif")
            return await ctx.send(content=message, embed=em)

        if member.id == ctx.author.id:
            return await ctx.send(
                f"I uh ..... **{ctx.author.name}**, self harm doesn't"
                + " sound so fun. Stop it, get some help."
            )

        await ctx.trigger_typing()
        punch_to = await self.config.member(ctx.author).PUNCH_TO()
        punch_from = await self.config.member(member).PUNCH_FROM()
        gpunch_to = await self.config.user(ctx.author).PUNCH_TO()
        gpunch_from = await self.config.user(member).PUNCH_FROM()
        await self.config.member(ctx.author).PUNCH_TO.set(punch_to + 1)
        await self.config.member(member).PUNCH_FROM.set(punch_from + 1)
        await self.config.user(ctx.author).PUNCH_TO.set(gpunch_to + 1)
        await self.config.user(member).PUNCH_FROM.set(gpunch_from + 1)
        embed = discord.Embed(colour=member.colour)
        message = f"_**{ctx.author.name}** {choice(PUNCH_STRINGS)}_ {member.mention}"
        embed.set_image(url=choice(PUNCH))
        footer = (
            f"So far, {ctx.author} sent {punch_to + 1} punches to others,\n"
            + f"{member} received {punch_from + 1} punches in this server!"
        )
        embed.set_footer(text=footer)

        await ctx.send(content=quote(message), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def slap(self, ctx: Context, *, member: discord.Member):
        """Slap a server member!"""
        if member.id == ctx.me.id:
            return await ctx.send("**Ｎ Ｏ   Ｕ**")

        if member.id == ctx.author.id:
            return await ctx.send(f"{ctx.author.mention} Don't slap yourself, you're precious!")

        await ctx.trigger_typing()
        slap_to = await self.config.member(ctx.author).SLAP_TO()
        slap_from = await self.config.member(member).SLAP_FROM()
        gslap_to = await self.config.user(ctx.author).SLAP_TO()
        gslap_from = await self.config.user(member).SLAP_FROM()
        await self.config.member(ctx.author).SLAP_TO.set(slap_to + 1)
        await self.config.member(member).SLAP_FROM.set(slap_from + 1)
        await self.config.user(ctx.author).SLAP_TO.set(gslap_to + 1)
        await self.config.user(member).SLAP_FROM.set(gslap_from + 1)
        embed = discord.Embed(colour=member.colour)
        message = f"_**{ctx.author.name}** slaps_ {member.mention}"
        embed.set_image(url=choice(SLAP))
        footer = (
            f"So far, {ctx.author} gave {slap_to + 1} slaps to others,\n"
            + f"{member} received {slap_from + 1} slaps in this server!"
        )
        embed.set_footer(text=footer)

        await ctx.send(content=quote(message), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def smug(self, ctx: Context):
        """Show everyone your smug face!"""
        message = f"_**{ctx.author.name}** smugs at **@\u200bsomeone**_ 😏"
        await ctx.trigger_typing()
        smug_count = await self.config.member(ctx.author).SMUG_COUNT()
        gsmug_count = await self.config.user(ctx.author).SMUG_COUNT()
        await self.config.member(ctx.author).SMUG_COUNT.set(smug_count + 1)
        await self.config.user(ctx.author).SMUG_COUNT.set(gsmug_count + 1)
        embed = discord.Embed(colour=ctx.author.colour)
        embed.set_image(url=choice(SMUG))
        footer = f"{ctx.author} has smugged {smug_count + 1} times in this server so far."
        embed.set_footer(text=footer)

        await ctx.send(content=quote(message), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def tickle(self, ctx: Context, *, member: discord.Member):
        """Try to tickle a server member!"""
        if member.id == ctx.author.id:
            return await ctx.send(
                f"{ctx.author.mention} tickling yourself is boring!"
                + " Tickling others is more fun though, right? 😏"
            )

        await ctx.trigger_typing()
        tickle_to = await self.config.member(ctx.author).TICKLE_TO()
        tickle_from = await self.config.member(member).TICKLE_FROM()
        gtickle_to = await self.config.user(ctx.author).TICKLE_TO()
        gtickle_from = await self.config.user(member).TICKLE_FROM()
        await self.config.member(ctx.author).TICKLE_TO.set(tickle_to + 1)
        await self.config.member(member).TICKLE_FROM.set(tickle_from + 1)
        await self.config.user(ctx.author).TICKLE_TO.set(gtickle_to + 1)
        await self.config.user(member).TICKLE_FROM.set(gtickle_from + 1)
        embed = discord.Embed(colour=member.colour)
        if member.id == ctx.me.id:
            message = f"_Wow, nice tickling skills, {bold(ctx.author.name)}. I LOL'd._ 🤣 🤡"
            embed.set_image(url="https://i.imgur.com/6jr50Fp.gif")
        else:
            message = f"_**{ctx.author.name}** tickles_ {member.mention}"
            embed.set_image(url=choice(TICKLE))
        footer = (
            f"So far, {ctx.author} tickled others {tickle_to + 1} times,\n"
            + f"{'I' if member == ctx.me else member} "
            + f"received {tickle_from + 1} tickles in this server!"
        )
        embed.set_footer(text=footer)

        await ctx.send(content=quote(message), embed=embed)
