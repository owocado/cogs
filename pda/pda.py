from random import choice

import discord
from redbot.core import Config, commands
from redbot.core.commands import Context
from redbot.core.utils.chat_formatting import bold, italics, quote

from .constants import *


class PDA(commands.Cog):
    """Do roleplay with your Discord friends or virtual strangers."""

    __author__ = "siu3334 (<@306810730055729152>)"
    __version__ = "0.2.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 123456789987654321, force_registration=True)
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
            "SMUG_TO": 0,
            "SMUG_FROM": 0,
            "TICKLE_TO": 0,
            "TICKLE_FROM": 0
        }
        self.config.register_member(**default_user)
        self.config.register_user(**default_user)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def baka(self, ctx: Context, *, member: discord.Member):
        """Call someone a BAKA with a GIF reaction!"""
        if member.id == ctx.me.id:
            message = "**Ｎ Ｏ   Ｕ**"
            return await ctx.send(message)

        if member.id == ctx.author.id:
            message = f"{bold(ctx.author.name)}, you really are BAKA. Stupid!! 💩"
            return await ctx.send(message)

        async with ctx.typing():
            baka_to = await self.config.member(ctx.author).BAKA_TO()
            baka_from = await self.config.member(member).BAKA_FROM()
            gbaka_to = await self.config.user(ctx.author).BAKA_TO()
            gbaka_from = await self.config.user(member).BAKA_FROM()
            await self.config.member(ctx.author).BAKA_TO.set(baka_to + 1)
            await self.config.member(member).BAKA_FROM.set(baka_from + 1)
            await self.config.user(ctx.author).BAKA_TO.set(gbaka_to + 1)
            await self.config.user(member).BAKA_FROM.set(gbaka_from + 1)
            embed = discord.Embed(colour=member.colour)
            message = f"{bold(ctx.author.name)} calls {member.mention} a BAKA bahahahahaha!!!"
            embed.set_image(url=choice(BAKA))
            footer = (
                f"{ctx.author} called {baka_to} people a BAKA, {member} got called "
                + f"a BAKA {baka_from} times by others in this server so far."
            )
            embed.set_footer(text=footer)

        await ctx.send(content=quote(italics(message)), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 90, commands.BucketType.member)
    async def bully(self, ctx: Context, *, member: discord.Member):
        """Bully someone in this server with a funny GIF!"""
        if member.id == ctx.me.id:
            message = "**Ｎ Ｏ   Ｕ**"
            return await ctx.send(message)

        if member.id == ctx.author.id:
            message = f"{ctx.author.mention} Self bullying doesn't make sense. Stop it, get some help."
            return await ctx.send(message)

        async with ctx.typing():
            bully_to = await self.config.member(ctx.author).BULLY_TO()
            bully_from = await self.config.member(member).BULLY_FROM()
            gbully_to = await self.config.user(ctx.author).BULLY_TO()
            gbully_from = await self.config.user(member).BULLY_FROM()
            await self.config.member(ctx.author).BULLY_TO.set(bully_to + 1)
            await self.config.member(member).BULLY_FROM.set(bully_from + 1)
            await self.config.user(ctx.author).BULLY_TO.set(gbully_to + 1)
            await self.config.user(member).BULLY_FROM.set(gbully_from + 1)
            embed = discord.Embed(colour=member.colour)
            message = f"{bold(ctx.author.name)} bullies {member.mention} 🤡"
            embed.set_image(url=choice(BULLY))
            footer = (
                f"{ctx.author} bullied {bully_to} people, {member} "
                + f"got bullied {bully_from} times so far in this server."
            )
            embed.set_footer(text=footer)

        await ctx.send(content=quote(italics(message)), embed=embed)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def cry(self, ctx: Context):
        """Let others know that you feel like crying or just wanna cry."""
        async with ctx.typing():
            cry_count = await self.config.member(ctx.author).CRY_COUNT()
            gcry_count = await self.config.user(ctx.author).CRY_COUNT()
            await self.config.member(ctx.author).CRY_COUNT.set(cry_count + 1)
            await self.config.user(ctx.author).CRY_COUNT.set(gcry_count + 1)
            embed = discord.Embed(colour=ctx.author.colour)
            embed.description = f"{ctx.author.mention} {choice(CRY_STRINGS)}"
            embed.set_image(url=choice(CRY))
            footer = f"{ctx.author} has cried {cry_count} times so far in this server."
            embed.set_footer(text=footer)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def cuddle(self, ctx: Context, *, member: discord.Member):
        """Cuddle with a server member!"""
        if member.id == ctx.me.id:
            return await ctx.send(f"Awww thanks, {bold(ctx.author.name)}! Very kind of you. 😳")

        if member.id == ctx.author.id:
            message = (
                f"{ctx.author.mention} According to all known laws of roleplay, there is no way you "
                + "can cuddle yourself! Go cuddle with someone... or a pillow, if you're lonely like me. 😔"
            )
            return await ctx.send(message)

        async with ctx.typing():
            cuddle_to = await self.config.member(ctx.author).CUDDLE_TO()
            cuddle_from = await self.config.member(member).CUDDLE_FROM()
            gcuddle_to = await self.config.user(ctx.author).CUDDLE_TO()
            gcuddle_from = await self.config.user(member).CUDDLE_FROM()
            await self.config.member(ctx.author).CUDDLE_TO.set(cuddle_to + 1)
            await self.config.member(member).CUDDLE_FROM.set(cuddle_from + 1)
            await self.config.user(ctx.author).CUDDLE_TO.set(gcuddle_to + 1)
            await self.config.user(member).CUDDLE_FROM.set(gcuddle_from + 1)
            embed = discord.Embed(colour=member.colour)
            message = f"{bold(ctx.author.name)} cuddles {member.mention}"
            embed.set_image(url=str(choice(CUDDLE)))
            footer = (
                f"{ctx.author} cuddled {cuddle_to} people, {member} "
                + f"received {cuddle_from} cuddles so far in this server."
            )
            embed.set_footer(text=footer)

        await ctx.send(content=quote(italics(message)), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def feed(self, ctx: Context, *, member: discord.Member):
        """Feed someone from this server virtually!"""
        if member.id == ctx.me.id:
            message = f"OWO! Yummy food... Thanks much, {bold(ctx.author.name)}! ❤️"
            return await ctx.send(message)

        async with ctx.typing():
            feed_to = await self.config.member(ctx.author).FEED_TO()
            feed_from = await self.config.member(member).FEED_FROM()
            gfeed_to = await self.config.user(ctx.author).FEED_TO()
            gfeed_from = await self.config.user(member).FEED_FROM()
            await self.config.member(ctx.author).FEED_TO.set(feed_to + 1)
            await self.config.member(member).FEED_FROM.set(feed_from + 1)
            await self.config.user(ctx.author).FEED_TO.set(gfeed_to + 1)
            await self.config.user(member).FEED_FROM.set(gfeed_from + 1)
            embed = discord.Embed(colour=member.colour)
            message = f"{bold(ctx.author.name)} feeds {member.mention} some delicious food!"
            embed.set_image(url=choice(FEED))
            footer = (
                f"{ctx.author} have fed {feed_to} people, {member} was fed "
                + f"some food from {feed_from} people so far in this server."
            )
            embed.set_footer(text=footer)

        await ctx.send(content=quote(italics(message)), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def highfive(self, ctx: Context, *, member: discord.Member):
        """High-fives a user!"""
        if member.id == ctx.author.id:
            message = f"{ctx.author.mention} high-fives themselves in mirror, I guess?"
            return await ctx.send(italics(message))

        async with ctx.typing():
            h5_to = await self.config.member(ctx.author).HIGHFIVE_TO()
            h5_from = await self.config.member(member).HIGHFIVE_FROM()
            gh5_to = await self.config.user(ctx.author).HIGHFIVE_TO()
            gh5_from = await self.config.user(member).HIGHFIVE_FROM()
            await self.config.member(ctx.author).HIGHFIVE_TO.set(h5_to + 1)
            await self.config.member(member).HIGHFIVE_FROM.set(h5_from + 1)
            await self.config.user(ctx.author).HIGHFIVE_TO.set(gh5_to + 1)
            await self.config.user(member).HIGHFIVE_FROM.set(gh5_from + 1)
            embed = discord.Embed(colour=member.colour)
            message = f"{bold(ctx.author.name)} high fives {member.mention}"
            embed.set_image(url=choice(HIGHFIVE))
            footer = (
                f"{ctx.author} high-five'd {h5_to} people, {member} "
                + f"received {h5_from} high-fives so far in this server."
            )
            embed.set_footer(text=footer)

        await ctx.send(content=quote(italics(message)), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def hugs(self, ctx: Context, *, member: discord.Member):
        """Hug a user virtually on Discord!"""
        if member.id == ctx.me.id:
            message = f"Awwww thanks! So nice of you! *hugs {bold(ctx.author.name)} back* 🤗"
            return await ctx.send(message)

        if member.id == ctx.author.id:
            message = f"{ctx.author.mention} One dOEs NOt SiMplY hUg THeIR oWn sELF!!!!!"
            return await ctx.send(message)

        async with ctx.typing():
            hug_to = await self.config.member(ctx.author).HUG_TO()
            hug_from = await self.config.member(member).HUG_FROM()
            ghug_to = await self.config.user(ctx.author).HUG_TO()
            ghug_from = await self.config.user(member).HUG_FROM()
            await self.config.member(ctx.author).HUG_TO.set(hug_to + 1)
            await self.config.member(member).HUG_FROM.set(hug_from + 1)
            await self.config.user(ctx.author).HUG_TO.set(ghug_to + 1)
            await self.config.user(member).HUG_FROM.set(ghug_from + 1)
            embed = discord.Embed(colour=member.colour)
            message = f"{bold(ctx.author.name)} hugs {member.mention} 🤗"
            embed.set_image(url=str(choice(HUG)))
            footer = (
                f"{ctx.author} hugged {hug_to} people, {member} "
                + f" received {hug_from} hugs so far in this server!"
            )
            embed.set_footer(text=footer)

        await ctx.send(content=quote(italics(message)), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 90, commands.BucketType.member)
    async def kill(self, ctx: Context, *, member: discord.Member):
        """Virtually attempt to kill a server member with a GIF reaction!"""
        if member.id == ctx.me.id:
            message = "**Ｎ Ｏ   Ｕ**"
            return await ctx.send(content=message)

        if member.id == ctx.author.id:
            message = f"{ctx.author.mention} Seppukku is not allowed on my watch. 💀"
            return await ctx.send(message)

        async with ctx.typing():
            kill_to = await self.config.member(ctx.author).KILL_TO()
            kill_from = await self.config.member(member).KILL_FROM()
            gkill_to = await self.config.user(ctx.author).KILL_TO()
            gkill_from = await self.config.user(member).KILL_FROM()
            await self.config.member(ctx.author).KILL_TO.set(kill_to + 1)
            await self.config.member(member).KILL_FROM.set(kill_from + 1)
            await self.config.user(ctx.author).KILL_TO.set(gkill_to + 1)
            await self.config.user(member).KILL_FROM.set(gkill_from + 1)
            embed = discord.Embed(colour=member.colour)
            message = f"🇫 {bold(ctx.author.name)} tries to kill {member.mention}"
            embed.set_image(url=choice(KILL))
            footer = (
                f"{ctx.author} tried to kill {kill_to} people, {member} "
                + f"got killed {kill_from} times so far in this server!"
            )
            embed.set_footer(text=footer)

        await ctx.send(content=quote(italics(message)), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def kiss(self, ctx: Context, *, member: discord.Member):
        """[NSFW] Kiss a user! Only allowed in NSFW channel."""
        if not ctx.channel.is_nsfw():
            return await ctx.send("NSFW command blocked in non NSFW channel.")

        if member.id == ctx.me.id:
            message = f"Awwww! *kisses {ctx.author.mention} back!* 😘 🥰"
            return await ctx.send(message)

        if member.id == ctx.author.id:
            message = f"Congratulations {bold(ctx.author.name)}, you just kissed yourself! LOL!!! 💋"
            return await ctx.send(message)

        async with ctx.typing():
            kiss_to = await self.config.member(ctx.author).KISS_TO()
            kiss_from = await self.config.member(member).KISS_FROM()
            gkiss_to = await self.config.user(ctx.author).KISS_TO()
            gkiss_from = await self.config.user(member).KISS_FROM()
            await self.config.member(ctx.author).KISS_TO.set(kiss_to + 1)
            await self.config.member(member).KISS_FROM.set(kiss_from + 1)
            await self.config.user(ctx.author).KISS_TO.set(gkiss_to + 1)
            await self.config.user(member).KISS_FROM.set(gkiss_from + 1)
            embed = discord.Embed(colour=member.colour)
            message = f"{bold(ctx.author.name)} kisses {member.mention} 😘 🥰"
            embed.set_image(url=str(choice(KISS)))
            footer = (
                f"{ctx.author} have kissed {kiss_to} people, {member} "
                + f"received {kiss_from} kisses so far in this server!"
            )
            embed.set_footer(text=footer)

        await ctx.send(content=quote(italics(message)), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def lick(self, ctx: Context, *, member: discord.Member):
        """[NSFW] Lick a user! Only allowed in NSFW channel."""
        if not ctx.channel.is_nsfw():
            return await ctx.send("NSFW command blocked in non NSFW channel.")

        if member.id == ctx.me.id:
            message = f"{ctx.author.mention} You wanna lick a bot? Very horny!"
            return await ctx.send(message)

        async with ctx.typing():
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
                f"{ctx.author.mention} Bravo, you just licked yourself. 👏"
                if member.id == ctx.author.id
                else f"{ctx.author.mention} licks {member.mention} 😳"
            )
            embed.set_image(url=choice(LICK))
            footer = (
                f"{ctx.author} have licked {lick_to} people, {member} "
                + f"got licked {lick_from} times so far in this server!"
            )
            embed.set_footer(text=footer)

        await ctx.send(content=quote(italics(message)), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def nom(self, ctx: Context, *, member: discord.Member):
        """Try to nom/bite a server member!"""
        if member.id == ctx.me.id:
            return await ctx.send(f"**OH NO!** _runs away_")
        embed = discord.Embed(colour=member.colour)
        if member.id != ctx.author:
            message = f"{ctx.author.mention} casually noms {member.mention} 😈"
        else:
            message = f"Waaaaaa! {bold(ctx.author.name)}, You bit yourself! Whyyyy?? 😭"
        embed.set_image(url=choice(BITE))
        await ctx.send(content=quote(italics(message)), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def pat(self, ctx: Context, *, member: discord.Member):
        """Pats a user!"""

        embed = discord.Embed(colour=member.colour)
        if member.id == ctx.me.id:
            message = f"{ctx.author.mention} pats {member.mention}"
        else:
            message = f"{ctx.author.mention} pats themselves, I guess?"
        embed.set_image(url=choice(PAT))
        await ctx.send(content=quote(italics(message)), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def poke(self, ctx: Context, *, member: discord.Member):
        """Pokes a user!"""

        if member.id == ctx.me.id:
            message = f"Awwww! Hey there. *pokes {ctx.author.mention} back! touchy touchy*"
            return await ctx.send(message)
        if member.id != ctx.author.id:
            embed = discord.Embed(colour=member.colour)
            message = f"{ctx.author.mention} casually pokes {member.mention}"
            embed.set_image(url=choice(POKE))
            return await ctx.send(content=quote(italics(message)), embed=embed)
        else:
            message = f"{ctx.author.mention} self-poking is widely regarded as a bad move!"
            await ctx.send(message)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 30, commands.BucketType.member)
    async def punch(self, ctx: Context, *, member: discord.Member):
        """Punch a user with a GIF reaction!"""

        if member.id == ctx.me.id:
            message = (
                ctx.author.mention
                + " tried to punch a bot but failed miserably"
                + " and they actually punched themselves instead."
                + " How disappointing LMFAO! 😂"
            )
            em = discord.Embed(colour=await ctx.embed_colour())
            em.set_image(url="https://media1.tenor.com/images/c20ffecdd8cca7f0ce9c4a670d5f7ff0/tenor.gif")
            return await ctx.send(content=message, embed=em)
        if member.id != ctx.author.id:
            embed = discord.Embed(colour=member.colour)
            message = f"{ctx.author.mention} {choice(PUNCH_STRINGS)} {member.mention}"
            embed.set_image(url=choice(PUNCH))
            return await ctx.send(content=quote(italics(message)), embed=embed)
        else:
            message = f"I uh ..... **{ctx.author.name}**, self harm doesn't sound so fun. Stop it, get some help."
            await ctx.send(message)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def slap(self, ctx: Context, *, member: discord.Member):
        """Slaps a user!"""

        if member.id == ctx.me.id:
            message = "**Ｎ Ｏ   Ｕ**"
            return await ctx.send(message)
        if member.id != ctx.author.id:
            embed = discord.Embed(colour=member.colour)
            message = f"{ctx.author.mention} slaps {member.mention}"
            embed.set_image(url=choice(SLAP))
            return await ctx.send(content=quote(italics(message)), embed=embed)
        else:
            message = f"Don't slap yourself, you're precious! {ctx.author.mention}"
            await ctx.send(message)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def smug(self, ctx: Context, *, member: discord.Member = None):
        """Be smug towards someone!"""

        embed = discord.Embed(colour=ctx.author.colour)
        if not member:
            message = f"{ctx.author.mention} smugs at **@\u200bsomeone** 😏"
        else:
            message = f"{ctx.author.mention} smugs at {member.mention} 😏"
        embed.set_image(url=choice(SMUG))
        await ctx.send(content=quote(italics(message)), embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def tickle(self, ctx: Context, *, member: discord.Member):
        """Tickles a user!"""

        if member.id == ctx.me.id:
            message = F"LOL. Tickling a bot now, are we? {ctx.author.mention} 🤣 🤡"
            return await ctx.send(message)
        if member.id != ctx.author.id:
            embed = discord.Embed(colour=member.colour)
            message = f"{ctx.author.mention} tickles {member.mention}"
            embed.set_image(url=choice(TICKLE))
            return await ctx.send(content=quote(italics(message)), embed=embed)
        else:
            message = (
                f"{ctx.author.mention} tickling yourself is boring!"
                + " Tickling others is more fun though, right? 😏"
            )
            await ctx.send(message)
