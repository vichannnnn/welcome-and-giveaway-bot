import lightbulb
import hikari
from Database import Database
import re
import random
import components.colourEmbed as functions
from components.colourEmbed import embedColour
import datetime
import pytz
import traceback
import ast
from lightbulb.ext import tasks
from components.ConfirmView import View

plugin = lightbulb.Plugin("🎉 Giveaway")
plugin.add_checks(lightbulb.checks.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))


class Giveaway:
    def __init__(self, message_id: int):
        self.ga = False
        self.server_id = None
        self.channel_id = None
        self.msg_id = message_id
        self.user_id = None
        self.ends_at = None
        self.winners = None
        self.prize = None
        self.description = None
        self.role_requirement = None
        self.server_obj = None
        self.channel_obj = None
        self.msg_obj = None
        self.get_data()

    def get_data(self):
        data = [i for i in Database.execute(' SELECT * FROM giveaway WHERE msg_id = ? ', self.msg_id)]

        if data:
            self.server_id, self.channel_id, self.user_id, self.ends_at, self.winners, self.prize, self.description, self.role_requirement = \
                data[0]
            self.server_obj = plugin.bot.cache.get_guild(self.server_id)
            self.channel_obj = plugin.bot.cache.get_guild_channel(self.channel_id)
            self.msg_obj = plugin.bot.cache.get_message(self.msg_id)
            self.ga = True

        else:
            self.ga = False


class EndedGiveaway:
    def __init__(self, message_id: int):
        self.ga = False
        self.server_id = None
        self.channel_id = None
        self.msg_id = message_id
        self.user_id = None
        self.ends_at = None
        self.winners = None
        self.prize = None
        self.description = None
        self.participants = None
        self.winning_list = None
        self.server_obj = None
        self.channel_obj = None
        self.msg_obj = None
        self.get_data()

    def get_data(self):
        data = [i for i in Database.execute(' SELECT * FROM endedGiveaway WHERE msg_id = ? ', self.msg_id)]

        if data:
            self.server_id, self.channel_id, self.user_id, self.ends_at, self.winners, self.prize, self.description, self.participants, self.winning_list = \
                data[0]
            self.server_obj = plugin.bot.cache.get_guild(self.server_id)
            self.channel_obj = plugin.bot.cache.get_guild_channel(self.channel_id)
            self.msg_obj = plugin.bot.cache.get_message(self.msg_id)
            self.ga = True

        else:
            self.ga = False


def dmyConverter(seconds):
    seconds_in_days = 60 * 60 * 24
    seconds_in_hours = 60 * 60
    seconds_in_minutes = 60

    days = seconds // seconds_in_days
    hours = (seconds - (days * seconds_in_days)) // seconds_in_hours
    minutes = ((seconds - (days * seconds_in_days)) - (hours * seconds_in_hours)) // seconds_in_minutes
    seconds_left = seconds - (days * seconds_in_days) - (hours * seconds_in_hours) - (minutes * seconds_in_minutes)

    time_statement = ""

    if days != 0:
        time_statement += f"{round(days)} day{'s' if round(days) > 1 else ''}, "
    if hours != 0:
        time_statement += f"{round(hours)} hour{'s' if round(hours) > 1 else ''}, "
    if minutes != 0:
        time_statement += f"{round(minutes)} minute{'s' if round(minutes) > 1 else ''}, "
    if seconds_left != 0:
        time_statement += f"{round(seconds_left)} second{'s' if round(seconds_left) > 1 else ''}"
    if time_statement[-2:] == ", ":
        time_statement = time_statement[:-2]
    return time_statement


def in_seconds(text):
    unit_value = {'d': 60 * 60 * 24, 'h': 60 * 60, 'm': 60, 's': 1}
    seconds = 0
    for number, unit in re.findall(r'(\d+)([dhms])', text):
        seconds = seconds + unit_value[unit] * int(number)
    return seconds


async def delete_giveaway(embed: hikari.Embed, msg_obj: hikari.Message, id: int):
    await msg_obj.edit(embed=embed)
    Database.execute(' DELETE FROM giveaway WHERE msg_id = ? ', id)


