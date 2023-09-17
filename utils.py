import math

from discord.ext import commands
from exceptions import NoPrivateMessages
from calendar import monthrange
import discord
import datetime


def guild_only():
    async def predicate(ctx: commands.context):
        if ctx.guild is None:
            raise NoPrivateMessages()
        return True
    return commands.check(predicate)


def permissions():
    async def predicate(ctx: commands.context):

        #check per-channel personal overwrites

        #check per-channel group overwrites

        #check global personal overwrites

        #check global group overwrites

        #check per-channel default

        #check global default

        return True
    return commands.check(predicate)


async def fetch_member(ctx: commands.context, member):
    if member is None:
        member = ctx.author
    else:
        member = await commands.MemberConverter().convert(ctx, str(member))
    return member


def delta_string_builder(start_date: datetime.datetime, end_date: datetime.datetime):
    years_delta = end_date.year - start_date.year
    months_delta = end_date.month - start_date.month
    days_delta = end_date.day - start_date.day
    hours_delta = end_date.hour - start_date.hour

    if hours_delta < 0:
        days_delta -= 1
        hours_delta %= 24

    if days_delta < 0:
        months_delta -= 1
        prev_month = end_date.replace(day=1) - datetime.timedelta(days=1)
        days_in_month = monthrange(prev_month.year, prev_month.month)[1]
        days_delta %= days_in_month

    if months_delta < 0:
        years_delta -= 1
        months_delta %= 12

    delta_string = ""

    def time_unit_append(delta_string: str, delta: int, unit: str):
        time_unit_string = ""
        if delta > 0:
            if len(delta_string) > 0:
                time_unit_string += ", "
            if delta == 1:
                time_unit_string += f"1 {unit}"
            else:
                time_unit_string += f"{delta} {unit}s"
        return time_unit_string

    for pair in ((years_delta, "year"), (months_delta, "month"), (days_delta, "day"), (hours_delta, "hour")):
        delta_string += time_unit_append(delta_string, pair[0], pair[1])

    if len(delta_string) == 0:
        return "not so long"
    else:
        return delta_string


def embed_builder(ctx: commands.Context, title="", description="", color=discord.Color.from_str("#a7f432"), image_url="", url="",
                  fields=None, footer=False):
    """fields as a tuple of 3 member tuples (name, value, inline)"""
    embed = discord.Embed(title=title, description=description, color=color, url=url)

    if image_url:
        embed.set_image(url=image_url)

    if fields:
        for el in fields:
            embed.add_field(name=el[0], value=el[1], inline=el[2])

    if footer:
        #embed.set_footer(text=f"'{ctx.prefix}{ctx.command.qualified_name}' invoked by {ctx.author.display_name}",
        #                 icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=footer)

    return embed


def is_reserved(color: discord.Color, reserved):
    """takes the color to query and the reserved colors list from the main config"""
    for entry in reserved:
        centre = discord.Color(entry["centre"])
        radius = entry["radius"]

        distance = math.sqrt((centre.r - color.r)**2 + (centre.g - color.g)**2 + (centre.b - color.b)**2)
        if distance <= radius:
            return True
    return False