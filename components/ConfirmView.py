import lightbulb
import miru
import hikari

plugin = lightbulb.Plugin("Button Component")


class View(miru.View):
    def __init__(self, ctx: lightbulb.Context):
        self.ctx = ctx
        self.value = None
        super().__init__(timeout=10)

    async def view_check(self, ctx: miru.Context) -> bool:
        return self.ctx.author == ctx.user

    async def on_timeout(self) -> None:
        i = 0
        for button in self.children:
            if not i:
                button.emoji = "❎"
                button.label = "Timed Out"
                button.style = hikari.ButtonStyle.DANGER
                button.disabled = True
                i += 1
                continue
            self.remove_item(button)
        await self.message.edit(components=self.build())

    # Define a new Button with the Style of success (Green)
    @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS, emoji="✅")
    async def confirm(self, button: miru.Button, ctx: miru.Context) -> None:
        await ctx.respond("Successfully confirmed.", flags=hikari.MessageFlag.EPHEMERAL)
        button.label = "Confirmed"
        button.emoji = "☑"
        button.disabled = True

        for b in self.children:
            if b is not button:
                self.remove_item(b)

        await self.message.edit(components=self.build())
        self.value = True
        self.stop()

    # Define a new Button that when pressed will stop the view & invalidate all the buttons in this view
    @miru.button(label="Stop me!", style=hikari.ButtonStyle.DANGER, emoji="❎")
    async def stop_button(self, button: miru.Button, ctx: miru.Context) -> None:
        await ctx.respond("Successfully cancelled.", flags=hikari.MessageFlag.EPHEMERAL)
        button.label = "Cancelled"
        button.emoji = "❎"
        button.disabled = True

        for b in self.children:
            if b is not button:
                self.remove_item(b)

        await self.message.edit(components=self.build())
        self.value = False
        self.stop()


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)
