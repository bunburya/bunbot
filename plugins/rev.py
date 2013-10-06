class Plugin:

    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.hooks = [{'type': 'command', 'key': '!rev', 'func': self.rev}]

    def rev(self, data):
        self.conn.say(' '.join(data.tokens)[::-1], data.to)