@tasks.task(s=30, pass_app=True)
async def giveaway_handler(self):
    try:
        now = datetime.datetime.now(pytz.timezone("Singapore")).timestamp()
        all_giveaways = [i for i in Database.get('SELECT * FROM giveaway')]

        for serverID, channelID, msgID, hostID, endsAt, qtyWinners, prize, description, roleRequirement in all_giveaways:
            guildObject = plugin.bot.cache.get_guild(serverID)
            channelObject = guildObject.get_channel(channelID)

            try:
                messageObject = await plugin.bot.rest.fetch_message(channelObject, msgID)
            except:
                Database.execute(' DELETE FROM giveaway WHERE msg_id = ? ', msgID)
                continue

            hostObject = guildObject.get_member(hostID)
            endsAtTimeObject = datetime.datetime.fromtimestamp(endsAt, tz=pytz.timezone("Singapore"))
            timeLeft = endsAt - now
            formattedTime = dmyConverter(timeLeft)

            if timeLeft < 0:
                for reaction in messageObject.reactions:
                    if str(reaction.emoji) == '🎉':
                        users = await plugin.bot.rest.fetch_reactions_for_emoji(channelObject, messageObject,
                                                                                reaction.emoji)
                        raffle = [user for user in users if not user.is_bot]

                        if not raffle:
                            totalDescription = "Could not determine a winner!\n"
                            totalDescription += f"Hosted by: {hostObject.mention}"
                            embed = hikari.Embed(title=f'{prize}', description=totalDescription,
                                                 timestamp=endsAtTimeObject,
                                                 colour=functions.embedColour(serverID))
                            embed.set_footer(text=f"{qtyWinners} Winner{'s' if qtyWinners > 1 else ''} | Ended at ")
                            await delete_giveaway(embed, messageObject, msgID)
                            endedDescription = f"🎉 Could not determine a winner for **{prize}**"
                            return await channelObject.send(endedDescription, user_mentions=True)

                        winnerList = ""
                        winners = []

                        for i in range(qtyWinners):
                            if not raffle:
                                break
                            winner = random.choice(raffle)
                            winners.append(winner)
                            winnerList += f"{winner.mention}"
                            raffle.remove(winner)

                        totalDescription = f"Winner: {winnerList}\n"
                        totalDescription += f"Hosted by: {hostObject.mention}"
                        embed = hikari.Embed(title=f'{prize}',
                                             description=totalDescription, timestamp=endsAtTimeObject,
                                             colour=functions.embedColour(serverID))
                        embed.set_footer(text=f"{qtyWinners} Winner{'s' if qtyWinners > 1 else ''} | Ended at ")
                        await delete_giveaway(embed, messageObject, msgID)
                        endedDescription = f"🎉 Congratulations {winnerList}, you won **{prize}**"
                        await channelObject.send(endedDescription, user_mentions=True)

                        if raffle:
                            remainingPool = [user.id for user in raffle]
                            strPool = f"{remainingPool}"
                            strWinner = f"{winners}"
                            Database.execute('INSERT INTO endedGiveaway VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                             serverID, channelID, msgID, hostID, endsAt,
                                             qtyWinners,
                                             prize,
                                             totalDescription, strPool, strWinner)
                continue

            totalDescription = f"{description}\n\n"
            totalDescription += "React with 🎉 to enter!\n"
            totalDescription += f"Time Remaining: {formattedTime}\n"
            totalDescription += f"Hosted by: {hostObject.mention}"

            if roleRequirement:
                roleList = ast.literal_eval(roleRequirement)
                totalDescription += "\nRequired Roles (at least one): "
                for role in roleList:
                    totalDescription += f"{guildObject.get_role(int(role)).mention}"

            embed = hikari.Embed(title=f'{prize}', description=totalDescription, timestamp=endsAtTimeObject,
                                 colour=functions.embedColour(serverID))
            embed.set_footer(text=f"{qtyWinners} Winner{'s' if qtyWinners > 1 else ''} | Ended at ")
            await messageObject.edit(embed=embed)

    except:
        traceback.print_exc()


