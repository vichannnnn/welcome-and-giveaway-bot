import hikari
import lightbulb
from Database import Database

plugin = lightbulb.Plugin("Greetings")
plugin.add_checks(lightbulb.checks.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))


class NoSettingsError(Exception):
    def __init__(self, guild: hikari.Guild):
        self.guild = guild
        self.message = f"Guild: {self.guild} ({self.guild.id}) has no settings set yet."
        super().__init__(self.message)


class Greetings:
    def __init__(self, guild: hikari.Guild):
        self.guild = guild
        self.colour = None
        self.message = None
        self.channel_id = None
        self.guild_id = None
        self.image_list = []
        self.get_data()

    def get_data(self):
        try:
            self.guild_id, self.channel_id, self.message, self.colour = \
                [i for i in Database.get(' SELECT * FROM greetingSettings WHERE guildID = ? ', self.guild.id)][0]

        except IndexError:
            raise NoSettingsError(self.guild)

        img_lst = \
            [i[0] for i in Database.get(' SELECT COUNT(*) FROM greetingImages WHERE guildID = ? ', self.guild_id)][0]

        if img_lst:
            self.image_list = [i[0] for i in Database.get(' SELECT image FROM greetingImages WHERE guildID = ? ', self.guild_id)]


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)
