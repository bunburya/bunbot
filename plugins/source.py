class Plugin:

    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.hooks = [{'type': 'command', 'key': '!source', 'func': self.source}]

    def source(self, data):
        self.conn.say('https://github.com/bunburya/bunbot', data.to)
