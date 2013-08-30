class Plugin:
    
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.conn
        self.hooks = [{'type': 'ping', 'func': self.pong}]
    
    def pong(self, data):
        self.bot.conn.pong(data.string)
