from discord.ext import commands
import discord
import datetime
from utils import fetch_member
from utils import guild_only
from utils import delta_string_builder
from utils import embed_builder
import json
import aiofiles

from exceptions import ColorParsingFailure


class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # load config
        self.config = self.bot.config


    @commands.hybrid_command()
    @guild_only()
    async def joined(self, ctx, member=None):
        member = await fetch_member(ctx, member)

        join_date = member.joined_at

        await ctx.send(embed=embed_builder(ctx,
                                           title=f"{member.display_name} is with us for " +
                                                 delta_string_builder(join_date, datetime.datetime.now()) + "!",
                                           description=f"Joined on {join_date.strftime('%B')} {join_date.day}, "
                                                       f"{join_date.year} at {join_date.hour}:{join_date.strftime('%M')}."))

    @commands.hybrid_command()
    async def avatar(self, ctx, member=None):
        member = await fetch_member(ctx, member)

        embed = discord.Embed(title=f"{member.display_name}'s avatar")

        embed.set_image(url=member.display_avatar.url)

        await ctx.send(embed=embed_builder(ctx,
                                           title=f"{member.display_name}'s avatar",
                                           image_url=member.display_avatar.url))

    @commands.hybrid_group(invoke_without_command=True)
    @guild_only()
    async def color(self, ctx):
        pass

    @color.command()
    @guild_only()
    async def check(self, ctx, member=None):
        member = await fetch_member(ctx, member)

        fields = (("RGB",  f"{member.color.to_rgb()[0]}, {member.color.to_rgb()[1]}, {member.color.to_rgb()[2]}", False),
                  ("HEX", f"{str(member.color)}", False))

        await ctx.send(embed=embed_builder(ctx,
                                           title=f"{member.display_name}'s color",
                                           color=member.color,
                                           fields=fields))

    @color.command(enabled=False)
    @guild_only()
    async def set(self, ctx, color_code):
        # parse color argument...
        if not color_code[0] == "#":
            color_code = "#" + color_code

        try:
            color = discord.Color.from_str(color_code)
        except ValueError:
            raise ColorParsingFailure


        # check if a color role with this color exists - if it does return error, else proceed

        pass

    @color.command(enabled=False)
    @commands.has_permissions(administrator=True)
    async def reserve(self, ctx, color_code, radius):
        color = discord.Colour.from_str(color_code)

        self.config["reserved_colors"][color.value] = radius

        await ctx.invoke(self.config.get_command("save"))

    @commands.hybrid_command()
    async def spotify(self, ctx, member=None):
        member = await fetch_member(ctx, member)

        spotify = None

        if isinstance(member.activity, discord.Spotify):
            spotify = member.activity
        else:
            if member.activity is not None:
                for el in member.activities:
                    if isinstance(el, discord.Spotify):
                        spotify = el

        if spotify is None:
            await ctx.send(embed=embed_builder(ctx,
                                               title=f"{member.display_name} is not listening to anything",
                                               description="No listening activity detected."))
        else:
            await ctx.send(embed=embed_builder(ctx,
                                               title=f"{member.display_name} is listening to {spotify.title}",
                                               description=f"by {spotify.artist} on {spotify.album}.",
                                               image_url=spotify.album_cover_url))

    @commands.hybrid_command()
    @guild_only()
    async def icon(self, ctx):
        await ctx.send(embed=embed_builder(ctx,
                                           title=f"{ctx.guild.name}'s icon",
                                           image_url=ctx.guild.icon.url))



