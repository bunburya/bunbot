class Plugin:
    
    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.hooks = [{'type': 'ping', 'func': self.pong}]
    
    def pong(self, data):
        self.bot.conn.pong(data.string)
