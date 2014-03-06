class Plugin:

    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.pwd = bot.config['identity'].get('pass')
        if self.pwd:
            self.hooks = [
                    {'type': 'on_connect', 'func': self.identify}
                    ]
        else:
            self.hooks = []

    def identify(self, data):
        self.conn.say('identify {}'.format(self.pwd), 'NickServ')

