import components.colourEmbed as functions
import traceback
import re
import random
import hikari
import lightbulb
from components.settings_components import Greetings, NoSettingsError
from Database import Database

plugin = lightbulb.Plugin("⚙️ Admin Commands")
plugin.add_checks(lightbulb.checks.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))


def hexConverter(colour):
    colourEmbedInt = int(colour, 16)
    return colourEmbedInt


async def welcomeEmbedCreator(guild: hikari.Guild, member: hikari.Member):
    greet_obj = Greetings(guild)
    hexColour = hexConverter(greet_obj.colour)
    channel = plugin.bot.cache.get_guild_channel(greet_obj.channel_id)
    updated_message = greet_obj.message.replace('[member]', member.mention)
    embed = hikari.Embed(description=updated_message, colour=hikari.Colour(hexColour))
    embed.set_author(name=str(member), icon=str(member.display_avatar_url))
    chosen_image = random.choice(greet_obj.image_list) if greet_obj.image_list else None
    embed.set_image(chosen_image) if chosen_image else None
    return await channel.send(embed=embed)


@plugin.listener(hikari.MemberCreateEvent)
async def on_member_join(event: hikari.MemberCreateEvent) -> None:
    await welcomeEmbedCreator(event.member.get_guild(), event.member)


@plugin.command
@lightbulb.command("testgreet", f"Test the greeting embed.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def testgreet(ctx: lightbulb.Context):
    try:
        greet_obj = Greetings(ctx.get_guild())

    except NoSettingsError:
        await functions.errorEmbedTemplate(ctx,
                                           f"There are no settings in this guild yet. "
                                           f"Please set-up using the other commands before trying again.",
                                           ctx.author)
        return
    message = await welcomeEmbedCreator(ctx.get_guild(), ctx.author)
    await functions.successEmbedTemplate(ctx, f"Successfully sent the test greet "
                                              f"[here](https://discordapp.com/channels/{greet_obj.guild_id}/{greet_obj.channel_id}/{message.id})!",
                                         ctx.author)


@plugin.command
@lightbulb.command("greetimagelist", f"Shows the list of greeting images.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def greetimagelist(ctx: lightbulb.Context):
    guild = ctx.get_guild()

    try:
        greet_obj = Greetings(guild)
    except NoSettingsError:
        await functions.errorEmbedTemplate(ctx,
                                           f"There are no settings in this guild yet. "
                                           f"Please set-up using the other commands before trying again.",
                                           ctx.author)
        return

    description = ""
    if greet_obj.image_list:
        for i in greet_obj.image_list:
            description += f"{i}\n\n"

    embed = hikari.Embed(title="Greeting Image List", description=description,
                         colour=functions.embedColour(guild.id))
    embed.set_footer(text=f"Requested by {ctx.author}", icon=str(ctx.author.display_avatar_url))
    await ctx.respond(embed=embed)


@plugin.command
@lightbulb.option('image_url', 'Image Link that you want to remove from the greeting images.', str)
@lightbulb.command("greetimageremove", f"Removes a specific image link from the greeting images.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def greetimageremove(ctx: lightbulb.Context):
    try:
        greet_obj = Greetings(ctx.get_guild())

    except NoSettingsError:
        await functions.errorEmbedTemplate(ctx,
                                           f"There are no settings in this guild yet. "
                                           f"Please set-up using the other commands before trying again.",
                                           ctx.author)
        return

    if ctx.options.image_url not in greet_obj.image_list:
        return await functions.errorEmbedTemplate(ctx, f"The image link you're trying to delete does not exist.",
                                                  ctx.author)

    Database.execute('DELETE FROM greetingImages WHERE image = ? ', ctx.options.image_url)
    return await functions.successEmbedTemplate(ctx,
                                                f"Successfully deleted the image link from the greeting image list.",
                                                ctx.author)


@plugin.command
@lightbulb.option('image_url', 'Image Link that you want to add to the greeting images.', str)
@lightbulb.command("setgreetimage", f"Sets the greeting message image or gif.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def setgreetimage(ctx: lightbulb.Context):
    if not re.findall(r'(https?://[^\s]+)', ctx.options.image_url):
        return functions.errorEmbedTemplate(ctx,
                                            f"Please enter a valid image link that is in either GIF/PNG/JPG format!",
                                            ctx.author)

    Database.execute('INSERT INTO greetingImages VALUES (?, ?)', ctx.get_guild().id, ctx.options.image_url)
    return await functions.successEmbedTemplate(ctx,
                                                f"Successfully added an image to be shown in the welcome embed.\n\n"
                                                f"**Please use `greetimagelist` to see the current list of image links or `greetimageremove` to remove it.**",
                                                ctx.author)


@plugin.command
@lightbulb.option('message', 'The text message you want shown.', str)
@lightbulb.command("setgreetmsg", f"Sets the greeting message.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def setgreetmsg(ctx: lightbulb.Context):
    Database.execute('INSERT OR IGNORE INTO greetingSettings (guildID, message) VALUES (?, ?)', ctx.get_guild().id,
                     ctx.options.message)
    Database.execute('UPDATE greetingSettings SET message = ? WHERE guildID = ?', ctx.options.message,
                     ctx.get_guild().id)
    return await functions.successEmbedTemplate(ctx,
                                                f"Successfully set new greet message to: \n"
                                                f"`{ctx.options.message}`\n\n"
                                                f"**Please use `testgreet` command to test the preview of the welcome message.**\n"
                                                f"**You can also use `[member]` in the message to substitute the member mention.**\n"
                                                f'**Example: "Welcome, [member]!" would result in "Welcome, {ctx.author.mention}!"**',
                                                ctx.author)


@plugin.command
@lightbulb.option('colour_code', 'The colour code of the embed e.g. 0xffff0', str)
@lightbulb.command("setgreetcolour", f"Sets the greeting embed colour.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def setgreetcolour(ctx: lightbulb.Context):
    hexcode = hexConverter(ctx.options.colour_code)
    guild = ctx.get_guild()
    if hexcode > 16777216 or hexcode < 0:
        return await functions.errorEmbedTemplate(ctx,
                                                  f"Invalid input for colour code. Please make sure it's in the "
                                                  f"format of 0x E.g. `0xffff00` for #ffff00 and a valid hexcode.",
                                                  ctx.author)

    Database.execute('INSERT OR IGNORE INTO greetingSettings (guildID, embed) VALUES (?, ?)', guild.id,
                     str(ctx.options.colour_code))
    Database.execute('UPDATE greetingSettings SET embed = ? WHERE guildID = ? ', str(ctx.options.colour_code), guild.id)
    return await functions.successEmbedTemplate(ctx,
                                                f"Successfully set the greet embed colour to **{str(ctx.options.colour_code)}**",
                                                ctx.author)


@plugin.command
@lightbulb.option('channel', 'The welcome text channel to be set.', hikari.TextableChannel,
                  channel_types=[hikari.ChannelType.GUILD_TEXT], default=None)
@lightbulb.command("setgreetchannel", f"Sets the greeting channel where the welcome message is sent.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def setgreetchannel(ctx: lightbulb.Context):
    channel = ctx.options.channel
    guild = ctx.get_guild()

    if channel:
        chnl_object = guild.get_channel(channel.id)
        Database.execute('INSERT OR IGNORE INTO greetingSettings (guildID, channelID) VALUES (?, ?) ', guild.id,
                         channel.id if channel else 0)
        Database.execute('UPDATE greetingSettings SET channelID = ? WHERE guildID = ? ', channel.id if channel else 0,
                         guild.id)
        return await functions.successEmbedTemplate(ctx,
                                                    f"Successfully {'set new greet channel to' if channel else 'removed the greet channel.'} "
                                                    f"{chnl_object.mention if channel else ''}. "
                                                    f"To remove the greet channel, "
                                                    f"use `setgreetchannel` command without any arguments.",
                                                    ctx.author)


@plugin.command
@lightbulb.option('colour_code', 'The colour code of the embed e.g. 0xffff0', str)
@lightbulb.command("embedsettings", f"Changes the colour of the embed.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def embed_settings(ctx: lightbulb.Context):
    hexcode = hexConverter(ctx.options.colour_code)

    if hexcode > 16777216 or hexcode < 0:
        return await functions.errorEmbedTemplate(ctx,
                                                  f"Invalid input for colour code. Please make sure it's in the "
                                                  f"format of 0x E.g. `0xffff00` for #ffff00 and a valid hexcode.",
                                                  ctx.author)

    try:
        await functions.colourChange(ctx, str(ctx.options.colour))

    except ValueError:
        traceback.print_exc()


@plugin.command
@lightbulb.option('description', 'The status\' text description', str)
@lightbulb.option('type', 'The type of status (playing/watching/listening)', str)
@lightbulb.command("status", f"Sets a custom status type and status for the Bot.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def status(ctx: lightbulb.Context):
    validInput = ['playing', 'listening', 'watching']

    if ctx.options.type.lower() not in validInput:
        return await functions.errorEmbedTemplate(ctx,
                                                  f"Invalid input. Input has to be either `playing`, `listening` or `watching`.",
                                                  ctx.author)

    if ctx.options.type.lower() == 'playing':
        # Setting `Playing ` status
        await plugin.bot.update_presence(
            activity=hikari.Activity(
                name=ctx.options.description,
                type=hikari.ActivityType.PLAYING,
            )
        )

    if ctx.options.type.lower() == 'listening':
        # Setting `Listening ` status
        await plugin.bot.update_presence(
            activity=hikari.Activity(
                name=ctx.options.description,
                type=hikari.ActivityType.LISTENING,
            )
        )

    if ctx.options.type.lower() == 'watching':
        # Setting `Watching ` status
        await plugin.bot.update_presence(
            activity=hikari.Activity(
                name=ctx.options.description,
                type=hikari.ActivityType.WATCHING,
            )
        )
    return await functions.successEmbedTemplate(ctx,
                                                f"Successfully set the Bot's status to **{ctx.options.type} {ctx.options.description}**.",
                                                ctx.author)


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)
