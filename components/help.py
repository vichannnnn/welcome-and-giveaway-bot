import asyncio
import lightbulb
import miru
import hikari

plugin = lightbulb.Plugin("Help Commands")

async def get_command_list(ctx: lightbulb.Context, cog: str):
    sub_commands_list = [i.subcommands for i in ctx.bot.get_plugin(cog).raw_commands if
                         i.subcommands]

    if sub_commands_list:
        sub_commands = []
        for i in sub_commands_list:
            for k in i:
                sub_commands.append(k)
        commands = [i.name for i in ctx.bot.get_plugin(cog).raw_commands][1:] + sub_commands
    else:
        commands = [i.name for i in ctx.bot.get_plugin(cog).raw_commands]
    return commands


class HelpDropdown(miru.Select):
    def __init__(self, ctx: lightbulb.Context, header, selections):
        self.ctx = ctx
        self.dict = {}
        options = []
        for emote, name in selections:
            options.append(miru.SelectOption(label=name, emoji=hikari.Emoji.parse(emote)))
            self.dict[name] = f'{emote} {name}'
        super().__init__(placeholder=header, min_values=1, max_values=1, options=options)

    async def callback(self, ctx: lightbulb.Context) -> None:
        labels = [i.label for i in self.options]
        idx = labels.index(self.values[0])
        name = str(self.options[idx].label)
        self.view.value = self.dict[name]

        embed = hikari.Embed(title=f"{name} Help", colour=hikari.Color(0xD5AF9F))
        embed.set_thumbnail(str(self.ctx.bot.application.icon_url))
        embed.set_footer(
            text=f"Select dropdown menu below category help! ::",
            icon=self.ctx.bot.application.icon_url)

        commands = await get_command_list(self.ctx, self.view.value)
        for comm in commands:
            try:
                comm_object = self.ctx.bot.get_slash_command(comm)
            except TypeError:
                comm_object = comm

            embed.add_field(name=f"/{comm_object.name}",
                            value=comm_object.description, inline=True)
        await ctx.respond(embed=embed, flags=hikari.MessageFlag.EPHEMERAL)


class View(miru.View):
    def __init__(self, ctx: lightbulb.Context, item):
        self.ctx = ctx
        self.item = item
        self.bot = self.ctx.bot
        super().__init__(timeout=300)
        self.add_item(self.item)

    async def on_timeout(self) -> None:
        embed = hikari.Embed(description="Help command has timed out. Please restart the command.")
        await self.message.edit(embed=embed, components=[])

    async def view_check(self, ctx: miru.Context) -> bool:
        return self.ctx.author == ctx.user

@plugin.command
@lightbulb.add_cooldown(5, 1, lightbulb.UserBucket)
@lightbulb.command("help", "Help command to navigate the bot.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def help(ctx: lightbulb.Context):
    cogs = [ctx.bot.get_plugin(cog) for cog in ctx.bot.plugins if
            ctx.bot.get_plugin(cog).name not in ["Help Commands", "Admin Commands"] and ctx.bot.get_plugin(
                cog).all_commands]

    embed = hikari.Embed(description=f"You may use any of my command by either using in-built slash commands or "
                                     f"by mentioning me as prefix."
                                     f"\n\n", colour=hikari.Color(0xD5AF9F))
    embed.set_author(name=f"{str(ctx.bot.get_me().username).partition('#')[0]}'s Commands and Help",
                     icon=ctx.bot.application.icon_url)
    embed.set_thumbnail(ctx.bot.application.icon_url)
    embed.set_footer(
        text=f"Select dropdown menu below for more category help! :: ",
        icon=ctx.bot.application.icon_url)

    for cog in cogs:
        commands_list = ''
        lst = await get_command_list(ctx, cog.name)
        for command in lst:
            try:
                commands = ctx.bot.get_slash_command(command)
            except TypeError:
                commands = command
            commands_list += f'`{commands.name}` ' if commands else ''
        embed.add_field(name=cog.name, value=commands_list, inline=False)

    try:
        lst = [(cog.name.split()[0], ' '.join(cog.name.split()[1:])) for cog in cogs]
        view = View(ctx, HelpDropdown(ctx, "Choose a category", lst))
        proxy = await ctx.respond(embed=embed, components=view.build(), flags=hikari.MessageFlag.EPHEMERAL)
        message = await proxy.message()
        view.start(message)
        await view.wait()

    except asyncio.TimeoutError:
        pass


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)
