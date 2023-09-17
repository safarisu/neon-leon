from discord.ext import commands
import discord
import datetime
import re
import json
import operator
import os
import aiofiles


def count(d, name):
    if name in d:
        d[name] += 1
    else:
        d[name] = 1


def super_sort(x):
    x = sorted(x, key=operator.itemgetter(0))
    return sorted(x, key=operator.itemgetter(1), reverse=True)


class StatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def stat(self, ctx, *args):

        preset = {'limit': None}

        year = int(args[0])
        if len(args) == 2:
            month = int(args[1])
            aft_date = datetime.datetime(year, month, day=1)
            aft_date -= datetime.timedelta(seconds=1)
            bfr_date = datetime.datetime(year + month // 12, month % 12 + 1, day=1)
        else:
            month = "all"
            aft_date = datetime.datetime(year, month=1, day=1)
            aft_date -= datetime.timedelta(seconds=1)
            bfr_date = datetime.datetime(year+1, month=1, day=1)

        #aft_date.replace(tzinfo=datetime.timezone.utc)
        #bfr_date.replace(tzinfo=datetime.timezone.utc)

        filename = '{}_{}'.format(month, year)
        preset['after'] = aft_date
        preset['before'] = bfr_date

        total, pp_member, pp_channel, pp_day = 0, {}, {}, {}
        errors = 0
        guild_emojis = {emoji.name: 0 for emoji in ctx.guild.emojis}
        pattern = r':(.*?):'
        p = re.compile(pattern)

        print('Start counting...')
        print(ctx.guild.text_channels)

        for channel in ctx.guild.text_channels:
            print(channel.name)
            counter = 0
            async for message in channel.history(**preset):
                try:
                    try:
                        member = message.author.nick
                        assert member is not None
                    except (AttributeError, AssertionError):
                        member = message.author.name

                    mid = message.author.id

                    if mid not in pp_member:
                        pp_member[mid] = [member, 1]
                    else:
                        pp_member[mid][1] += 1

                    matches = p.findall(message.content)
                    for match in matches:
                        if match in guild_emojis:
                            guild_emojis[match] += 1

                    dt = message.created_at
                    #dt_aware = dt.replace(tzinfo=datetime.timezone.utc)
                    #dt_gmt1 = dt_aware.astimezone(GMT1())
                    #day = dt_gmt1.date().isoformat()
                    
                    day = dt.date().isoformat()

                    count(pp_day, day)

                except Exception:
                    errors += 1
                    pass

                finally:
                    total += 1
                    counter += 1
                    print(f'{message.channel}|{message.author}|{message.created_at}|{message.content[:10]}')
                    if counter % 1000 == 0:
                        print(counter)

            print(f'out of {channel.name}')
            pp_channel[channel.name] = counter

        print(errors)

        stats = {'total': total,
                 'pp_member': pp_member,
                 'pp_channel': pp_channel,
                 'pp_day': pp_day,
                 'emojis': guild_emojis}

        with open(filename + ".json", 'w+', encoding='utf-8') as file_json:
            json.dump(stats, file_json, ensure_ascii=False)
            file_json_name = file_json.name

        await ctx.send(file=discord.File(file_json_name))
        os.remove(file_json_name)

        stat_total = total

        stat_members = list(pp_member.values())
        stat_members = super_sort(stat_members)

        stat_channels = [[x, pp_channel[x]] for x in pp_channel]
        stat_channels = super_sort(stat_channels)

        stat_days = [[x, pp_day[x]] for x in pp_day]
        stat_days = super_sort(stat_days)

        stat_emojis = [[x, guild_emojis[x]] for x in guild_emojis]
        stat_emojis = super_sort(stat_emojis)

        with open(filename + ".txt", 'w+', encoding='utf-8') as file_text:
            file_text.write("total:{}\n".format(stat_total))
            file_text.write("\n")

            for i in [stat_members, stat_channels, stat_days, stat_emojis]:
                for l in i:
                    file_text.write("{}:{}\n".format(l[0], l[1]))
                file_text.write("\n")
            file_text_name = file_text.name

        await ctx.send(file=discord.File(file_text_name))

        print('Done.')

        os.remove(file_text_name)

    @commands.command()
    async def posts(self, ctx, *args):
        pass

    @commands.command()
    async def print_time(self, ctx):
        now_utc = datetime.datetime.now(tz=datetime.timezone.utc)
        #now = now_utc.astimezone(GMT1())
        await ctx.send(now.hour)


def setup(bot):
    bot.add_cog(StatCog(bot))
