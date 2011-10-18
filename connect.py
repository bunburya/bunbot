from socket import socket, AF_INET, SOCK_STREAM

class IRCConn:
    
    """
    This class handles the connection with the IRC server.
    It connects and sends and receives messages.
    """
    
    def __init__(self, bot):
        self.bot = bot
        i = bot.ident
        self.ident = i.ident
        self.serv = i.serv
        self.host = i.host
        self.name = i.name
        self.nick = i.nick
        self.join_first = i.joins
        self.port = 6667
    
    def connect(self):
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self._send('USER {} {} {} :{}'.format(self.ident, self.host, self.serv, self.name))
        self._send('NICK {}'.format(self.nick))
        # wait until we have received the MOTD in full before proceeding

    def on_connect(self):
        """
        Called once we have connected to and identified with the server.
        Mainly joins the channels that we want to join at the start.
        """
        for chan in self.join_first:
            self.join(chan)
    
    def join(self, chan):
        self._send('JOIN {}'.format(chan))
    
    def _send(self, msg):
        """Send something (anything) to the IRC server."""
        print('sending: {}\r\n'.format(msg))
        self.sock.send('{}\r\n'.format(msg).encode())
    
    def say(self, msg, chan, to=None):
        """say(msg, chan): Say msg on chan."""
        prefix = '' if to is None else '{}: '.format(sender)
        self._send('{} {} :{}{}'.format('PRIVMSG', chan, prefix, msg))

    def pong(self, trail):
        self._send('{} {}'.format('PONG', trail))
    
    def receive(self):
        """
        Read from the socket until we reach the end of an IRC message.
        Attempt to decode the message and return it.
        Call handle_encoing_error() if unsuccessful.
        """
        buf = []
        while True:
            nxt_ch = None
            ch = self.sock.recv(1)
            if ch == b'\r':
                nxt_ch = self.sock.recv(1)
                if nxt_ch == b'\n':
                    try:
                        line = b''.join(buf).decode()
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        self.handle_encoding_error()
                        return ''
                    print('received:', line)
                    return line
            buf.append(ch)
            if nxt_ch:
                buf.append(nxt_ch)
            
        if not line.strip():
            return None
        else:
            try:
                parsable = line.strip(b'\r\n').decode()
                print('received:', parsable)
                return parsable
            except (UnicodeEncodeError, UnicodeDecodeError):
                self.handle_encoding_error()
    
    def parse(self, line):
        if not line:
            # empty line; this should throw up an error.
            return
        line = line.strip('\r\n')
        tokens = line.split(' ')
        if tokens[0].startswith(':'):
            sender = tokens.pop(0)[1:]
        else:
            sender = ''
        
        cmd = tokens.pop(0)
        if cmd == '433':    # nick already in use
            self.nick += '_'
            self._send('NICK {}'.format(self.nick))
        if cmd == '376':    # end of MOTD
            self.on_connect()
        if cmd == 'PING':
            self.pong(' '.join(tokens))
        elif cmd == 'ERROR':
            self.handle_error(tokens)
        elif cmd == 'PRIVMSG':
            self.bot.handle_privmsg(tokens, sender)
    
    def mainloop(self):
        while True:
            line = self.receive()
            self.parse(line)

    def handle_encoding_error(self):
        print('encoding error encountered.')
    
    def handle_error(self, tokens):
        print('error. tokens:', tokens)
        self.connect()
