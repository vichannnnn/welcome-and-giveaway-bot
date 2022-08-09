import hikari
import lightbulb
from Database import Database

plugin = lightbulb.Plugin("Colour Commands")
plugin.add_checks(lightbulb.checks.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))


async def requestEmbedTemplate(ctx: lightbulb.Context, description, author: hikari.Member):
    embed = hikari.Embed(description=f"{description}", colour=embedColour(ctx.get_guild().id))
    embed.set_footer(text=f"Requested by {author}", icon=str(author.display_avatar_url))
    return await ctx.respond(embed=embed)


async def errorEmbedTemplate(ctx: lightbulb.Context, description, author: hikari.Member):
    embed = hikari.Embed(description=f"❎ {description}", colour=embedColour(ctx.get_guild().id))
    embed.set_footer(text=f"Requested by {author}", icon=str(author.display_avatar_url))
    return await ctx.respond(embed=embed)


async def successEmbedTemplate(ctx: lightbulb.Context, description, author: hikari.Member):
    embed = hikari.Embed(description=f"☑️ {description}", colour=embedColour(ctx.get_guild().id))
    embed.set_footer(text=f"Requested by {author}", icon=str(author.display_avatar_url))
    return await ctx.respond(embed=embed)


async def colourChange(ctx: lightbulb.Context, colour):
    guild = ctx.get_guild()
    Database.execute(f''' UPDATE server SET embed = ? WHERE server_id = ? ''', colour, guild.id)
    return await successEmbedTemplate(ctx, f"Embed colour successfully set to `{colour}` for **{guild}**.", ctx.author)


def embedColour(guild: int):
    colour = [i[0] for i in Database.get(f'SELECT embed FROM server WHERE server_id = ? ', guild)][0]
    colour_int = int(colour, 16)
    return colour_int


def createGuildProfile(id: int):
    Database.execute(''' INSERT INTO server VALUES (?, ?) ''', id, "0xdecaf0")
    print(f"Added for {id} into guild database.")


@plugin.listener(hikari.GuildJoinEvent)
async def on_guild_join(event: hikari.GuildJoinEvent):
    guild_database = [i[0] for i in Database.get('SELECT server_id FROM server')]

    if event.guild_id not in guild_database:
        createGuildProfile(event.guild_id)


@plugin.listener(hikari.StartedEvent)
async def on_ready(event: hikari.StartedEvent):

    guild_check = [i[0] for i in Database.get(' SELECT COUNT(*) FROM server ')][0]
    guilds = event.app.rest.fetch_my_guilds()

    if not guild_check:
        async for guild in guilds:
            createGuildProfile(guild.id)
        return

    guild_database = [i[0] for i in Database.get('SELECT server_id FROM server')]
    async for guild in guilds:
        if guild.id not in guild_database:
            createGuildProfile(guild.id)


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)
