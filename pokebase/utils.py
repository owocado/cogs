import random

from redbot.core import commands

BADGES = {
    "kanto": [2, 3, 4, 5, 6, 7, 8, 9],
    "johto": [10, 11, 12, 13, 14, 15, 16, 17],
    "hoenn": [18, 19, 20, 21, 22, 23, 24, 25],
    "sinnoh": [26, 27, 28, 29, 30, 31, 32, 33],
    "unova": [34, 35, 36, 37, 38, 39, 40, 41],
    "kalos": [44, 45, 46, 47, 48, 49, 50, 51],
}
INTRO_GEN = ["na", "rb", "gs", "rs", "dp", "bw", "xy", "sm", "ss"]
INTRO_GAMES = {
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
STYLES = {"default": 3, "black": 50, "collector": 96, "dp": 5, "purple": 43}
TRAINERS = {
    "ash": 13,
    "red": 922,
    "ethan": 900,
    "lyra": 901,
    "brendan": 241,
    "may": 255,
    "lucas": 747,
    "dawn": 856,
}


def get_generation(pkmn_id: int) -> int:
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


class Generation(commands.Converter):

    async def convert(self, ctx: commands.Context, argument: str) -> int:
        allowed_gens = ["gen1", "gen2", "gen3", "gen4", "gen5", "gen6", "gen7", "gen8"]
        if argument and argument not in allowed_gens:
            ctx.command.reset_cooldown(ctx)
            raise commands.BadArgument("Only `gen1` to `gen8` arguments are allowed.")

        if argument == "gen1":
            return random.randint(1, 151)
        elif argument == "gen2":
            return random.randint(152, 251)
        elif argument == "gen3":
            return random.randint(252, 386)
        elif argument == "gen4":
            return random.randint(387, 493)
        elif argument == "gen5":
            return random.randint(494, 649)
        elif argument == "gen6":
            return random.randint(650, 721)
        elif argument == "gen7":
            return random.randint(722, 809)
        elif argument == "gen8":
            return random.randint(810, 898)
        else:
            return random.randint(1, 898)