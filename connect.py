from socket import socket, AF_INET, SOCK_STREAM

class IRCConn:
    
    """
    This class handles the connection with the IRC server.
    It connects and sends and receives messages.
    """
    
    def __init__(self, bot):
        self._bot = bot
        i = bot.ident
        self._ident = i.ident
        self._serv = i.serv
        self._host = i.host
        self._name = i.name
        self._nick = i.nick
        self._join_first = i.joins
        self._port = 6667
    
    def connect(self):
        self._sock = socket(AF_INET, SOCK_STREAM)
        self._sock.connect((self._host, self._port))
        self._send('USER {} {} {} :{}'.format(self._ident, self._host, self._serv, self._name))
        self.nick(self._nick)
        # wait until we have received the MOTD in full before proceeding

    def on_connect(self):
        """
        Called once we have connected to and identified with the server.
        Mainly joins the channels that we want to join at the start.
        """
        for chan in self._join_first:
            self.join(chan)
    
    def join(self, chan):
        self._send('JOIN {}'.format(chan))

    def part(self, chan):
        self._send('PART {}'.format(chan))
    
    def topic(self, chan, new=None):
        self._send('TOPIC {} {}'.format(chan, new or ''))
    
    def _send(self, msg):
        """Send something (anything) to the IRC server."""
        print('sending: {}\r\n'.format(msg))
        self._sock.send('{}\r\n'.format(msg).encode())
    
    def say(self, msg, chan, to=None):
        """say(msg, chan): Say msg on chan."""
        prefix = '' if to is None else '{}: '.format(to)
        for line in msg.splitlines():
            self._send('{} {} :{}{}'.format('PRIVMSG', chan, prefix, line))

    def pong(self, trail):
        self._send('{} {}'.format('PONG', trail))

    def nick(self, new):
        self._send('NICK {}'.format(new))
        self._nick = new

    def receive(self):
        """
        Read from the socket until we reach the end of an IRC message.
        Attempt to decode the message and return it.
        Call handle_encoing_error() if unsuccessful.
        """
        buf = []
        while buf[-2:] != [b'\r', b'\n']:
            buf.append(self._sock.recv(1))

        try:
            line = b''.join(buf).decode()
        except (UnicodeDecodeError, UnicodeEncodeError):
            self.handle_encoding_error()
            return ''
        print('received:', line)
        return line
            
    def parse(self, line):
        if not line:
            # empty line; this should throw up an error.
            return
        line = line.strip('\r\n')
        tokens = line.split()
        if tokens[0].startswith(':'):
            prefix = tokens.pop(0)[1:].strip(':')
        else:
            prefix = ''
        
        cmd = tokens.pop(0)
        if cmd == '433':    # nick already in use
            self._nick += '_'
            self.nick(self._nick)
        if cmd == '376':    # end of MOTD
            self.on_connect()
        if cmd == 'PING':
            self.pong(' '.join(tokens))
        elif cmd == 'ERROR':
            self.handle_error(tokens)
        elif cmd == 'JOIN':
            if prefix.split('!')[0] != self.nick:
                self._bot.handle_other_join(tokens, prefix)
        elif cmd == 'PRIVMSG':
            self._bot.handle_privmsg(tokens, prefix)
        elif cmd == 'NICK':
            self._bot.handle_other_nick(tokens, prefix)

    def mainloop(self):
        while True:
            line = self.receive()
            self.parse(line)

    def handle_encoding_error(self):
        print('encoding error encountered.')
    
    def handle_error(self, tokens):
        print('error. tokens:', tokens)
        self.connect()
