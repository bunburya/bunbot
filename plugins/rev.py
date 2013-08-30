class Plugin:

    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.conn
        self.hooks = [{'type': 'command', 'key': '!rev', 'func': self.rev}]

    def rev(self, data):
        self.conn.say(' '.join(data.tokens)[::-1], data.to)
