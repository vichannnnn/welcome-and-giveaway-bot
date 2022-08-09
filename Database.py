import sqlite3

conn = sqlite3.connect('bot.db', timeout=5.0)
c = conn.cursor()

c.execute(
    '''CREATE TABLE IF NOT EXISTS server (
    server_id INT PRIMARY KEY, 
    embed TEXT
    ) ''')

c.execute(
    '''CREATE TABLE IF NOT EXISTS greetingSettings (
    guildID INT PRIMARY KEY, 
    channelID INT DEFAULT 0, 
    message TEXT DEFAULT "",
    embed TEXT DEFAULT "0xdecaf0"
    ) ''')

c.execute(
    '''CREATE TABLE IF NOT EXISTS greetingImages (
    guildID INT, 
    image TEXT
    ) ''')

c.execute(
    ' CREATE TABLE IF NOT EXISTS giveaway '
    '(server_id INT, '
    'channel_id INT,'
    'msg_id INT, '
    'user_id INT , '
    'endsAt INT, '
    'winners INT, '
    'prize TEXT, '
    'description TEXT, '
    'roleRequirement INT'
    ')')

c.execute(
    ' CREATE TABLE IF NOT EXISTS endedGiveaway '
    '(server_id INT, '
    'channel_id INT, '
    'msg_id INT, '
    'user_id INT , '
    'endsAt INT, '
    'winners INT, '
    'prize TEXT, '
    'descriptions TEXT, '
    'participants TEXT, '
    'winningLists TEXT'
    ')')


class Database:
    @staticmethod
    def connect():
        conn = sqlite3.connect('bot.db')
        c = conn.cursor()
        return c

    @staticmethod
    def execute(statement, *args):
        c = Database.connect()
        c.execute(statement, args)
        c.connection.commit()
        c.connection.close()

    @staticmethod
    def get(statement, *args):
        c = Database.connect()
        c.execute(statement, args)
        res = c.fetchall()
        c.connection.close()
        return res
