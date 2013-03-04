from socket import socket, AF_INET, SOCK_STREAM

class IRCConn:
    
    """
    This class handles the connection with the IRC server.
    It connects and sends and receives messages.
    """
    
    def __init__(self, bot):
        self._bot = bot
        self._id = bot.ident
        self._port = 6667
    
    def connect(self):
        self._sock = socket(AF_INET, SOCK_STREAM)
        self._sock.connect((self._id.host, self._port))
        self._send('USER {} {} {} :{}'.format(self._id.ident, self._id.host, self._id.serv, self._id.name))
        self.nick(self._id.nick)
        # wait until we have received the MOTD in full before proceeding
    
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
        except (UnicodeError):
            self.handle_encoding_error()
            return ''
        print('received:', line)
        return line

    def mainloop(self):
        while True:
            line = self.receive()
            self._bot.parse(line)

    def handle_encoding_error(self):
        print('encoding error encountered.')
    
    def handle_error(self, tokens):
        print('error. tokens:', tokens)
        self.connect()
