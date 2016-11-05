import pexpect
from pexpect.exceptions import TIMEOUT

class Plugin:

    FLAGS = {'g', 'p' , 'I', 'i', 'M', 'm', 'number'}
    SED_TIMEOUT = 0.01

    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.hooks = [
                {'type': 'privmsg', 'func': self.sub},
                ]
    
    def sed(self, msg, data):
        sed = pexpect.spawn('sed', [msg], timeout=self.SED_TIMEOUT)
        sed.delaybeforesend = None

        print(self.bot.histories[data.to])
        for d in self.bot.histories[data.to]:
            line = ' '.join(d.trailing)
            if self.is_sed_cmd(line):
                continue
            print('trying line {}'.format(line))
            sed.sendline(line)
            print('line sent. expecting.')
            try:
                sed.expect('\r\n.+\r\n', timeout=1)
            except TIMEOUT:
                continue
            print('expected.')
            result = sed.after.strip().decode()
            print('result: {}'.format(result))
            if result != line:
                return data.from_nick, result
            
    
    def is_sed_cmd(self, string):
        """A very simple way of detecting if a string looks like a sed
        command for our purposes.  Note that this doesn't mean the string
        will be accepted as valid by the actual sed programme (eg, s/foo/bar
        is good enough for our purposes here; we add the trailing / later)."""

        return string.startswith('s/') and '/' in string[2:]

    def str_is_valid(self, string):
        """Test if string is of form `s/X/Y/f` where `f` is a valid flag."""

        in_digits = False
        flags = self.FLAGS.copy()
        for c in reversed(string):
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
        if self.is_sed_cmd(msg):
            if not self.str_is_valid(msg):
                msg += '/'
            print('str is sed, msg = {}'.format(msg))
            result = self.sed(msg, data)
            if result is not None:
                response = 'Correction, <{}> {}'.format(*result)
                self.conn.say(response, data.to)