@plugin.listener(hikari.StartedEvent)
async def on_ready(event: hikari.StartedEvent) -> None:
    giveaway_handler.start()


@plugin.command
@lightbulb.option('description', 'The description of the giveaway.', str, default=None)
@lightbulb.option('prize', 'The prize of the giveaway.', str)
@lightbulb.option('winners', 'The number of winners.', int)
@lightbulb.option('duration', 'The duration you want to set to.', str)
@lightbulb.option('channel', 'The text channel where the giveaway will be held.', hikari.TextableChannel,
                  channel_types=[hikari.ChannelType.GUILD_TEXT])
@lightbulb.command("start", "Starts a quick giveaway.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def start(ctx: lightbulb.Context):
    seconds = in_seconds(ctx.options.duration)

    if seconds <= 0:
        return await functions.errorEmbedTemplate(ctx,
                                                  f"Invalid time format or input! Please restart the command and try again.",
                                                  ctx.author)

    if not 21 > ctx.options.winners > 0:
        return await functions.errorEmbedTemplate(ctx,
                                                  f"Invalid number of winners or input! Please restart the command and try again.",
                                                  ctx.author)

    formattedTime = dmyConverter(seconds)
    timeRemaining = f"Time Remaining: {formattedTime}"
    hostedBy = f"Hosted by: {ctx.author.mention}"

    now = datetime.datetime.now(pytz.timezone("Singapore"))
    endsAt = now + datetime.timedelta(seconds=seconds)
    description = f"{ctx.options.description}\n\n" if ctx.options.description else ''
    description += "React with 🎉 to enter!\n"
    description += f"{timeRemaining}\n"
    description += f"{hostedBy}"

    embed = hikari.Embed(title=ctx.options.prize, description=description, timestamp=endsAt,
                         colour=embedColour(ctx.get_guild().id))
    embed.set_footer(text=f"{ctx.options.winners} Winner{'s' if ctx.options.winners > 1 else ''} | Ends at ")

    channel = plugin.bot.cache.get_guild_channel(ctx.options.channel.id)
    msg = await channel.send(embed=embed)
    await msg.add_reaction('🎉')

    Database.execute('INSERT INTO giveaway VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     ctx.guild_id, channel.id, msg.id, ctx.author.id, endsAt.timestamp(), ctx.options.winners,
                     ctx.options.prize, ctx.options.description if ctx.options.description else '', 0)
    await functions.successEmbedTemplate(ctx, f"Giveaway successfully started on {channel.mention}", ctx.author)


@plugin.command
@lightbulb.command("giveaway", "Starts a giveaway in an interactive and detailed manner.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def giveaway(ctx: lightbulb.Context):
    description = "🎉 Alright! Let's set up your giveaway! First, what channel do you want the giveaway in?\n"
    description += "You can type cancel at any time to cancel creation.\n\n"
    description += "`Please mention the channel that you want the giveaway to be hosted in this server.`"
    embed = hikari.Embed(description=description)
    await ctx.respond(embed=embed)

    waited_event = await plugin.bot.wait_for(hikari.MessageCreateEvent,
                                             timeout=60,
                                             predicate=lambda e: e.author_id == ctx.interaction.user.id)

    channelMessage = waited_event.content
    giveawayChannelID = channelMessage.replace('<', '').replace('>', '').replace('#', '')

    try:
        giveawayChannel = plugin.bot.cache.get_guild_channel(int(giveawayChannelID))

    except:
        return await functions.errorEmbedTemplate(ctx,
                                                  f"Something went wrong with your channel input, please restart the command!",
                                                  ctx.author)

    description = f"🎉 Sweet! The giveaway will be in {giveawayChannel.mention}! Next, how long should the giveaway last?\n\n"
    description += "`Please enter the duration of the giveaway in dhms format (e.g. 6d2h4m2s).`"

    embed = hikari.Embed(description=description)
    await ctx.respond(embed=embed)

    waited_event = await plugin.bot.wait_for(hikari.MessageCreateEvent,
                                             timeout=60,
                                             predicate=lambda e: e.author_id == ctx.interaction.user.id)

    durationMessage = waited_event.content
    seconds = in_seconds(durationMessage)

    if seconds <= 0 or seconds < 300:
        return await functions.errorEmbedTemplate(ctx,
                                                  f"Invalid time format or input! Please restart the command and try again. "
                                                  f"Time must be at least 5 minutes!",
                                                  ctx.author)

    formattedTime = dmyConverter(seconds)
    description = f"🎉 Neat! This giveaway will last {formattedTime}! Now, how many winners should there be?\n\n"
    description += "`Please enter a number of winners between 1 and 20.`"

    embed = hikari.Embed(description=description)
    await ctx.respond(embed=embed)

    waited_event = await plugin.bot.wait_for(hikari.MessageCreateEvent,
                                             timeout=60,
                                             predicate=lambda e: e.author_id == ctx.interaction.user.id)
    quantityMessage = waited_event.content

    if not 21 > int(quantityMessage) > 0:
        return await functions.errorEmbedTemplate(ctx,
                                                  f"Invalid number of winners or input! Please restart the command and try again.",
                                                  ctx.author)

    description = f"🎉 Ok! {quantityMessage} winner it is! Now, what do you want to give away?\n\n"
    description += f"`Please enter the giveaway prize.`"

    embed = hikari.Embed(description=description)
    await ctx.respond(embed=embed)

    waited_event = await plugin.bot.wait_for(hikari.MessageCreateEvent,
                                             timeout=30,
                                             predicate=lambda e: e.author_id == ctx.interaction.user.id)

    prizeMessage = waited_event.content

    description = f"🎉 Great! The prize will be **{prizeMessage}**! Almost done! What is your text description for the giveaway?\n\n"
    description += "`Please enter your description text for the giveaway.`"

    embed = hikari.Embed(description=description)
    await ctx.respond(embed=embed)

    waited_event = await plugin.bot.wait_for(hikari.MessageCreateEvent,
                                             timeout=30,
                                             predicate=lambda e: e.author_id == ctx.interaction.user.id)

    descMessage = waited_event.content

    if len(descMessage) > 1500:
        return await functions.errorEmbedTemplate(ctx,
                                                  f"Your message is too long (Max. 1500 characters)! Please restart the command and try again!",
                                                  ctx.author)

    description = f"🎉 Awesome! The description has been successfully set! Finally, are there any role requirements?\n\n"
    description += "`Please mention the role you want to for users to have before allowing them to partake in the giveaway`\n"
    description += "`Please mention the roles together in one message (separated by space) if there are multiple roles. Type 'none' if there are no requirements.`\n"
    description += "`If no mentioned roles are detected and 'none' is not typed, it will be assumed to have no role requirements.`"

    embed = hikari.Embed(description=description)
    await ctx.respond(embed=embed)

    waited_event = await plugin.bot.wait_for(hikari.MessageCreateEvent,
                                             timeout=30,
                                             predicate=lambda e: e.author_id == ctx.interaction.user.id)
    newRoleList = []

    if waited_event.content == "none":
        roleRequirements = 0

    else:
        roleList = waited_event.content.split()
        for role in roleList:
            newRole = role.replace('<', '').replace('>', '').replace('&', '').replace('@', '')
            if role != newRole:
                newRoleList.append(newRole)

        if not newRoleList:
            roleRequirements = 0
        else:
            roleRequirements = f"{newRoleList}"

    timeRemaining = f"Time Remaining: {formattedTime}"
    hostedBy = f"Hosted by: {ctx.author.mention}"

    now = datetime.datetime.now(pytz.timezone("Singapore"))
    endsAt = now + datetime.timedelta(seconds=seconds)
    description = f"{descMessage}\n\n"
    description += "React with 🎉 to enter!\n"
    description += f"{timeRemaining}\n"
    description += f"{hostedBy}"

    if roleRequirements:
        roleObjList = [ctx.get_guild().get_role(role) for role in newRoleList]
        roleDesc = ""
        for role in roleObjList:
            roleDesc += f"{role.mention}"
        description += f"\nRequired Roles (at least one): {roleDesc}"

    embed = hikari.Embed(title=f'{prizeMessage}', description=description, timestamp=endsAt,
                         colour=embedColour(ctx.guild_id))
    embed.set_footer(text=f"{int(quantityMessage)} Winner{'s' if int(quantityMessage) > 1 else ''} | Ends at ")
    view = View(ctx)
    proxy = await ctx.respond(embed=embed,
                              content="🎉 This will how the giveaway look like, please confirm below to confirm if you want to start the giveaway!",
                              components=view.build())
    message = await proxy.message()
    view.start(message)
    await view.wait()

    if view.value:
        msg = await giveawayChannel.send(embed=embed)
        Database.execute('INSERT INTO giveaway VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                         ctx.guild_id, giveawayChannelID, msg.id, ctx.author.id, endsAt.timestamp(),
                         int(quantityMessage),
                         prizeMessage,
                         descMessage, roleRequirements)
        await functions.successEmbedTemplate(ctx, f"Giveaway successfully started on {giveawayChannel.mention}",
                                             ctx.author)

    else:
        embed = hikari.Embed(description="You have discarded your input, please start the command again!")
        await ctx.respond(embed=embed)


@plugin.command
@lightbulb.option('duration', 'The duration you want to set to.', str)
@lightbulb.option('giveaway_id', 'The ID of the existing ongoing giveaway.', str)
@lightbulb.command("timereset", f"Changes the timer of an existing giveaway.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def timereset(ctx: lightbulb.Context):
    giveaway_id = int(ctx.options.giveaway_id)
    current_giveaway = Giveaway(int(ctx.options.giveaway_id))

    if not current_giveaway.ga:
        return await functions.errorEmbedTemplate(ctx,
                                                  f"The giveaway with that ID either does not exist!",
                                                  ctx.author)

    now = datetime.datetime.now(pytz.timezone("Singapore")).timestamp()
    seconds = in_seconds(ctx.options.duration)
    Database.execute(' UPDATE giveaway SET endsAt = ? WHERE msg_id = ? ', now + seconds, giveaway_id)

    await functions.successEmbedTemplate(ctx, f"Successfully changed the timer of giveaway `{giveaway_id}`!",
                                         ctx.author)


@plugin.command
@lightbulb.option('giveaway_id', 'The ID of the existing ongoing giveaway.', str)
@lightbulb.command("reroll", f"Rerolls an ended giveaway. Only works if there are pool of eligible remaining users.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def reroll(ctx: lightbulb.Context):
    ga_id = int(ctx.options.giveaway_id)
    ga_obj = EndedGiveaway(ga_id)

    if not ga_obj.ga:
        return await functions.errorEmbedTemplate(ctx,
                                                  f"The giveaway with that ID either does not exist or isn't eligible for reroll "
                                                  f"due to lack of participants!",
                                                  ctx.author)

    if ga_obj.server_id != ctx.guild_id:
        return await functions.errorEmbedTemplate(ctx,
                                                  f"The giveaway with that ID is not in this server!",
                                                  ctx.author)

    Database.execute('DELETE FROM endedGiveaway WHERE msg_id = ?', ga_id)
    participantPool = ast.literal_eval(ga_obj.winning_list)
    endsAtTimeObject = datetime.datetime.fromtimestamp(ga_obj.ends_at, tz=pytz.timezone("Singapore"))

    winnerList = ""
    winners = []

    for i in range(ga_obj.winners):
        if not participantPool:
            break
        winner = random.choice(participantPool)
        winnerObject = ctx.get_guild().get_member(winner)

        if winnerObject:
            winnerList += f"{winnerObject.mention}"
            winners.append(winner)
            participantPool.remove(winner)
        else:
            participantPool.remove(winner)
            continue

    remainingPool = [user for user in participantPool]
    strPool = f"{remainingPool}"
    strWinner = f"{winners}"
    totalDescription = f"Winner: {winnerList}\n"
    totalDescription += f"Hosted by: <@{ga_obj.user_id}>"
    embed = hikari.Embed(title=ga_obj.prize,
                         description=totalDescription, timestamp=endsAtTimeObject,
                         colour=embedColour(ga_obj.server_id))
    embed.set_footer(text=f"{ga_obj.winners} Winner{'s' if ga_obj.winners > 1 else ''} | Ended at ")
    await ga_obj.msg_obj.edit(embed=embed)
    endedDescription = f"🎉 Congratulations {winnerList}, you won **{ga_obj.prize}**"
    await ga_obj.channel_obj.send(endedDescription)
    await functions.successEmbedTemplate(ctx, f"Successfully rerolled {ga_obj.msg_id}", ctx.author)

    if remainingPool:
        Database.execute('INSERT INTO endedGiveaway VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (
            ga_obj.server_id, ga_obj.channel_id, ga_obj.msg_id, ga_obj.user_id, ga_obj.ends_at,
            ga_obj.winners, ga_obj.prize, totalDescription, strPool, strWinner))


@plugin.command
@lightbulb.option('giveaway_id', 'The ID of the existing ongoing giveaway.', str)
@lightbulb.command("end", f"Ends a specified giveaway regardless of time left. Has a short delay.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def end(ctx: lightbulb.Context):
    giveawayId = int(ctx.options.giveaway_id)
    ga_obj = Giveaway(giveawayId)

    if not ga_obj.ga:
        return await functions.errorEmbedTemplate(ctx,
                                                  f"The giveaway with that ID either does not exist!",
                                                  ctx.author)

    endsAtTimeObject = datetime.datetime.fromtimestamp(ga_obj.ends_at, tz=pytz.timezone("Singapore"))
    now = datetime.datetime.now(pytz.timezone("Singapore"))

    for reaction in ga_obj.msg_obj.reactions:
        if str(reaction.emoji) == '🎉':
            users = await plugin.bot.rest.fetch_reactions_for_emoji(ga_obj.channel_obj, ga_obj.msg_obj,
                                                                    reaction.emoji)
            raffle = [user for user in users if not user.is_bot]

            if not raffle:
                totalDescription = "Could not determine a winner!\n"
                totalDescription += f"Hosted by: <@{ga_obj.user_id}>"
                embed = hikari.Embed(title=ga_obj.prize, description=totalDescription,
                                     timestamp=now,
                                     colour=embedColour(ga_obj.server_id))
                embed.set_footer(text=f"{ga_obj.winners} Winner{'s' if ga_obj.winners > 1 else ''} | Ended at ")
                await ga_obj.msg_obj.edit(embed=embed)
                Database.execute(' DELETE FROM giveaway WHERE msg_id = ? ', ga_obj.msg_id)

                endedDescription = f"🎉 Could not determine a winner for **{ga_obj.prize}**"
                return await ga_obj.channel_obj.send(endedDescription)

            winnerList = ""
            winners = []

            for i in range(ga_obj.winners):
                if not raffle:
                    break
                winner = random.choice(raffle)
                winners.append(winner)
                winnerList += f"{winner.mention}"
                raffle.remove(winner)

            totalDescription = f"Winner: {winnerList}\n"
            totalDescription += f"Hosted by: <@{ga_obj.user_id}>"
            embed = hikari.Embed(title=ga_obj.prize, description=totalDescription,
                                 timestamp=now,
                                 colour=embedColour(ga_obj.server_id))
            embed.set_footer(text=f"{ga_obj.winners} Winner{'s' if ga_obj.winners > 1 else ''} | Ended at ")
            await ga_obj.msg_obj.edit(embed=embed)
            Database.execute(' DELETE FROM giveaway WHERE msg_id = ? ', ga_obj.msg_id)
            endedDescription = f"🎉 Congratulations {winnerList}, you won **{ga_obj.prize}**"
            await ga_obj.channel_obj.send(endedDescription)

            if raffle:
                remainingPool = [user.id for user in raffle]
                strPool = f"{remainingPool}"
                strWinner = f"{winners}"
                Database.execute('INSERT INTO endedGiveaway VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                 ga_obj.server_id, ga_obj.channel_id, ga_obj.msg_id, ga_obj.user_id, ga_obj.ends_at,
                                 ga_obj.winners,
                                 ga_obj.prize,
                                 totalDescription, strPool, strWinner)
    await functions.successEmbedTemplate(ctx, f"Giveaway {giveawayId} successfully ended!", ctx.author)


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)
