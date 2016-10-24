
class Plugin:

    FLAGS = {'g', 'p' , 'I', 'i', 'M', 'm', 'number'}

    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.hooks = [
                {'type': 'privmsg', 'func': self.sub},
                ]
    
    def sed(self, msg, chan):
        sed = pexpect.spawn('sed', [msg], timeout=1)
        sed.delaybeforesend = None
        #TODO: implement this in History
        for data in self.bot.histories[data.to]:
            line = ' '.join(data.trailing)
            sed.sendline(line)
            sed.expect('\r\n\w+\r\n')
            result = sed.after.strip().decode()
            if result != line:
                return data.from_nick, result
            
    
    def str_is_valid(self, string):
        in_digits = False
        flags = self.FLAGS.copy()
        for c in reversed(msg):
            if c.isdigit():
                if ('number' not in flags) and (not in_digits):
                    return False
                elif 'number' in flags:
                    in_digits = True
                    flags.remove('number')
            else:
                in_digits = False
                if c in flags:
                    flags.remove(c)
                else:
                    if c == '/':
                        return True
                    else:
                        return False
    
    def sub(self, data):
        msg = ' '.join(data.trailing).strip()
        if msg.startswith('s/') and '/' in msg[2:]:
            # good enough for us
            if not self.str_is_valid(msg):
                msg += '/'
        result = self.sub(msg, data.to)
        response = 'Correction, <{}> {}'.format(*result)
        self.conn.say(response, data.to)
