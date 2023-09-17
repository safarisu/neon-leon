from discord.ext import commands
import aiosqlite
import datetime
import aiofiles
import discord
from exceptions import InsufficientFunds
from utils import embed_builder
import calendar


async def test_connection(db_file):
    conn = None
    try:
        conn = await aiosqlite.connect(db_file)
        print("Connected to aiosqlite " + aiosqlite.sqlite_version)
    except aiosqlite.Error as e:
        print(e)
    finally:
        if conn:
            await conn.close()


def adapt_datetime_epoch(val):
    """Adapt datetime.datetime to Unix timestamp."""
    return int(val.timestamp())


def convert_timestamp(val):
    """Convert Unix epoch timestamp to datetime.datetime object."""
    return datetime.datetime.fromtimestamp(int(val))


def adapt_date_iso(val):
    """Adapt datetime.date to ISO 8601 date."""
    return val.isoformat()


def convert_date(val):
    """Convert ISO 8601 date to datetime.date object."""
    return datetime.date.fromisoformat(val.decode())


def month_string():
    now = datetime.datetime.utcnow()
    month = str(now.month)
    year = str(now.year)

    if now.month < 10:
        month = "0" + month

    return year + "_" + month


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config
        self.db_file = "db/" + str(self.config["server_id"]) + ".db"
        self.conn = aiosqlite.connect(self.db_file)
        aiosqlite.register_adapter(datetime.date, adapt_date_iso)
        aiosqlite.register_adapter(datetime.datetime, adapt_datetime_epoch)
        aiosqlite.register_converter("date", convert_date)
        aiosqlite.register_converter("timestamp", convert_timestamp)

    async def cog_load(self):
        await test_connection(self.db_file)
        await self._populate()
        await self._count_posts()

    async def _populate(self):
        create_accounts_table = """ CREATE TABLE IF NOT EXISTS accounts (
                                        id integer PRIMARY KEY,
                                        user_id integer NOT NULL UNIQUE,
                                        balance real,
                                        private integer
                                    ); """

        create_roles_table = """ CREATE TABLE IF NOT EXISTS roles (
                                        id integer PRIMARY KEY,
                                        role_id integer NOT NULL UNIQUE,
                                        owner integer,
                                        subscription integer,
                                        last_paid timestamp 
                                    ); """

        create_timestamps_table = """ CREATE TABLE IF NOT EXISTS timestamps (
                                        id integer PRIMARY KEY,
                                        name text UNIQUE,
                                        ts timestamp
                                    ); """

        create_posts_table = f""" CREATE TABLE IF NOT EXISTS posts (
                                                id integer PRIMARY KEY,
                                                msg_id integer,
                                                user_id integer,
                                                user_name text,
                                                channel_id integer,
                                                channel_name text,
                                                content text,
                                                attachments text,
                                                datetime datetime
                                            ); """

        create_issues_table = f""" CREATE TABLE IF NOT EXISTS issues (
                                                id integer PRIMARY KEY,
                                                receiver_id integer,
                                                amount real,
                                                title text,
                                                ts timestamp
                                            ); """

        create_transactions_table = """ CREATE TABLE IF NOT EXISTS transactions (
                                        id integer PRIMARY KEY,
                                        sender_id integer,
                                        receiver_id integer,
                                        amount real,
                                        title text,
                                        ts timestamp
                                    ); """

        create_stocks_table = """ CREATE TABLE IF NOT EXISTS stocks (
                                        id integer PRIMARY KEY,
                                        owner_id integer,
                                        stock text,
                                        shares real,
                                        private integer
                                    ); """

        try:
            async with aiosqlite.connect(self.db_file) as conn:
                cur = await conn.cursor()
                await cur.execute(create_accounts_table)
                await cur.execute(create_roles_table)
                await cur.execute(create_timestamps_table)
                await cur.execute(create_posts_table)
                await cur.execute(create_transactions_table)
                await cur.execute(create_issues_table)
                await cur.execute(create_stocks_table)

                #initialize timestamps
                await cur.execute("SELECT * FROM timestamps WHERE name='last_logged'")
                row = await cur.fetchone()
                date = datetime.datetime(year=2016, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                ts = date.timestamp()
                if not row:
                    await cur.execute("INSERT INTO timestamps(name, ts) VALUES (?,?)", ("last_logged", ts))

                #initialize tax presets
                for preset in self.config["tax_preset"]:
                    await cur.execute("SELECT * FROM stocks WHERE owner_id=? AND stock=?", (self.config["central_bank"], preset))
                    row = await cur.fetchone()
                    if not row:
                        await cur.execute("INSERT INTO stocks (owner_id, stock, shares, private) VALUES (?, ?, ?, ?)",
                                          (self.config["central_bank"],
                                           preset,
                                           self.config["tax_preset"][preset],
                                           1))
                await conn.commit()
        except aiosqlite.Error as e:
            print(e)

    async def _log_msg(self, message: discord.Message, cur):
        '''Logs the message in the database'''

        msg_id = message.id
        user_id = message.author.id
        user_name = message.author.display_name
        channel_id = message.channel.id
        channel_name = message.channel.name
        content = message.content
        attachment = str(message.attachments)
        date = message.created_at

        sql = f"INSERT INTO posts(msg_id, user_id, user_name, channel_id, channel_name, content, attachments, datetime) VALUES (?,?,?,?,?,?,?,?)"
        await cur.execute(sql, (msg_id, user_id, user_name, channel_id, channel_name, content, attachment, date))

        await cur.execute(f"SELECT ts FROM timestamps WHERE name='last_logged'")
        row = await cur.fetchone()
        if date.timestamp() >= row[0]:
            await cur.execute("UPDATE timestamps SET ts=? WHERE name='last_logged'", (date.timestamp(),))

        # sql = f"SELECT * FROM posts WHERE user_id=? AND channel_id=? AND day=?"
        # await cur.execute(sql, (message.author.id, message.channel.id, message.created_at.date()))
        # row = await cur.fetchone()
        #
        # if row:
        #     sql = f"UPDATE posts SET count=count+1 WHERE user_id=? AND channel_id=? AND day=?"
        #     await cur.execute(sql, (message.author.id, message.channel.id, message.created_at.date()))
        # else:
        #     sql = f"INSERT INTO posts(user_id, channel_id, day, count) VALUES (?,?,?,?)"
        #     await cur.execute(sql, (message.author.id, message.channel.id, message.created_at.date(), 1))
        #
        # date = message.created_at
        # ts = date.timestamp()


    async def _issue_log(self, cur, receiver_id, amount, title, ts):
        '''Logs the issue in the databatase'''
        if title == "FREE_PRINT":
            sql = f"INSERT INTO issues(receiver_id, amount, title, ts)" \
                      f"VALUES(?,?,?,?)"
            await cur.execute(sql, (receiver_id, amount, title, ts))

        else:
            sql = f"SELECT * FROM issues WHERE receiver_id=? AND title='{title} AND ts={ts}'"
            await cur.execute(sql, (receiver_id,))
            row = await cur.fetchone()
            if row:
                sql = f"UPDATE issues SET amount=amount+? WHERE receiver_id=? AND title='{title} AND ts={ts}'"
                await cur.execute(sql, (amount, receiver_id))
            else:
                sql = f"INSERT INTO issues(receiver_id, amount, title, ts) VALUES(?,?,?,?)"
                await cur.execute(sql, (receiver_id, amount, title, ts))

    async def _print(self, cur, receiver_id, amount, ts, title="FREE PRINT"):
        await self._check_account(receiver_id, cur)
        await cur.execute("UPDATE accounts SET balance=round(balance+?, 6) WHERE user_id=?", (amount, receiver_id))

        await self._issue_log(cur, receiver_id, amount, title, ts)

    async def _ren_msg(self, message: discord.Message, cur):
        '''Renumerates author and shareholders for the message'''
        day = message.created_at.date()
        ts = message.created_at.timestamp()
        if str(message.channel.id) in list(self.config["stocks"].keys()):
            stock = self.config["stocks"][str(message.channel.id)]
        else:
            stock = "default"

        await cur.execute("SELECT * FROM stocks WHERE stock=?", (stock,))
        rows = await cur.fetchall()
        dividend_sum = 0

        for row in rows:
            shares = row[3]
            owner_id = row[1]
            dividend_sum += shares/1000
            await self._print(cur, owner_id, shares/1000, ts, title="DIVIDEND")

        author_fee = self.config["base_reward"] - dividend_sum
        await self._print(cur, message.author.id, author_fee, ts, title="ACTIVITY")

    async def _count_posts(self, before_message=False):
        async with aiosqlite.connect(self.db_file) as conn:
            cur = await conn.cursor()
            await cur.execute("SELECT ts FROM timestamps WHERE name='last_logged'")
            row = await cur.fetchone()

            last_logged = datetime.datetime.fromtimestamp(row[0])

            now = datetime.datetime.now()

            td = now - last_logged

            # if td < datetime.timedelta(minutes=10):
            #     return

            guild_id = self.config["server_id"]
            # guild = self.bot.get_guild(guild_id)
            guild = await self.bot.fetch_guild(guild_id)
            channels = await guild.fetch_channels()
            # print(channels)
            text_channels = []

            for channel in channels:
                if type(channel) is discord.TextChannel:
                    text_channels.append(channel)

            total_count = 0
            for channel in text_channels:
                count = 0
                print(f"Counting posts from the channel: {channel.name}...")
                async for message in channel.history(limit=None, after=last_logged, before=now):
                    await self._log_msg(message, cur)
                    await self._ren_msg(message, cur)

                    content = message.content
                    words = content.split()

                    for word in words:
                        if word.lower() in self.config["banned_words"].split(",") or word.lower() + "s" in self.config["banned_words"]:
                            try:
                                await message.delete()
                                print(f'''Deleting message: {message.content}\nBanned word: {word}''')
                            except Exception:
                                print(Exception)

                    count += 1
                    total_count += 1
                    if count % 1000 == 0:
                        print(f"{count}")
            await conn.commit()

            print(f"Done. {total_count} posts counted.")

    async def _check_account(self, user_id, cur):
        await cur.execute("SELECT * FROM accounts WHERE user_id=?", (user_id,))
        row = await cur.fetchone()

        if not row:
            await cur.execute("INSERT INTO accounts(user_id, balance, private)"
                              "VALUES(?,?,?)", (user_id, 0, 0))

    async def _check_balance(self, user_id, cur):
        await cur.execute("SELECT balance FROM accounts WHERE user_id=?", (user_id,))

        row = await cur.fetchone()

        if row:
            return row[0]
        else:
            return 0

    async def _transfer(self, sender_id, receiver_id, amount, title):
        async with aiosqlite.connect(self.db_file) as conn:
            cur = await conn.cursor()

            await self._check_account(sender_id, cur)
            await self._check_account(receiver_id, cur)
            sender_balance = await self._check_balance(sender_id, cur)
            # receiver_balance = await self._check_balance(receiver_id, amount)

            if sender_balance < amount:
                raise InsufficientFunds
            await cur.execute("UPDATE accounts SET balance=round(balance-?, 6) WHERE user_id=?", (amount, sender_id))
            await cur.execute("UPDATE accounts SET balance=round(balance+?, 6) WHERE user_id=?", (amount, receiver_id))
            await cur.execute("INSERT INTO transactions(sender_id, receiver_id, amount, title, ts)"
                              "VALUES(?, ?, ?, ?, ?)", (sender_id, receiver_id, amount, title,
                                                        datetime.datetime.utcnow().timestamp()))
            await conn.commit()

    async def _grant_shares(self, receiver_id, stock, shares, private):
        async with aiosqlite.connect(self.db_file) as conn:
            cur = await conn.cursor()

            await cur.execute("SELECT * FROM stocks WHERE owner_id=? AND stock=?", (receiver_id, stock))
            row = await cur.fetchone()

            if not row:
                await cur.execute("INSERT INTO stocks(owner_id, stock, shares, private) VALUES(?, ?, ?, ?)",
                                  (receiver_id, stock, shares, private))
            else:
                await cur.execute("UPDATE stocks SET shares=shares+? WHERE owner_id=? AND stock=?",
                                  (shares, receiver_id, stock))
            await conn.commit()


    # @commands.Cog.listener()
    # async def on_message(self, ctx):
    #     async with aiosqlite.connect(self.db_file) as conn:
    #         cur = await conn.cursor()
    #         await self._log_msg(ctx, cur)
    #         await self._ren_msg(ctx, cur)
    #         await conn.commit()

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def _set_timestamps(self, ctx):
        async with aiosqlite.connect(self.db_file) as conn:
            cur = await conn.cursor()
            now = datetime.datetime.utcnow()
            first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            before_month = first_day - datetime.timedelta(seconds=1)
            bfr_ts = before_month.timestamp()
            # now_ts = now.timestamp()

            await cur.execute("INSERT INTO timestamps(name, ts) VALUES (?,?)", ("last_logged", bfr_ts))
            # await cur.execute("INSERT INTO timestamps(name, ts) VALUES (?,?)", ("last_settled", now_ts))
            await conn.commit()

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def push_db(self, ctx):
        attachment = ctx.message.attachments[0]

        async with aiofiles.open(self.db_file, mode="w") as f:
            await attachment.save(f)

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def pop_db(self, ctx):
        async with aiofiles.open(self.db_file, mode="w") as f:
            await ctx.send(file=f)

    @commands.hybrid_command()
    async def balance(self, ctx):
        # checks accounts balance
        user_id = ctx.author.id

        async with aiosqlite.connect(self.db_file) as conn:
            cur = await conn.cursor()
            balance = await self._check_balance(user_id, cur)

        await ctx.send(embed=embed_builder(ctx,
                                           title="Your balance:",
                                           description=f"{balance} DMC :money_mouth:"))

    @commands.hybrid_command()
    @commands.has_any_role("MODE", "J MODE")
    async def transfer(self, ctx, sender: discord.Member, receiver: discord.Member, amount: float, title="TRANSFER"):
        # transfers dmc to the target
        sender_id = sender.id
        receiver_id = receiver.id

        await self._transfer(sender_id, receiver_id, abs(amount), title)

        await ctx.send(embed=embed_builder(ctx,
                                           title="Transfer successful",
                                           description=f"{amount} DMC successfully transferred from {sender.display_name} "
                                                       f"to {receiver.display_name}."))

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def print(self, ctx, receiver: discord.Member, amount: float):
        receiver_id = receiver.id

        async with aiosqlite.connect(self.db_file) as conn:
            cur = await conn.cursor()
            day = ctx.message.created_at.date()
            await self._print(cur, receiver_id, abs(amount), day)

        await ctx.send(embed=embed_builder(ctx,
                                           title="Money printer go BRRR",
                                           description=f"{amount} DMC printed for {receiver.display_name}."))

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def grant_shares(self, ctx, receiver: discord.Member, stock: str, no_shares: float, private=0):
        receiver_id = receiver.id

        await self._grant_shares(receiver_id, stock, no_shares, private)

        await ctx.send(embed=embed_builder(ctx,
                                           title="Shares granted",
                                           description=f"{no_shares} shares of {stock} granted to"
                                                       f" {receiver.display_name}"))

    @commands.hybrid_command()
    async def postsboard(self, ctx, year=None, month=None):
        posts_string = ""

        if year is None and month is None:
            posts_string = "posts_" + month_string()
        else:
            return

        async with aiosqlite.connect(self.db_file) as conn:
            cur = await conn.cursor()
            sql = f"SELECT * FROM {posts_string}"
            await cur.execute(sql)
            rows = await cur.fetchall()

        if not rows:
            return

        total_monthly_count = 0
        users_monthly_count = {}

        for row in rows:
            total_monthly_count += row[4]
            if row[1] in users_monthly_count:
                users_monthly_count[row[1]] += row[4]
            else:
                users_monthly_count[row[1]] = row[4]

        users_sorted = sorted(users_monthly_count.items(), key=lambda item: item[1], reverse=True)
        users_top10 = users_sorted[:10]

        i = 1

        fields_top10 = []

        for entry in users_top10:
            user = await self.bot.fetch_user(entry[0])
            display_name = user.display_name
            fields_top10.append((f"{i}. " + display_name, entry[1], False))
            i += 1

        month = calendar.month_name[int(month_string().split("_")[1])]
        year = month_string().split("_")[0]

        title = f"Top 10 {month} {year}"

        author_rank = None
        author_post_count = None
        description = ""

        for user in users_sorted:
            if user[0] == ctx.author.id:
                author_rank = users_sorted.index(user) + 1
                author_post_count = user[1]

        description = f"Your rank: {author_rank} with {author_post_count} posts this month."

        footer = f"{total_monthly_count} posts counted."

        await ctx.send(embed=embed_builder(ctx,
                                           title=title,
                                           description=description,
                                           footer=footer,
                                           fields=fields_top10))


    @commands.hybrid_command()
    async def dmcboard(self, ctx):
        async with aiosqlite.connect(self.db_file) as conn:
            cur = await conn.cursor()
            sql = f"SELECT * FROM accounts WHERE private!=1"
            await cur.execute(sql)
            rows = await cur.fetchall()

        for row in rows:
            pass